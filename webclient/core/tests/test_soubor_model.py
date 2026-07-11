import io

from core.models import Soubor
from django.test import SimpleTestCase
from PIL import Image
from pypdf import PdfWriter


class SouborCalculateRozsahTest(SimpleTestCase):
    """Testy pro výpočet rozsahu souboru."""

    def _pdf_data(self, page_count):
        """Vytvoří PDF s daným počtem stran v paměti."""
        writer = PdfWriter()
        for _ in range(page_count):
            writer.add_blank_page(width=72, height=72)
        data = io.BytesIO()
        writer.write(data)
        data.seek(0)
        return data

    def _tif_data(self, frame_count):
        """Vytvoří vícesnímkový TIF v paměti."""
        images = [Image.new("RGB", (1, 1), color=(index, index, index)) for index in range(frame_count)]
        data = io.BytesIO()
        images[0].save(data, format="TIFF", save_all=True, append_images=images[1:])
        data.seek(0)
        return data

    def test_calculate_rozsah_returns_pdf_page_count(self):
        """calculate_rozsah() vrátí počet stran PDF souboru."""
        soubor = Soubor(nazev="dokument.pdf")

        rozsah = soubor.calculate_rozsah(binary_data=self._pdf_data(3))

        self.assertEqual(rozsah, 3)

    def test_calculate_rozsah_returns_tif_frame_count(self):
        """calculate_rozsah() vrátí počet snímků TIF souboru."""
        soubor = Soubor(nazev="snimky.tif")

        rozsah = soubor.calculate_rozsah(binary_data=self._tif_data(2))

        self.assertEqual(rozsah, 2)

    def test_calculate_rozsah_returns_one_for_tif_with_foreign_content(self):
        """calculate_rozsah() vrátí 1 pro soubor s příponou TIF, jehož obsah je jiný obrazový formát bez n_frames."""
        data = io.BytesIO()
        Image.new("RGB", (1, 1)).save(data, format="JPEG")
        data.seek(0)
        soubor = Soubor(nazev="prejmenovany.tif")

        rozsah = soubor.calculate_rozsah(binary_data=data)

        self.assertEqual(rozsah, 1)

    def test_calculate_rozsah_returns_one_for_other_file_type(self):
        """calculate_rozsah() vrátí 1 pro soubor bez zvláštního zpracování."""
        soubor = Soubor(nazev="poznamka.txt")

        rozsah = soubor.calculate_rozsah(binary_data=io.BytesIO(b"plain text"))

        self.assertEqual(rozsah, 1)

    def test_calculate_rozsah_keeps_existing_value_without_binary_data(self):
        """calculate_rozsah() bez binárních dat vrátí už uložený rozsah."""
        soubor = Soubor(nazev="dokument.pdf", rozsah=7)

        rozsah = soubor.calculate_rozsah()

        self.assertEqual(rozsah, 7)
        self.assertEqual(soubor.rozsah, 7)
