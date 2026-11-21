import gettext as gettext_module
import os
import re
import shutil
import tempfile
from unittest.mock import MagicMock, PropertyMock, patch

import polib
from core import translation as catalog_reload
from core.translation import (
    connect_translation_catalog_signals,
    import_translation_catalog,
    reload_translation_catalogs_if_changed,
    replace_file_atomically,
)
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404, HttpResponse
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.utils import translation
from django.utils.translation import trans_real

TEST_KEY = "core.tests.translationReload.key"
FOOTER_AUTOMATIC = "templates.emailFooter.automatic"
FOOTER_SENT_FROM = "templates.emailFooter.sentFrom"


class RuntimeCatalogTestMixin:
    """
    Společná příprava testů: dočasné runtime katalogy v ``LOCALE_PATHS`` a čistý stav kontroly.

    Každý test dostane vlastní adresář s katalogy ``cs`` a ``en``, nastavení
    ``TRANSLATION_CATALOG_CHECK_INTERVAL = 0`` a vynulovaný stav kontroly v modulu
    ``core.translation``; po testu se stav i aktivní jazyk vrátí do výchozího stavu.
    """

    check_interval = 0

    def setUp(self):
        """Vytvoří dočasný adresář katalogů a přepíše nastavení překladů pro test."""
        super().setUp()
        self.locale_dir = tempfile.mkdtemp(prefix="amcr-locale-")
        self.addCleanup(shutil.rmtree, self.locale_dir, ignore_errors=True)
        settings_override = override_settings(
            LOCALE_PATHS=[self.locale_dir],
            LANGUAGE_CODE="cs",
            LANGUAGES=[("cs", "Czech"), ("en", "English")],
            TRANSLATION_CATALOG_CHECK_INTERVAL=self.check_interval,
        )
        settings_override.enable()
        self.addCleanup(settings_override.disable)
        self._reset_check_state()
        self.addCleanup(self._reset_check_state)
        self.addCleanup(translation.deactivate)

    @staticmethod
    def _reset_check_state():
        """Vynuluje uložené otisky a čas poslední kontroly v ``core.translation``."""
        catalog_reload._catalog_state["fingerprint"] = None
        catalog_reload._catalog_state["failed_fingerprint"] = None
        catalog_reload._catalog_state["last_check"] = None

    def mo_path(self, language_code):
        """
        Vrátí cestu k testovacímu katalogu ``django.mo`` daného jazyka.

        :param language_code: Kód jazyka (``cs``, ``en``).
        :return: Cesta k souboru v dočasném adresáři.
        """
        return os.path.join(self.locale_dir, language_code, "LC_MESSAGES", "django.mo")

    def build_mo(self, entries, path):
        """
        Zkompiluje katalog s danými hesly do souboru ``path``.

        :param entries: Slovník ``msgid -> msgstr``.
        :param path: Cílová cesta souboru ``.mo``.
        """
        po = polib.POFile()
        po.metadata = {"Content-Type": "text/plain; charset=UTF-8", "Language": "cs"}
        for msgid, msgstr in entries.items():
            po.append(polib.POEntry(msgid=msgid, msgstr=msgstr))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        po.save_as_mofile(path)

    def write_catalog(self, language_code, entries):
        """
        Přepíše runtime katalog jazyka na místě a posune čas změny souboru.

        Posun času zajišťuje odlišný otisk i na souborových systémech s hrubým rozlišením času.

        :param language_code: Kód jazyka.
        :param entries: Slovník ``msgid -> msgstr``.
        """
        path = self.mo_path(language_code)
        previous_mtime = os.stat(path).st_mtime_ns if os.path.exists(path) else 0
        self.build_mo(entries, path)
        bumped = max(os.stat(path).st_mtime_ns, previous_mtime + 1_000_000_000)
        os.utime(path, ns=(bumped, bumped))

    def write_catalogs(self, cs_entries, en_entries):
        """
        Přepíše runtime katalogy obou jazyků.

        :param cs_entries: Hesla českého katalogu.
        :param en_entries: Hesla anglického katalogu.
        """
        self.write_catalog("cs", cs_entries)
        self.write_catalog("en", en_entries)

    @staticmethod
    def translated(language_code, message_id=TEST_KEY):
        """
        Přeloží ``message_id`` v daném jazyce.

        :param language_code: Kód jazyka.
        :param message_id: Překladové ID.
        :return: Přeložený text.
        """
        with translation.override(language_code):
            return translation.gettext(message_id)


