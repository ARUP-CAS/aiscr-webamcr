import contextlib
import gettext as gettext_module
import logging
import os
import shutil
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path

import polib
from django.conf import settings
from django.utils import translation as django_translation
from django.utils.translation import gettext, trans_real

logger = logging.getLogger(__name__)

# Stav kontroly runtime katalogů pro aktuální proces: otisk souborů `django.mo`, ze kterých
# proces naposledy načetl katalogy, otisk stavu souborů, jehož načtení naposledy selhalo
# (opakuje se po změně nebo po pětiminutové prodlevě), a monotónní časy kontrol. Každý proces
# (worker uWSGI, potomek Celery) má vlastní kopii; po forku se první kontrola v potomkovi
# postará o nové načtení (viz `reload_translation_catalogs_if_changed`).
_catalog_state = {"fingerprint": None, "failed_fingerprint": None, "last_check": None, "failed_at": None}
_catalog_lock = threading.Lock()
_UNKNOWN_FINGERPRINT = object()
_CATALOG_RETRY_COOLDOWN = 300


def format_message(message_id, **params) -> str:
    """
    Přeloží zprávu s pojmenovanými zástupnými znaky a dosadí do ní parametry.

    Překlad drží celou větu (``{child}``, ``{field}`` …), takže pořadí slov řídí překladatel,
    ne skládání fragmentů v kódu. Chybí-li překlad (``gettext`` vrátí ID doslova), parametry se
    připojí za ID ve tvaru ``klíč=hodnota``, aby se informace ze zprávy neztratila. Překlad
    s neznámým zástupným znakem se vrátí bez dosazení místo vyvolání výjimky.

    Volající označí ID pomocí ``gettext_noop``, aby ho ``makemessages`` extrahoval.

    :param message_id: Překladové ID zprávy.
    :param params: Hodnoty pro zástupné znaky v přeložené zprávě.
    :return: Přeložená zpráva s dosazenými hodnotami.
    """
    text = str(gettext(message_id))
    if text == message_id:
        return " ".join([message_id] + [f"{key}={value}" for key, value in params.items()])
    try:
        return text.format(**params)
    except (KeyError, IndexError, ValueError):
        return text


def _catalog_paths():
    """
    Vrátí cesty k runtime katalogům ``django.mo`` pro všechny jazyky z ``settings.LANGUAGES``.

    Prochází každou cestu z ``settings.LOCALE_PATHS`` a pro každý jazyk sestaví cestu
    ``<cesta>/<locale>/LC_MESSAGES/django.mo``; existenci souborů neověřuje.

    :return: Seznam absolutních nebo relativních cest tak, jak vyplývají z nastavení.
    """
    return [
        os.path.join(str(locale_path), trans_real.to_locale(language_code), "LC_MESSAGES", "django.mo")
        for locale_path in settings.LOCALE_PATHS
        for language_code, _name in settings.LANGUAGES
    ]


def _catalog_fingerprint():
    """
    Sestaví otisk runtime katalogů z metadat souborů.

    Pro každý katalog uloží ``(st_mtime_ns, st_size, st_ino)``; inode zachytí i atomické
    nahrazení souboru přejmenováním, u kterého by změna času nemusela být rozlišitelná.
    Chybějící nebo nedostupný soubor má v otisku hodnotu ``None``.

    :return: N-tice dvojic ``(cesta, metadata)`` v pořadí podle ``_catalog_paths``.
    """
    fingerprint = []
    for path in _catalog_paths():
        try:
            stat_result = os.stat(path)
        except OSError:
            fingerprint.append((path, None))
            continue
        fingerprint.append((path, (stat_result.st_mtime_ns, stat_result.st_size, stat_result.st_ino)))
    return tuple(fingerprint)


def _ordered_language_codes():
    """
    Vrátí kódy jazyků z ``settings.LANGUAGES`` s výchozím jazykem na prvním místě.

    Výchozí jazyk se sestavuje jako první, aby případné záložní katalogy dalších jazyků
    (Django je bere z výchozího jazyka) vznikly už z nově načteného katalogu.

    :return: Seznam kódů jazyků bez duplicit.
    """
    codes = [settings.LANGUAGE_CODE]
    for language_code, _name in settings.LANGUAGES:
        if language_code not in codes:
            codes.append(language_code)
    return codes


