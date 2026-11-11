"""
Django management příkaz ``aktualizuj_ruian_shp``.

Spouští plnou synchronizaci heslářů RÚIAN ze **dvojice** lokálních souborů:

* **SHP** ``1.zip`` (státní polygony krajů/okresů/KÚ, ~241 MB) –
  https://services.cuzk.gov.cz/shp/stat/epsg-5514/1.zip
* **VFR** ``YYYYMMDD_ST_UZSZ.xml.zip`` (autoritativní definiční body, ~4.5 MB) –
  https://services.cuzk.gov.cz/vfr/<RRRRMM>/<RRRRMMDD>_ST_UZSZ.xml.zip nebo
  https://vdp.cuzk.gov.cz/vdp/ruian/vymennyformat?crKopie=on&casovyRozsah=U&upStatAzZsj=on&uzemniPrvky=ST&dsZakladni=on&datovaSada=Z&vyZakladni=on&vyber=vyZakladni&kodOrp=&search=

Operátor stáhne oba soubory (typicky ručně přes ``wget``) do
``/vol/data-migrace/`` a předá cesty argumenty ``--shp`` a ``--uzsz``.

Syncer (:func:`heslar.ruian_sync.syncer.sync_full`) je sdílený.
Pro běžný plný sync je preferován tento command (jen 2 soubory ~245 MB
namísto tisíců souborů v alternativních zdrojích).

Pro denní inkrementální změny používej :func:`cron.tasks.sync_ruian_changes`
s VFR variantou ``ZKSH`` – beze změny, není dotčeno.

Příklady použití::

    # --valid-to se u 1.zip od ČÚZK odvodí z časů souborů v archivu
    # (den před vygenerováním)
    python manage.py aktualizuj_ruian_shp \\
        --shp /vol/data-migrace/1.zip \\
        --uzsz /vol/data-migrace/20260228_ST_UZSZ.xml.zip

    # Vstup může být i rozbalený adresář s SHP layery; --valid-to je pak povinné
    python manage.py aktualizuj_ruian_shp \\
        --shp /home/admin/ARUP/Katastry/ \\
        --uzsz /vol/data-migrace/20260228_ST_UZSZ.xml.zip \\
        --valid-to 2026-02-28
"""

import logging
import traceback
import zipfile
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.translation import gettext as _
from heslar.models import RuianSyncRun
from heslar.ruian_sync import ShpUzszSource
from heslar.ruian_sync import syncer as ruian_syncer
from heslar.ruian_sync.souhrn_varovani import SberVarovani
from heslar.ruian_sync.zamek import ruian_sync_lock

logger = logging.getLogger(__name__)


#: Po kolika dnech odstupu ÚZSZ od ``--valid-to`` se upozorní. ÚZSZ vychází
#: řidčeji než se aktualizuje SHP, takže odstup je normální; teprve delší
#: prodleva znamená, že katastrům vzniklým mezitím budou chybět definiční body
#: a dopočítají se z centroidu hranice (viz ``ShpUzszSource._load_katastry``).
_MAX_ODSTUP_UZSZ_DNU = 60