class CatalogChangeDetectionTest(RuntimeCatalogTestMixin, SimpleTestCase):
    """Testy detekce změn runtime katalogů a omezení četnosti kontrol."""

    def setUp(self):
        """Připraví výchozí katalogy obou jazyků."""
        super().setUp()
        self.write_catalogs({TEST_KEY: "Původní"}, {TEST_KEY: "Original"})

    def test_first_check_in_process_reloads(self):
        """První kontrola v procesu načítá vždy, i když proces katalogy už načetl dříve."""
        self.assertEqual(self.translated("cs"), "Původní")
        self.assertTrue(reload_translation_catalogs_if_changed())

    def test_unchanged_catalogs_are_not_reloaded(self):
        """Beze změny souborů se katalogy znovu nenačítají."""
        self.assertTrue(reload_translation_catalogs_if_changed())
        with patch.object(catalog_reload, "_reload_translation_catalogs") as reload_mock:
            self.assertFalse(reload_translation_catalogs_if_changed())
            self.assertFalse(reload_translation_catalogs_if_changed())
        reload_mock.assert_not_called()

    @override_settings(TRANSLATION_CATALOG_CHECK_INTERVAL=60)
    def test_checks_are_throttled(self):
        """Uvnitř intervalu se soubory nekontrolují; po jeho uplynutí se změna převezme."""
        with patch.object(catalog_reload.time, "monotonic", side_effect=[100.0, 110.0, 200.0]):
            self.assertTrue(reload_translation_catalogs_if_changed())
            self.write_catalogs({TEST_KEY: "Nový text"}, {TEST_KEY: "New text"})
            with patch.object(catalog_reload, "_catalog_fingerprint") as fingerprint_mock:
                self.assertFalse(reload_translation_catalogs_if_changed())
            fingerprint_mock.assert_not_called()
            self.assertTrue(reload_translation_catalogs_if_changed())
        self.assertEqual(self.translated("cs"), "Nový text")

    @override_settings(TRANSLATION_CATALOG_CHECK_INTERVAL=None)
    def test_disabled_check_never_reloads(self):
        """Hodnota ``None`` mechanismus vypne a katalogy zůstanou načtené jen jednou."""
        self.assertEqual(self.translated("cs"), "Původní")
        self.write_catalogs({TEST_KEY: "Nový text"}, {TEST_KEY: "New text"})
        with patch.object(catalog_reload, "_reload_translation_catalogs") as reload_mock:
            self.assertFalse(reload_translation_catalogs_if_changed())
        reload_mock.assert_not_called()
        self.assertEqual(self.translated("cs"), "Původní")