def _reload_translation_catalogs(fingerprint):
    """
    Znovu načte překladové katalogy procesu metodou „sestavit, pak vyměnit“.

    Před sestavením uloží obě mezipaměti, výchozí katalog a přesný stav aktivního jazyka.
    Sestaví každý jazyk (výchozí jako první) a znovu ověří metadata souborů. Změnila-li se,
    kandidáta odmítne. Jinak vynuluje výchozí katalog a obnoví aktivaci stejného jazyka nad
    novými objekty. Při chybě včetně dokončení aktivace obnoví celý původní stav a výjimku
    předá volajícímu, který ji zachytí a zapíše varování.

    :param fingerprint: Otisk očekávaných katalogů pořízený před sestavením.
    :return: ``True`` při úspěšném načtení.
    :raises Exception: Chyba sestavení nebo dokončení aktivace; původní stav se obnoví.
    """
    previous_gettext_cache = gettext_module._translations
    previous_django_cache = trans_real._translations
    previous_default = trans_real._default
    missing_active = object()
    active = getattr(trans_real._active, "value", missing_active)
    active_language = getattr(active, "to_language", lambda: None)()

    new_django_cache = {}
    try:
        gettext_module._translations = {}
        trans_real._translations = new_django_cache
        for language_code in _ordered_language_codes():
            trans_real.translation(language_code)
        if _catalog_fingerprint() != fingerprint:
            raise OSError("Translation catalog metadata changed while loading")
        trans_real._default = None
        if active_language is not None:
            django_translation.activate(active_language)
        logger.info("core.translation.reload_catalogs.reloaded", extra={"languages": list(new_django_cache)})
    except Exception:
        gettext_module._translations = previous_gettext_cache
        trans_real._translations = previous_django_cache
        trans_real._default = previous_default
        if active is missing_active:
            with contextlib.suppress(AttributeError):
                del trans_real._active.value
        else:
            trans_real._active.value = active
        raise
    return True


