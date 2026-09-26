"""
Testy odvození přípony souboru podle detekovaného MIME typu (issue #4289).

Při nahrazení souboru se dříve přípona brala z uživatelského názvu přes ``split(".")[-1]`` bez
jakékoli validace, čímž se zahodila korekce podle detekovaného MIME typu provedená o několik řádků
dřív. Při nahrání nového souboru bez tečky zase ``replace_last`` nahradil celý vygenerovaný název
příponou a ztratil se ident i suffix; API pro fotografie samostatných nálezů příponu neopravovalo vůbec.
Všechny tři cesty teď používají :func:`core.soubor_naming.get_mime_safe_soubor_name`, kterou testy
pokrývají. Nepotřebují databázi ani běžící Fedoru – funkce pracuje jen s řetězci.
"""

from core.soubor_naming import get_mime_safe_soubor_name
from django.test import SimpleTestCase

#: Přípony vracené ``Soubor.get_file_extension_by_mime`` pro ``application/pdf``.
PDF_EXTENSIONS = ("pdf",)
#: Přípony vracené ``Soubor.get_file_extension_by_mime`` pro ``image/jpeg``.
JPEG_EXTENSIONS = ("jpeg", "jpg", "jpe", "jfif", "jfif-tbnl", "jif", "pjpg")


class NahrazeniSouboruTest(SimpleTestCase):
    """Testy odvození názvu při nahrání nové verze souboru (základ z databáze, přípona od uživatele)."""

    def test_pripona_odpovidajici_mime_se_prevezme(self):
        """Přípona nahrávaného souboru se použije, když odpovídá detekovanému MIME typu."""
        self.assertEqual(
            get_mime_safe_soubor_name("CDL202500001F001.jpg", "sken.pdf", PDF_EXTENSIONS),
            "CDL202500001F001.pdf",
        )

    def test_pripona_neodpovidajici_mime_se_nahradi(self):
        """
        Přípona neodpovídající obsahu se nahradí příponou z MIME typu.

        Klíčový případ #4289: PDF přejmenované na ``.jpg`` projde i klientským filtrem Dropzone,
        protože prohlížeč hlásí ``image/jpeg`` podle přípony.
        """
        self.assertEqual(
            get_mime_safe_soubor_name("CDL202500001F001.jpg", "foto.jpg", PDF_EXTENSIONS),
            "CDL202500001F001.pdf",
        )

    def test_alternativni_pripona_ze_sady_zustane(self):
        """Kterákoli přípona ze sady odpovídající MIME typu se zachová, nejen ta první."""
        self.assertEqual(
            get_mime_safe_soubor_name("CDL202500001F001.jpg", "foto.jpeg", JPEG_EXTENSIONS),
            "CDL202500001F001.jpeg",
        )

    def test_pripona_se_prevede_na_mala_pismena(self):
        """Platná přípona s velkými písmeny se uloží malými, u nového i u historického ``.JPG`` názvu."""
        for current_name in ("CDL202500001F001.jpg", "CDL202500001F001.JPG"):
            with self.subTest(current_name=current_name):
                self.assertEqual(
                    get_mime_safe_soubor_name(current_name, "FOTO.JPG", JPEG_EXTENSIONS),
                    "CDL202500001F001.jpg",
                )

    def test_nahravany_nazev_bez_tecky_se_nestane_priponou(self):
        """Celý název bez tečky se nesmí stát příponou – použije se přípona z MIME typu."""
        self.assertEqual(
            get_mime_safe_soubor_name("CDL202500001F001.jpg", "bezpripony", PDF_EXTENSIONS),
            "CDL202500001F001.pdf",
        )

    def test_soucasny_nazev_bez_tecky_zustane_zakladem(self):
        """Nemá-li současný název příponu, zůstane celý základem a nová přípona se přidá."""
        self.assertEqual(
            get_mime_safe_soubor_name("CDL202500001F001", "sken.pdf", PDF_EXTENSIONS),
            "CDL202500001F001.pdf",
        )

    def test_oddelovac_cesty_se_do_nazvu_nedostane(self):
        """
        Žádný zkonstruovaný název nedostane do výsledku oddělovač cesty ani ``..``.

        Django tyto názvy ořízne už v ``MultiPartParser.sanitize_file_name``, funkce se na to
        ale nespoléhá – základ názvu bere vždy ze současného názvu v databázi.
        """
        for uploaded_name in ("../x", "..\\x", "/etc/passwd", "..", "a/b.pdf", "sken.pdf/../x"):
            with self.subTest(uploaded_name=uploaded_name):
                new_name = get_mime_safe_soubor_name("CDL202500001F001.jpg", uploaded_name, PDF_EXTENSIONS)
                self.assertEqual(new_name, "CDL202500001F001.pdf")
                self.assertNotIn("/", new_name)
                self.assertNotIn("\\", new_name)
                self.assertNotIn("..", new_name)


class NovySouborTest(SimpleTestCase):
    """
    Testy korekce vygenerovaného názvu při nahrání nového souboru.

    Webové nahrání i API předávají vygenerovaný název (``get_next_soubor_name``, u projektů
    ``get_projekt_soubor_name``) jako oba parametry – jeho přípona pochází od uživatele.
    """

    def test_shodna_pripona_zustane(self):
        """Vygenerovaný název s příponou odpovídající MIME typu zůstane beze změny."""
        self.assertEqual(
            get_mime_safe_soubor_name("CDL202500001F001.pdf", "CDL202500001F001.pdf", PDF_EXTENSIONS),
            "CDL202500001F001.pdf",
        )

    def test_neodpovidajici_pripona_se_opravi(self):
        """PDF nahrané jako ``.jpg`` dostane příponu ``.pdf`` (případ API pro fotografie nálezů)."""
        self.assertEqual(
            get_mime_safe_soubor_name("CDL202500001F001.jpg", "CDL202500001F001.jpg", PDF_EXTENSIONS),
            "CDL202500001F001.pdf",
        )

    def test_nazev_bez_tecky_si_zachova_ident_a_suffix(self):
        """
        Vygenerovaný název bez tečky si ponechá ident i suffix a dostane příponu z MIME typu.

        Dříve ``replace_last`` nahradil celý název příponou, takže z ``XM202500001F001`` zbylo jen ``pdf``.
        """
        for generated_name in ("XM202500001F001", "C_202500001_bezpripony"):
            with self.subTest(generated_name=generated_name):
                self.assertEqual(
                    get_mime_safe_soubor_name(generated_name, generated_name, PDF_EXTENSIONS),
                    f"{generated_name}.pdf",
                )

    def test_velka_pripona_se_prevede_na_mala(self):
        """Nahraný ``FOTO.JPG`` se uloží s příponou ``.jpg``."""
        self.assertEqual(
            get_mime_safe_soubor_name("CDL202500001F001.JPG", "CDL202500001F001.JPG", JPEG_EXTENSIONS),
            "CDL202500001F001.jpg",
        )
