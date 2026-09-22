"""
Testy odvození přípony při nahrání nové verze souboru (issue #4289).

Při nahrazení souboru se dříve přípona brala z uživatelského názvu přes ``split(".")[-1]`` bez
jakékoli validace, čímž se zahodila korekce podle detekovaného MIME typu provedená o několik řádků
dřív. Testy pokrývají :func:`core.soubor_naming.get_updated_soubor_name`, která odvození převzala.
Nepotřebují databázi ani běžící Fedoru – funkce pracuje jen s řetězci.
"""

from core.soubor_naming import get_updated_soubor_name
from django.test import SimpleTestCase

#: Přípony vracené ``Soubor.get_file_extension_by_mime`` pro ``application/pdf``.
PDF_EXTENSIONS = ("pdf",)
#: Přípony vracené ``Soubor.get_file_extension_by_mime`` pro ``image/jpeg``.
JPEG_EXTENSIONS = ("jpeg", "jpg", "jpe", "jfif", "jfif-tbnl", "jif", "pjpg")


class UpdatedSouborNameTest(SimpleTestCase):
    """Testy odvození názvu souboru při nahrání jeho nové verze."""

    def test_pripona_odpovidajici_mime_se_prevezme(self):
        """Přípona nahrávaného souboru se použije, když odpovídá detekovanému MIME typu."""
        self.assertEqual(
            get_updated_soubor_name("CDL202500001F001.jpg", "sken.pdf", PDF_EXTENSIONS),
            "CDL202500001F001.pdf",
        )

    def test_pripona_neodpovidajici_mime_se_nahradi(self):
        """
        Přípona neodpovídající obsahu se nahradí příponou z MIME typu.

        Klíčový případ #4289: PDF přejmenované na ``.jpg`` projde i klientským filtrem Dropzone,
        protože prohlížeč hlásí ``image/jpeg`` podle přípony.
        """
        self.assertEqual(
            get_updated_soubor_name("CDL202500001F001.jpg", "foto.jpg", PDF_EXTENSIONS),
            "CDL202500001F001.pdf",
        )

    def test_alternativni_pripona_ze_sady_zustane(self):
        """Kterákoli přípona ze sady odpovídající MIME typu se zachová, nejen ta první."""
        self.assertEqual(
            get_updated_soubor_name("CDL202500001F001.jpg", "foto.jpeg", JPEG_EXTENSIONS),
            "CDL202500001F001.jpeg",
        )

    def test_velikost_pismen_platne_pripony_zustava(self):
        """Nahrazení ``.JPG`` souboru jeho novou verzí název nemění."""
        current_name = "CDL202500001F001.JPG"
        self.assertEqual(get_updated_soubor_name(current_name, "FOTO.JPG", JPEG_EXTENSIONS), current_name)

    def test_nahravany_nazev_bez_tecky_se_nestane_priponou(self):
        """Celý název bez tečky se nesmí stát příponou – použije se přípona z MIME typu."""
        self.assertEqual(
            get_updated_soubor_name("CDL202500001F001.jpg", "bezpripony", PDF_EXTENSIONS),
            "CDL202500001F001.pdf",
        )

    def test_soucasny_nazev_bez_tecky_zustane_zakladem(self):
        """Nemá-li současný název příponu, zůstane celý základem a nová přípona se přidá."""
        self.assertEqual(
            get_updated_soubor_name("CDL202500001F001", "sken.pdf", PDF_EXTENSIONS),
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
                new_name = get_updated_soubor_name("CDL202500001F001.jpg", uploaded_name, PDF_EXTENSIONS)
                self.assertEqual(new_name, "CDL202500001F001.pdf")
                self.assertNotIn("/", new_name)
                self.assertNotIn("\\", new_name)
                self.assertNotIn("..", new_name)