def reload_translation_catalogs_if_changed():
    """
    Ověří, zda se změnily runtime překladové katalogy, a případně je v procesu znovu načte.

    Kontrola proběhne nejvýše jednou za ``settings.TRANSLATION_CATALOG_CHECK_INTERVAL``
    sekund (``0`` = při každém volání, ``None`` = mechanismus vypnut). Porovná otisk souborů
    ``django.mo`` s otiskem uloženým při posledním úspěšném načtení. První kontrola zkusí
    načíst přítomné katalogy i bez změny, protože proces je mohl načíst před aktualizací
    (např. Celery spuštěné souběžně s nasazením). Metadata se porovnají před sestavením i po něm;
    zjištěná změna odmítne kandidáta a zachová původní překlady. Dvojice kontrol nezaručuje
    konzistentní snímek souborů: změna tam a zpět se shodnými metadaty může uniknout.

    Chybí-li některý očekávaný ``django.mo``, nebo se katalogy nepodaří načíst, proces
    ponechá dříve načtené katalogy, zapíše jedno varování a otisk si uloží jako neúspěšný.
    Změněný otisk dovolí další pokus při běžné kontrole; shodný neúspěšný stav se zkusí
    znovu nejdřív za 300 sekund od posledního pokusu. Další selhání stejného stavu se
    nelogují. Úspěch nebo návrat k již načtenému otisku neúspěšný stav vymaže. Stejná
    prodleva platí pro chybu před zjištěním otisku. Neočekávané výjimky neuniknou do
    požadavku ani úlohy a chyba po změně překladového stavu obnoví původní objekty.

    Obnova bez změny metadat může čekat na prodlevu i na další interval kontroly;
    nečinný proces čeká až na požadavek či úlohu. Nezměněný chybný katalog tak stojí
    nejvýše jeden pokus za pět minut v každém procesu. Novému procesu bez dříve
    načteného platného katalogu tento mechanismus nezaručí existenci starého překladu.

    :return: ``True``, pokud se katalogy znovu načetly, jinak ``False``.
    """
    with _catalog_lock:
        fingerprint = _UNKNOWN_FINGERPRINT
        now = None
        try:
            now = time.monotonic()
            failed_at = _catalog_state["failed_at"]
            cooling_down = failed_at is not None and now - failed_at < _CATALOG_RETRY_COOLDOWN
            if _catalog_state["failed_fingerprint"] is _UNKNOWN_FINGERPRINT and cooling_down:
                return False
            interval = getattr(settings, "TRANSLATION_CATALOG_CHECK_INTERVAL", 60)
            if interval is None:
                return False
            last_check = _catalog_state["last_check"]
            if last_check is not None and now - last_check < interval:
                return False
            _catalog_state["last_check"] = now
            fingerprint = _catalog_fingerprint()
            if fingerprint == _catalog_state["fingerprint"]:
                _catalog_state["failed_fingerprint"] = None
                _catalog_state["failed_at"] = None
                return False
            repeated_failure = fingerprint == _catalog_state["failed_fingerprint"]
            if repeated_failure and cooling_down:
                return False
            missing_paths = [path for path, metadata in fingerprint if metadata is None]
            if missing_paths:
                _catalog_state["failed_fingerprint"] = fingerprint
                _catalog_state["failed_at"] = now
                if not repeated_failure:
                    logger.warning("core.translation.reload_catalogs.missing", extra={"paths": missing_paths})
                return False
            _reload_translation_catalogs(fingerprint)
            _catalog_state["fingerprint"] = fingerprint
            _catalog_state["failed_fingerprint"] = None
            _catalog_state["failed_at"] = None
            return True
        except Exception as error:
            repeated_failure = fingerprint == _catalog_state["failed_fingerprint"]
            _catalog_state["failed_fingerprint"] = fingerprint
            _catalog_state["failed_at"] = now
            if not repeated_failure:
                with contextlib.suppress(Exception):
                    logger.warning("core.translation.reload_catalogs.failed", extra={"error": repr(error)})
            return False


def reload_translation_catalogs_on_task_prerun(sender=None, **kwargs):
    """
    Přijímač signálu Celery ``task_prerun``: před spuštěním úlohy ověří runtime katalogy.

    Díky tomu úlohy (např. notifikační e-maily) překládají podle aktuálních katalogů
    i ve workeru, který katalogy načetl před nasazením nebo před úpravou na serveru.
    Pomocná funkce zachytí chyby kontroly i aktivace a zachová původní překlady.
    Celery navíc zachytává výjimky přijímačů signálů; samotná výjimka přijímače
    proto automaticky neoznačuje úlohu jako neúspěšnou.

    :param sender: Úloha, která se spouští (signál ji předává, kontrola ji nepoužívá).
    :param kwargs: Další argumenty signálu ``task_prerun`` (``task_id``, ``task``, ``args`` …).
    """
    reload_translation_catalogs_if_changed()


def _prepare_temporary_file(target_path, write_content, mode_source=None):
    """
    Připraví obsah pro pozdější atomickou náhradu souboru ``target_path``.

    Funkce ``write_content`` zapíše obsah do dočasného souboru ve stejném adresáři jako cíl
    (jen tak je následné přejmenování atomické). Dočasný soubor převezme práva souboru
    ``mode_source`` (výchozí je cílový soubor); když neexistuje, dostane ``0o644``. Při chybě
    se dočasný soubor smaže a výjimka se předá dál.

    :param target_path: Cesta k souboru, který se má později nahradit.
    :param write_content: Funkce, která dostane cestu dočasného souboru a zapíše do něj obsah.
    :param mode_source: Soubor, jehož práva dočasný soubor převezme; ``None`` = cílový soubor.
    :return: Cesta k připravenému dočasnému souboru.
    """
    directory = os.path.dirname(os.path.abspath(target_path))
    file_descriptor, temp_path = tempfile.mkstemp(
        dir=directory, prefix=f".{os.path.basename(target_path)}.", suffix=".tmp"
    )
    os.close(file_descriptor)
    try:
        write_content(temp_path)
        mode_source = mode_source or target_path
        if os.path.exists(mode_source):
            shutil.copymode(mode_source, temp_path)
        else:
            os.chmod(temp_path, 0o644)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(temp_path)
        raise
    return temp_path