class CatalogReloadTest(RuntimeCatalogTestMixin, SimpleTestCase):
    """Testy načtení změněných katalogů, odolnosti vůči poškozeným souborům a zachování jazyka."""

    def setUp(self):
        """Připraví výchozí katalogy a proběhne první kontrola, jako by proces už běžel."""
        super().setUp()
        self.write_catalogs({TEST_KEY: "Původní"}, {TEST_KEY: "Original"})
        reload_translation_catalogs_if_changed()
        self.assertEqual(self.translated("cs"), "Původní")

    def test_changed_msgstr_is_adopted_without_restart(self):
        """Úprava hesla na serveru se po kontrole projeví bez restartu procesu."""
        self.write_catalog("cs", {TEST_KEY: "Opravený překlad"})
        self.assertTrue(reload_translation_catalogs_if_changed())
        self.assertEqual(self.translated("cs"), "Opravený překlad")
        self.assertEqual(self.translated("en"), "Original")

    def test_atomically_replaced_catalog_is_adopted(self):
        """Katalog nahrazený přejmenováním (nasazení, import) se převezme."""
        replacement = self.mo_path("cs") + ".tmp"
        self.build_mo({TEST_KEY: "Nasazený překlad"}, replacement)
        os.replace(replacement, self.mo_path("cs"))
        self.assertTrue(reload_translation_catalogs_if_changed())
        self.assertEqual(self.translated("cs"), "Nasazený překlad")

    def test_truncated_catalog_keeps_previous_catalogs(self):
        """Rozepsaný (zkrácený) katalog nerozbije překlad; platný katalog se převezme později."""
        complete = self.mo_path("cs") + ".complete"
        self.build_mo({TEST_KEY: "Nový text po opravě"}, complete)
        with open(complete, "rb") as source:
            truncated_content = source.read()[:40]
        with open(self.mo_path("cs"), "wb") as target:
            target.write(truncated_content)

        with self.assertLogs("core.translation", level="WARNING") as captured:
            self.assertFalse(reload_translation_catalogs_if_changed())
        self.assertIn("core.translation.reload_catalogs.failed", captured.output[0])
        self.assertEqual(self.translated("cs"), "Původní")
        self.assertEqual(self.translated("en"), "Original")

        os.replace(complete, self.mo_path("cs"))
        self.assertTrue(reload_translation_catalogs_if_changed())
        self.assertEqual(self.translated("cs"), "Nový text po opravě")

    def test_missing_catalog_keeps_previous_catalogs(self):
        """Chybějící katalog nevrátí surové klíče; proces ponechá dříve načtené katalogy."""
        os.remove(self.mo_path("cs"))
        with self.assertLogs("core.translation", level="WARNING") as captured:
            self.assertFalse(reload_translation_catalogs_if_changed())
        self.assertIn("core.translation.reload_catalogs.missing", captured.output[0])
        self.assertEqual(self.translated("cs"), "Původní")
        self.assertEqual(self.translated("en"), "Original")

    def test_restored_catalog_is_adopted_after_missing(self):
        """Katalog obnovený po výpadku se při další kontrole převezme."""
        os.remove(self.mo_path("cs"))
        with self.assertLogs("core.translation", level="WARNING"):
            self.assertFalse(reload_translation_catalogs_if_changed())
        self.write_catalog("cs", {TEST_KEY: "Obnovený překlad"})
        self.assertTrue(reload_translation_catalogs_if_changed())
        self.assertEqual(self.translated("cs"), "Obnovený překlad")

    def test_persistent_corrupt_catalog_is_not_retried(self):
        """Nezměněný poškozený katalog se sestavuje i loguje jen jednou, ne při každé kontrole."""
        with open(self.mo_path("cs"), "wb") as target:
            target.write(b"\x00" * 10)
        with (
            patch.object(
                catalog_reload, "_reload_translation_catalogs", wraps=catalog_reload._reload_translation_catalogs
            ) as reload_spy,
            self.assertLogs("core.translation", level="WARNING") as captured,
        ):
            for _attempt in range(3):
                self.assertFalse(reload_translation_catalogs_if_changed())
        self.assertEqual(reload_spy.call_count, 1)
        self.assertEqual(len(captured.records), 1)
        self.assertEqual(self.translated("cs"), "Původní")

    def test_persistent_missing_catalog_is_not_retried(self):
        """Trvale chybějící katalog nespouští sestavení a varování se zapíše jen jednou."""
        os.remove(self.mo_path("cs"))
        with (
            patch.object(
                catalog_reload, "_reload_translation_catalogs", wraps=catalog_reload._reload_translation_catalogs
            ) as reload_spy,
            self.assertLogs("core.translation", level="WARNING") as captured,
        ):
            for _attempt in range(3):
                self.assertFalse(reload_translation_catalogs_if_changed())
        reload_spy.assert_not_called()
        self.assertEqual(len(captured.records), 1)

    def test_active_language_is_preserved_across_reload(self):
        """Aktivní angličtina zůstane aktivní a ukazuje na nově načtený katalog."""
        self.write_catalogs({TEST_KEY: "Opravený překlad"}, {TEST_KEY: "Corrected translation"})
        translation.activate("en")
        self.assertTrue(reload_translation_catalogs_if_changed())
        self.assertEqual(translation.get_language(), "en")
        self.assertEqual(translation.gettext(TEST_KEY), "Corrected translation")


class DjangoTranslationInternalsTest(SimpleTestCase):
    """Hlídá interní mezipaměti Djanga a Pythonu, které ``core.translation`` při načtení vyměňuje."""

    def test_internals_used_for_reload_exist(self):
        """Při upgradu Djanga nebo Pythonu selže tento test dřív než produkce."""
        self.assertIsInstance(trans_real._translations, dict)
        self.assertTrue(hasattr(trans_real, "_default"))
        self.assertTrue(hasattr(trans_real, "_active"))
        self.assertTrue(callable(trans_real.translation))
        self.assertTrue(callable(trans_real.to_locale))
        self.assertIsInstance(gettext_module._translations, dict)