class Command(BaseCommand):
    """
    Django management příkaz pro plný sync heslářů RÚIAN ze SHP + UZSZ.

    Příkaz otevře předané SHP a UZSZ soubory přes :class:`ShpUzszSource`,
    založí ``RuianSyncRun(mode=full, source="shp_uzsz")`` ve stavu
    ``running`` a deleguje aplikaci dat na sdílený
    :func:`heslar.ruian_sync.syncer.sync_full`. Při úspěchu nastaví
    ``status="success"``, při výjimce uloží traceback do ``error``
    a vrátí exit code 1.

    Cesta k UZSZ se uloží do ``RuianSyncRun.note`` (pole ``source_path``
    nese SHP cestu, protože je primárním nositelem polygonů).
    """

    help = _("heslar.management.commands.aktualizuj_ruian_shp.Command.help")

    def add_arguments(self, parser):
        """
        Registruje argumenty příkazu.

        :param parser: Argumentový parser pro přidání parametrů.
        """
        parser.add_argument(
            "--shp",
            type=str,
            required=True,
            help=_("heslar.management.commands.aktualizuj_ruian_shp.Command.add_arguments.shp_help"),
        )
        parser.add_argument(
            "--uzsz",
            type=str,
            required=True,
            help=_("heslar.management.commands.aktualizuj_ruian_shp.Command.add_arguments.uzsz_help"),
        )
        parser.add_argument(
            "--valid-to",
            type=str,
            required=False,
            help=_("heslar.management.commands.aktualizuj_ruian_shp.Command.add_arguments.valid_to_help"),
        )

    def handle(self, *args, **options):
        """
        Vykoná plnou synchronizaci heslářů RÚIAN ze SHP + UZSZ.

        :param args: Standardní pozicovaný argument managementu.
        :param options: Slovník s argumenty (``shp``, ``uzsz``, ``valid_to``).

        :raises CommandError: Pokud některá vstupní cesta neexistuje,
            ``--valid-to`` má neplatný formát, nebo chybí u vstupu, ze kterého
            ho nejde odvodit.
        """
        shp_path = Path(options["shp"])
        uzsz_path = Path(options["uzsz"])
        if not shp_path.exists():
            raise CommandError(f"SHP cesta neexistuje: {shp_path}")
        if not uzsz_path.exists():
            raise CommandError(f"UZSZ cesta neexistuje: {uzsz_path}")

        valid_to = self._urci_valid_to(shp_path, options.get("valid_to"))

        logger.debug(
            "heslar.management.commands.aktualizuj_ruian_shp.handle.start",
            extra={
                "file": str(shp_path),
                "uzsz": str(uzsz_path),
                "valid_to": valid_to.isoformat(),
            },
        )

        source = ShpUzszSource(shp_path=shp_path, uzsz_path=uzsz_path)

        self._zkontroluj_valid_to(shp_path, uzsz_path, valid_to)

        # Tentýž advisory lock jako plánovaný denní sync, a bere se dřív, než
        # vznikne audit záznam – odmítnutý pokus nemá co zakládat běh. Bez
        # zámku by cron spuštěný během hodiny trvajícího plného synchu zapsal
        # svou deltu, měl novější ``started_at``, stal se ``last_successful()``
        # – a plný sync by pak přes něj uložil svůj starší snapshot. Změny
        # toho dne by zmizely, aniž by to cokoli ohlásilo.
        with ruian_sync_lock() as ziskan_zamek:
            if not ziskan_zamek:
                raise CommandError(
                    "Synchronizace RÚIAN už běží (drží advisory lock). Počkejte na její "
                    "dokončení, nebo zastavte běžící úlohu. Souběh plného synchu a denní "
                    "delty by nenávratně zahodil změny zpracované mezitím."
                )
            self._proved_sync(source, shp_path, uzsz_path, valid_to)

    @staticmethod
    def _datum_snapshotu(uzsz_path):
        """
        Vyčte datum snapshotu z názvu souboru ``YYYYMMDD_ST_UZSZ.xml.zip``.

        :param uzsz_path: Cesta k souboru ÚZSZ.
        :return: :class:`datetime.date` z názvu, nebo ``None`` když název
            očekávaný tvar nemá (např. ručně přejmenovaný soubor).
        """
        zaklad = uzsz_path.name.split("_", 1)[0]
        if len(zaklad) != 8 or not zaklad.isdigit():
            return None
        try:
            return datetime.strptime(zaklad, "%Y%m%d").date()
        except ValueError:
            return None

    @staticmethod
    def _datum_vygenerovani_shp(shp_path) -> Optional[date]:
        """
        Zjistí den, kdy ČÚZK vygeneroval SHP archiv, z časů souborů v ZIP.

        ``1.zip`` má stálou URL a nedatovaný název, ale soubory vrstev uvnitř
        nesou čas vygenerování (např. ``1/OKRESY_P.shp`` 2026-11-10 20:27).
        Bere se **nejstarší** čas souboru vrstvy ``.shp``, tedy začátek
        generování – nejopatrnější odhad stavu dat.

        U rozbaleného adresáře se datum nezjišťuje: časy souborů tam určuje
        rozbalení, ne ČÚZK. Totéž platí pro archiv, který někdo přebalil –
        nese časy přebalení a kontrola je pak volnější, než by měla být.
        Časy v ZIP jsou místní bez časové zóny; ČÚZK generuje archiv večer
        (kolem 20:30), takže posun o pár hodin den nezmění.

        :param shp_path: Cesta k ``1.zip`` nebo k adresáři s vrstvami.
        :return: Den vygenerování, nebo ``None``, když ho nejde zjistit
            (adresář, poškozený archiv, archiv bez vrstev ``.shp``).
        """
        if not zipfile.is_zipfile(str(shp_path)):
            return None
        try:
            with zipfile.ZipFile(str(shp_path)) as zf:
                casy = [i.date_time for i in zf.infolist() if i.filename.lower().endswith(".shp")]
        except (OSError, zipfile.BadZipFile):
            return None
        if not casy:
            return None
        rok, mesic, den = min(casy)[:3]
        try:
            return date(rok, mesic, den)
        except ValueError:
            return None

    def _urci_valid_to(self, shp_path, zadane: Optional[str]) -> date:
        """
        Určí kotvu ``valid_to`` – ze zadané hodnoty, nebo z data vygenerování SHP.

        Bez ``--valid-to`` se u ``1.zip`` od ČÚZK použije **den před
        vygenerováním** archivu (viz :meth:`_datum_vygenerovani_shp`): archiv
        obsahuje změny do předchozího dne, změnový soubor téhož dne ještě ne.
        Ručně zadaná hodnota má přednost a dál ji ověří
        :meth:`_zkontroluj_valid_to`.

        :param shp_path: Cesta k ``1.zip`` nebo k adresáři s vrstvami.
        :param zadane: Hodnota ``--valid-to`` (``YYYY-MM-DD``), nebo ``None``.
        :return: Datum kotvy.
        :raises CommandError: Když má zadaná hodnota neplatný formát, nebo
            když chybí a datum vygenerování SHP nejde zjistit (adresář,
            archiv bez vrstev ``.shp``).
        """
        if zadane is not None:
            # Prázdný řetězec (např. nenastavená proměnná shellu) je chyba
            # formátu, ne pokyn kotvu odvodit.
            try:
                return datetime.strptime(zadane, "%Y-%m-%d").date()
            except ValueError as exc:
                raise CommandError(f"Neplatný formát --valid-to (očekáván YYYY-MM-DD): {exc}")

        datum_shp = self._datum_vygenerovani_shp(shp_path)
        if datum_shp is None:
            raise CommandError(
                f"U {shp_path} nejde zjistit datum vygenerování SHP (není to ZIP od ČÚZK), "
                f"zadejte proto --valid-to: poslední den, jehož změny SHP jistě obsahuje."
            )
        valid_to = datum_shp - timedelta(days=1)
        self.stdout.write(
            self.style.NOTICE(
                f"  --valid-to nezadáno: archiv vygeneroval ČÚZK {datum_shp.isoformat()} (podle časů "
                f"souborů v ZIP), kotva bude {valid_to.isoformat()}."
            )
        )
        return valid_to

    def _zkontroluj_valid_to(self, shp_path, uzsz_path, valid_to):
        """
        Ověří, že ``--valid-to`` nepopisuje pozdější stav, než jaký vstupy obsahují.

        Kotva odvozená v :meth:`_urci_valid_to` kontrolou proti datu SHP
        projde vždy; ostatní kontroly (ÚZSZ) platí pro ni stejně.

        ``valid_to`` se ukládá jako kotva ``RuianSyncRun.data_valid_to`` a cron
        od ní pokračuje následujícím dnem. Když popisuje pozdější stav, než
        jaký se opravdu nahrál, dny mezi skutečnými daty a kotvou se nikdy
        nestáhnou – a protože kotva vypadá čerstvě, nespustí se ani hlídač
        stáří dat. Taková ztráta je tichá: na testu (plný sync se SHP
        vygenerovaným 12. 10. 2026 a ``valid_to`` 12. 10.) vynechal denní sync
        změnový soubor z 12. 10., který SHP ještě neobsahoval, a sousední
        katastry se pak překrývaly.

        Kontroluje se:

        * ``valid_to`` v budoucnosti je vždy špatně – takový stav nemohl být
          stažen a kotva by přeskočila všechny dny až k němu;
        * ``valid_to`` **nejvýš den před vygenerováním SHP** (viz
          :meth:`_datum_vygenerovani_shp`). ČÚZK generuje archiv večer,
          ale změnový soubor téhož dne v něm ještě není; dřívější
          kotva je přitom neškodná – denní sync jen znovu aplikuje den, který
          už v datech je. U adresáře, kde datum nejde zjistit, jen upozorní;
        * ÚZSZ **novější** než ``valid_to`` je podezřelé, protože definiční
          body by pocházely z pozdějšího stavu, než jaký se deklaruje;
        * velký odstup ÚZSZ od ``valid_to`` je jen upozornění, že definiční
          body nově vzniklých katastrů mohou chybět. ÚZSZ vychází řidčeji než
          SHP, starší ÚZSZ je proto běžný stav.

        :param shp_path: Cesta k ``1.zip`` nebo k adresáři s vrstvami.
        :param uzsz_path: Cesta k souboru ÚZSZ.
        :param valid_to: Datum zadané přes ``--valid-to``.
        :raises CommandError: Když ``--valid-to`` leží v budoucnosti nebo je
            pozdější než den před vygenerováním SHP.
        """
        dnes = datetime.now().date()
        if valid_to > dnes:
            raise CommandError(
                f"--valid-to {valid_to.isoformat()} leží v budoucnosti (dnes je {dnes.isoformat()}). "
                f"Kotva by přeskočila denní změny za {(valid_to - dnes).days} dnů a nikdo by se to nedozvěděl."
            )

        datum_shp = self._datum_vygenerovani_shp(shp_path)
        if datum_shp is None:
            self.stdout.write(
                self.style.WARNING(
                    f"  U {shp_path} nejde zjistit datum vygenerování SHP (není to ZIP od ČÚZK). "
                    f"Ověřte, že --valid-to není pozdější než den před vygenerováním dat."
                )
            )
        else:
            nejpozdeji = datum_shp - timedelta(days=1)
            if valid_to > nejpozdeji:
                raise CommandError(
                    f"--valid-to {valid_to.isoformat()} je pozdější než stav SHP: archiv vygeneroval ČÚZK "
                    f"{datum_shp.isoformat()} (podle časů souborů v ZIP), --valid-to smí být nejvýš "
                    f"{nejpozdeji.isoformat()}. Pozdější kotva by denní sync přeskočil o změny "
                    f"{(nejpozdeji + timedelta(days=1)).isoformat()} až {valid_to.isoformat()}. Zadejte "
                    f"--valid-to {nejpozdeji.isoformat()} nebo dřívější; dřívější datum je bezpečné, denní sync "
                    f"dny navíc jen znovu aplikuje."
                )

        datum_uzsz = self._datum_snapshotu(uzsz_path)
        if datum_uzsz is None:
            self.stdout.write(self.style.WARNING(f"  Z názvu {uzsz_path.name} nejde vyčíst datum vydání ÚZSZ."))
            return

        if datum_uzsz > valid_to:
            self.stdout.write(
                self.style.WARNING(
                    f"  ÚZSZ je vydané {datum_uzsz.isoformat()}, tedy později než --valid-to "
                    f"{valid_to.isoformat()}; definiční body pocházejí z novějšího stavu, "
                    f"než jaký se ukládá jako kotva."
                )
            )
            return

        odstup = (valid_to - datum_uzsz).days
        if odstup > _MAX_ODSTUP_UZSZ_DNU:
            self.stdout.write(
                self.style.WARNING(
                    f"  ÚZSZ je {odstup} dnů staré ({datum_uzsz.isoformat()}) proti --valid-to "
                    f"{valid_to.isoformat()}; katastrům vzniklým mezitím mohou chybět definiční "
                    f"body a dopočítají se z centroidu hranice."
                )
            )

    def _proved_sync(self, source, shp_path, uzsz_path, valid_to):
        """
        Založí audit záznam a provede plný sync pod drženým zámkem.

        :param source: Zdroj dat :class:`~heslar.ruian_sync.ShpUzszSource`.
        :param shp_path: Cesta ke státnímu SHP archivu.
        :param uzsz_path: Cesta k souboru ÚZSZ s definičními body.
        :param valid_to: Datum, ke kterému jsou data platná.
        :raises CommandError: Když synchronizace selže.
        """
        initial_note_parts = [f"uzsz={uzsz_path.name}"]

        run = RuianSyncRun.objects.create(
            mode=RuianSyncRun.MODE_FULL,
            source=source.source_id,
            triggered_by=RuianSyncRun.TRIGGER_MANAGE,
            source_path=str(shp_path),
            data_valid_to=valid_to,
            variant="SHP_UZSZ",
            note=", ".join(initial_note_parts),
        )
        self.stdout.write(self.style.NOTICE(f"Vytvořen RuianSyncRun #{run.pk} (running)..."))
        self.stdout.write(f"  SHP:  {shp_path}")
        self.stdout.write(f"  UZSZ: {uzsz_path}")
        self.stdout.write(f"  valid_to: {valid_to.isoformat()}")

        # Varování z parseru a přepočtu se shrnou do ``run.warnings`` – viz
        # :class:`~heslar.ruian_sync.souhrn_varovani.SberVarovani`.
        sber_varovani = SberVarovani(run).start()
        try:
            ruian_syncer.sync_full(source=source, run=run)
        except Exception as exc:  # noqa: BLE001 — záměrně chytáme vše a logujeme
            run.error = traceback.format_exc()
            run.status = RuianSyncRun.STATUS_FAILED
            run.finished_at = timezone.now()
            run.save(update_fields=["error", "status", "finished_at"])
            logger.error(
                "heslar.management.commands.aktualizuj_ruian_shp.handle.error",
                extra={"run_id": run.pk, "error": str(exc)},
            )
            raise CommandError(f"Synchronizace selhala – RuianSyncRun #{run.pk}: {exc}")
        finally:
            sber_varovani.zapis()

        run.refresh_from_db()
        run.status = RuianSyncRun.STATUS_SUCCESS
        run.finished_at = timezone.now()
        run.save(update_fields=["status", "finished_at"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Synchronizace dokončena. RuianSyncRun #{run.pk}: "
                f"kraj +{run.kraj_upserts}/-{run.kraj_deletes}, "
                f"okres +{run.okres_upserts}/-{run.okres_deletes}, "
                f"katastr +{run.katastr_upserts}/-{run.katastr_deletes}, "
                f"přepočítáno: AZ {run.affected_az}, projekt {run.affected_projekt}, SN {run.affected_sn}."
            )
        )