def import_translation_catalog(po_file_path, uploaded_file):
    """
    Nahradí runtime katalog nahraným souborem a zkompiluje k němu ``.mo``.

    Import probíhá ve dvou fázích. Při přípravě se v adresáři katalogu vytvoří tři dočasné
    soubory: nahraný soubor (zapsaný jen jednou a z tohoto souboru načtený knihovnou
    ``polib``), ``.mo`` zkompilovaný z něj a kopie stávajícího ``.po`` pro zálohu. Selže-li
    cokoli z toho (včetně souboru, který ``polib`` nedokáže načíst), dočasné soubory se smažou
    a katalog ani seznam záloh se nezmění. Teprve když je vše připravené, přejmenují se
    dočasné soubory bezprostředně po sobě na zálohu ``<název>_backup_<ddmmYYYYHHMMSS>.po``
    (název rozpozná seznam záloh), na ``.po`` a na sousední ``.mo``. Běžící procesy tak nikdy
    nenačtou rozepsaný katalog a změnu převezmou při další kontrole katalogů.

    Každé přejmenování je atomické samostatně; nejde o transakci nad dvojicí katalogů.
    Selže-li náhrada ``.po``, publikovaná záloha zůstane. Selže-li následná náhrada ``.mo``,
    zůstane nové ``.po``, původní ``.mo`` a záloha původního ``.po``. Při zachycené chybě
    se zbývající dočasné soubory smažou. Obnova po ukončení procesu není zaručena.

    :param po_file_path: Cesta k nahrazovanému souboru ``.po``.
    :param uploaded_file: Nahraný soubor (``UploadedFile``), jehož obsah se zapíše do ``.po``.
    :return: Cesta k vytvořené záloze ``.po``.
    :raises Exception: Chyba načtení nahraného souboru, kompilace ``.mo`` nebo zápisu na disk;
        katalog zůstane beze změny, pokud chyba nastala před přejmenováním.
    """
    path = Path(po_file_path)
    mo_path = path.with_suffix(".mo")
    backup_path = path.with_name(f"{path.stem}_backup_{datetime.now().strftime('%d%m%Y%H%M%S')}{path.suffix}")

    def write_uploaded_po(temp_path):
        """
        Zapíše obsah nahraného souboru do dočasného souboru.

        :param temp_path: Cesta k dočasnému souboru.
        """
        with open(temp_path, "wb") as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

    def copy_current_po(temp_path):
        """
        Zkopíruje stávající ``.po`` (včetně metadat) do dočasného souboru zálohy.

        :param temp_path: Cesta k dočasnému souboru.
        """
        shutil.copy2(path, temp_path)

    prepared = []
    try:
        po_temp = _prepare_temporary_file(str(path), write_uploaded_po)
        prepared.append(po_temp)
        po_file = polib.pofile(po_temp)
        mo_temp = _prepare_temporary_file(str(mo_path), po_file.save_as_mofile)
        prepared.append(mo_temp)
        backup_temp = _prepare_temporary_file(str(backup_path), copy_current_po, mode_source=str(path))
        prepared.append(backup_temp)
        for temp_path, target in ((backup_temp, backup_path), (po_temp, path), (mo_temp, mo_path)):
            os.replace(temp_path, target)
            prepared.remove(temp_path)
    finally:
        for temp_path in prepared:
            with contextlib.suppress(OSError):
                os.unlink(temp_path)
    return str(backup_path)


def connect_translation_catalog_signals():
    """
    Připojí kontrolu runtime katalogů na signál Celery ``task_prerun``.

    Volá se z ``CoreConfig.ready()``; díky ``dispatch_uid`` je opakované volání bez účinku.
    """
    from celery.signals import task_prerun

    task_prerun.connect(
        reload_translation_catalogs_on_task_prerun,
        weak=False,
        dispatch_uid="core.translation.reload_translation_catalogs_on_task_prerun",
    )