class TranslationCatalogReloadMiddlewareTest(RuntimeCatalogTestMixin, SimpleTestCase):
    """Testy middleware, které kontroluje katalogy na začátku požadavku."""

    def setUp(self):
        """Připraví katalogy a řetězec ``TranslationCatalogReloadMiddleware`` → ``LocaleMiddleware``."""
        super().setUp()
        from core.middleware import TranslationCatalogReloadMiddleware
        from django.middleware.locale import LocaleMiddleware

        self.write_catalogs({TEST_KEY: "Původní"}, {TEST_KEY: "Original"})
        self.chain = TranslationCatalogReloadMiddleware(
            LocaleMiddleware(lambda request: HttpResponse(translation.gettext(TEST_KEY)))
        )
        self.factory = RequestFactory()

    def request(self, language_code):
        """
        Projde požadavkem s jazykem vybraným cookie.

        :param language_code: Kód jazyka uložený v cookie jazyka.
        :return: Text odpovědi.
        """
        request = self.factory.get("/")
        request.COOKIES[settings.LANGUAGE_COOKIE_NAME] = language_code
        return self.chain(request).content.decode()

    def test_next_request_renders_changed_catalog(self):
        """Po úpravě katalogu na serveru vykreslí další požadavek nový text."""
        self.assertEqual(self.request("cs"), "Původní")
        self.write_catalog("cs", {TEST_KEY: "Opravený překlad"})
        self.assertEqual(self.request("cs"), "Opravený překlad")

    def test_english_request_stays_english_during_reload(self):
        """Požadavek s vybranou angličtinou se vykreslí anglicky i při načtení katalogů."""
        self.assertEqual(self.request("en"), "Original")
        self.write_catalogs({TEST_KEY: "Opravený překlad"}, {TEST_KEY: "Corrected translation"})
        self.assertEqual(self.request("en"), "Corrected translation")


RELOAD_MIDDLEWARE = "core.middleware.TranslationCatalogReloadMiddleware"
LOCALE_MIDDLEWARE = "django.middleware.locale.LocaleMiddleware"


class MiddlewareOrderTest(SimpleTestCase):
    """Hlídá, že kontrola katalogů běží v reálném ``MIDDLEWARE`` těsně před ``LocaleMiddleware``."""

    def assert_reload_runs_right_before_locale(self, middleware):
        """
        Ověří, že ``TranslationCatalogReloadMiddleware`` stojí bezprostředně před ``LocaleMiddleware``.

        Jen v tomto pořadí se katalogy načtou dřív, než ``LocaleMiddleware`` aktivuje jazyk požadavku.

        :param middleware: Seznam cest k middleware v pořadí zpracování.
        """
        self.assertIn(RELOAD_MIDDLEWARE, middleware)
        self.assertIn(LOCALE_MIDDLEWARE, middleware)
        self.assertEqual(middleware.index(RELOAD_MIDDLEWARE) + 1, middleware.index(LOCALE_MIDDLEWARE))

    def test_reload_middleware_runs_right_before_locale_middleware(self):
        """Nastavení projektu registruje kontrolu katalogů těsně před ``LocaleMiddleware``."""
        self.assert_reload_runs_right_before_locale(list(settings.MIDDLEWARE))

    def test_swapped_order_is_rejected(self):
        """Protizkouška: prohozené pořadí kontrola odhalí."""
        swapped = list(settings.MIDDLEWARE)
        reload_index = swapped.index(RELOAD_MIDDLEWARE)
        locale_index = swapped.index(LOCALE_MIDDLEWARE)
        swapped[reload_index], swapped[locale_index] = swapped[locale_index], swapped[reload_index]
        with self.assertRaises(AssertionError):
            self.assert_reload_runs_right_before_locale(swapped)


class CeleryTaskPrerunReloadTest(RuntimeCatalogTestMixin, SimpleTestCase):
    """Testy kontroly katalogů před spuštěním úlohy Celery."""

    def test_receiver_is_connected_on_startup(self):
        """``CoreConfig.ready()`` připojí kontrolu katalogů na signál ``task_prerun``."""
        from celery.signals import task_prerun

        dispatch_uid = "core.translation.reload_translation_catalogs_on_task_prerun"
        self.assertTrue(any(lookup_key[0] == dispatch_uid for lookup_key, _receiver in task_prerun.receivers))

    def test_task_prerun_adopts_changed_catalog(self):
        """Úloha spuštěná po úpravě katalogu překládá podle nového katalogu."""
        from celery.signals import task_prerun

        connect_translation_catalog_signals()
        self.write_catalogs({TEST_KEY: "Původní"}, {TEST_KEY: "Original"})
        task_prerun.send(sender=None, task_id="test", task=None, args=(), kwargs={})
        self.assertEqual(self.translated("cs"), "Původní")

        self.write_catalog("cs", {TEST_KEY: "Opravený překlad"})
        task_prerun.send(sender=None, task_id="test", task=None, args=(), kwargs={})
        self.assertEqual(self.translated("cs"), "Opravený překlad")


@override_settings(SITE_URL="https://amcr.example.test")
class NotificationEmailFooterReloadTest(RuntimeCatalogTestMixin, SimpleTestCase):
    """Regresní test ARUP-CAS/aiscr-webamcr#4362: patička e-mailu po změně katalogu v běžícím procesu."""

    context = {"ident_cely": "C-202304651", "katastr": "Krásná Hora nad Vltavou", "title": "AMČR"}

    def render_email(self):
        """
        Vykreslí notifikační e-mail E-NZ-01.

        :return: HTML e-mailu.
        """
        return render_to_string("emails/E-NZ-01.html", self.context)

    def test_both_footers_translated_after_catalog_change(self):
        """
        Katalog načtený před změnou (stav po nasazení) neponechá v patičce surové klíče.

        Proces nejdřív vykreslí e-mail se starými katalogy bez hesel patičky, pak se katalogy
        změní (nasazení nebo úprava na serveru) a další e-mail po kontrole musí mít obě
        patičky přeložené.
        """
        self.write_catalogs({TEST_KEY: "Původní"}, {TEST_KEY: "Original"})
        reload_translation_catalogs_if_changed()
        self.assertIn(FOOTER_AUTOMATIC, self.render_email())

        self.write_catalogs(
            {FOOTER_AUTOMATIC: "Automatická zpráva AMČR.", FOOTER_SENT_FROM: "Odesláno z"},
            {FOOTER_AUTOMATIC: "Automatic AMCR message.", FOOTER_SENT_FROM: "Sent from"},
        )
        reload_translation_catalogs_if_changed()
        html = self.render_email()

        self.assertNotIn(FOOTER_AUTOMATIC, html)
        self.assertNotIn(FOOTER_SENT_FROM, html)
        self.assertIn("Automatická zpráva AMČR.", html)
        self.assertIn("Odesláno z:", html)
        self.assertIn("Automatic AMCR message.", html)
        self.assertIn("Sent from:", html)


class AtomicCatalogImportTest(SimpleTestCase):
    """Testy atomické náhrady runtime katalogu při importu."""

    OLD_PO = 'msgid ""\nmsgstr ""\n"Content-Type: text/plain; charset=UTF-8\n"\n\nmsgid "{key}"\nmsgstr "Původní"\n'
    NEW_PO = 'msgid ""\nmsgstr ""\n"Content-Type: text/plain; charset=UTF-8\n"\n\nmsgid "{key}"\nmsgstr "Importovaný"\n'

    def setUp(self):
        """Vytvoří dočasný adresář ``cs/LC_MESSAGES`` s původním ``django.po`` a ``django.mo``."""
        super().setUp()
        locale_dir = tempfile.mkdtemp(prefix="amcr-import-")
        self.addCleanup(shutil.rmtree, locale_dir, ignore_errors=True)
        self.locale_dir = locale_dir
        self.catalog_dir = os.path.join(locale_dir, "cs", "LC_MESSAGES")
        os.makedirs(self.catalog_dir)
        self.po_path = os.path.join(self.catalog_dir, "django.po")
        self.mo_path = os.path.join(self.catalog_dir, "django.mo")
        old_po = self.OLD_PO.format(key=TEST_KEY)
        with open(self.po_path, "w", encoding="utf-8") as target:
            target.write(old_po)
        polib.pofile(old_po).save_as_mofile(self.mo_path)
        self.new_po = self.NEW_PO.format(key=TEST_KEY)

    def uploaded(self):
        """
        Vrátí nahraný soubor s novým katalogem.

        :return: ``SimpleUploadedFile`` s obsahem ``NEW_PO``.
        """
        return SimpleUploadedFile("django.po", self.new_po.encode("utf-8"))

    def temporary_files(self):
        """
        Vrátí dočasné soubory, které po náhradě nesmí v adresáři katalogu zůstat.

        :return: Seznam názvů souborů začínajících tečkou nebo končících ``.tmp``.
        """
        return [name for name in os.listdir(self.catalog_dir) if name.startswith(".") or name.endswith(".tmp")]

    def mo_text(self):
        """
        Přeloží ``TEST_KEY`` přímo z aktuálního ``django.mo``.

        :return: Přeložený text.
        """
        with open(self.mo_path, "rb") as source:
            return gettext_module.GNUTranslations(source).gettext(TEST_KEY)

    def test_import_replaces_po_and_mo_and_keeps_backup(self):
        """Import nahradí ``.po`` i ``.mo``, původní ``.po`` uloží do zálohy a nenechá dočasné soubory."""
        original_mode = os.stat(self.mo_path).st_mode
        backup_path = import_translation_catalog(self.po_path, self.uploaded())

        with open(self.po_path, encoding="utf-8") as source:
            self.assertEqual(source.read(), self.new_po)
        self.assertEqual(self.mo_text(), "Importovaný")
        self.assertRegex(os.path.basename(backup_path), r"^django_backup_\d{14}\.po$")
        with open(backup_path, encoding="utf-8") as source:
            self.assertIn('msgstr "Původní"', source.read())
        self.assertEqual(self.temporary_files(), [])
        self.assertEqual(os.stat(self.mo_path).st_mode, original_mode)

    def backup_files(self):
        """
        Vrátí zálohy katalogu v adresáři katalogu.

        :return: Seznam názvů souborů odpovídajících ``django_backup_<čas>.po``.
        """
        return [name for name in os.listdir(self.catalog_dir) if re.fullmatch(r"django_backup_\d{14}\.po", name)]

    def assert_catalog_unchanged(self):
        """Ověří, že ``.po`` i ``.mo`` drží původní obsah, nevznikla záloha a nezůstal dočasný soubor."""
        with open(self.po_path, encoding="utf-8") as source:
            self.assertIn('msgstr "Původní"', source.read())
        self.assertEqual(self.mo_text(), "Původní")
        self.assertEqual(self.backup_files(), [])
        self.assertEqual(self.temporary_files(), [])

    def test_upload_is_written_once(self):
        """Nahraný soubor se při importu čte a zapisuje jen jednou."""
        uploaded = self.uploaded()
        with patch.object(uploaded, "chunks", wraps=uploaded.chunks) as chunks_spy:
            import_translation_catalog(self.po_path, uploaded)
        self.assertEqual(chunks_spy.call_count, 1)
        self.assertEqual(self.mo_text(), "Importovaný")

    def test_unparsable_upload_leaves_catalog_unchanged(self):
        """Soubor, který polib nenačte, katalog ani seznam záloh nezmění a nenechá dočasné soubory."""
        broken = SimpleUploadedFile("django.po", b'msgid "x"\nthis is not a po line\n' + b"#" * 1000)
        with self.assertRaises(Exception):
            import_translation_catalog(self.po_path, broken)
        self.assert_catalog_unchanged()

    def test_failed_mo_compilation_leaves_catalog_unchanged(self):
        """Selhání kompilace ``.mo`` ponechá ``.po``, ``.mo`` i seznam záloh beze změny."""
        with (
            patch.object(polib.POFile, "save_as_mofile", side_effect=OSError("disk full")),
            self.assertRaises(OSError),
        ):
            import_translation_catalog(self.po_path, self.uploaded())
        self.assert_catalog_unchanged()

    def test_failed_write_keeps_target_and_removes_temporary_file(self):
        """Chyba při zápisu ponechá původní soubor beze změny a smaže dočasný soubor."""

        def failing_write(temp_path):
            """
            Zapíše část obsahu a selže, jako by došlo místo na disku.

            :param temp_path: Cesta k dočasnému souboru.
            """
            with open(temp_path, "wb") as target:
                target.write(b"\x00partial")
            raise OSError("disk full")

        with self.assertRaises(OSError):
            replace_file_atomically(self.mo_path, failing_write)
        self.assertEqual(self.mo_text(), "Původní")
        self.assertEqual(self.temporary_files(), [])


class TranslationImportViewTest(AtomicCatalogImportTest):
    """Test pohledu ``TranslationImportView``: atomický import a zachování seznamu záloh."""

    def test_view_import_keeps_backup_listed(self):
        """Po importu přes pohled drží soubory nový obsah a záloha je v seznamu katalogů se zálohami."""
        from core.utils import find_pos_with_backup
        from core.views import TranslationImportView

        view = TranslationImportView()
        view.request = RequestFactory().post("/")
        view.kwargs = {"po_filter": "project", "lang_id": "cs", "idx": "0"}
        form = MagicMock(cleaned_data={"file": self.uploaded()})
        with (
            patch.object(TranslationImportView, "po_file_path", new_callable=PropertyMock, return_value=self.po_path),
            patch("core.views.messages") as messages_mock,
            patch("core.views.reverse", return_value="/translations/"),
        ):
            response = view.form_valid(form)

        self.assertEqual(response.status_code, 302)
        messages_mock.add_message.assert_called_once()
        with open(self.po_path, encoding="utf-8") as source:
            self.assertEqual(source.read(), self.new_po)
        self.assertEqual(self.mo_text(), "Importovaný")
        self.assertEqual(self.temporary_files(), [])
        with override_settings(LOCALE_PATHS=[self.locale_dir]):
            listed = find_pos_with_backup("cs", project_apps=False, django_apps=False, third_party_apps=False)
        backups = [path for path in listed if re.search(r"django_backup_\d{14}\.po$", path)]
        self.assertEqual(len(backups), 1)

    def call_view(self, uploaded, po_file_path_mock):
        """
        Zavolá ``TranslationImportView.form_valid`` s nahraným souborem a podvrženou cestou katalogu.

        :param uploaded: Nahraný soubor předaný ve ``cleaned_data``.
        :param po_file_path_mock: ``PropertyMock`` nahrazující vlastnost ``po_file_path``.
        :return: Dvojice ``(odpověď, mock modulu messages)``.
        """
        from core.views import TranslationImportView

        view = TranslationImportView()
        view.request = RequestFactory().post("/")
        view.kwargs = {"po_filter": "project", "lang_id": "cs", "idx": "0"}
        form = MagicMock(cleaned_data={"file": uploaded})
        with (
            patch.object(TranslationImportView, "po_file_path", po_file_path_mock),
            patch("core.views.messages") as messages_mock,
            patch("core.views.reverse", return_value="/translations/"),
        ):
            return view.form_valid(form), messages_mock

    def test_view_writes_upload_once(self):
        """Pohled už nevytváří vlastní ověřovací kopii; nahraný soubor se zapíše jen jednou."""
        uploaded = self.uploaded()
        with patch.object(uploaded, "chunks", wraps=uploaded.chunks) as chunks_spy:
            response, _messages = self.call_view(uploaded, PropertyMock(return_value=self.po_path))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(chunks_spy.call_count, 1)

    def test_view_reports_failed_import_as_error_message(self):
        """Neúspěšný import vrátí přesměrování s chybovou hláškou místo výjimky (HTTP 500)."""
        broken = SimpleUploadedFile("django.po", b'msgid "x"\nthis is not a po line\n' + b"#" * 1000)
        response, messages_mock = self.call_view(broken, PropertyMock(return_value=self.po_path))
        self.assertEqual(response.status_code, 302)
        messages_mock.add_message.assert_called_once()
        self.assertIs(messages_mock.add_message.call_args.args[1], messages_mock.ERROR)
        self.assert_catalog_unchanged()

    def test_view_rejects_user_without_language_rights_before_reading_upload(self):
        """Uživatel bez práva překládat jazyk dostane 404 dřív, než se nahraný soubor přečte."""
        uploaded = self.uploaded()
        with (
            patch.object(uploaded, "chunks", wraps=uploaded.chunks) as chunks_spy,
            self.assertRaises(Http404),
        ):
            self.call_view(uploaded, PropertyMock(side_effect=Http404))
        chunks_spy.assert_not_called()
        self.assert_catalog_unchanged()
