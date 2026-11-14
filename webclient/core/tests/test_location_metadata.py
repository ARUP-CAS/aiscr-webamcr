"""Regrese hledání a odstranění polohy mimo GPS IFD (XMP, PNG, MPF) bez Djanga a Fedory."""

import io
import struct
import unittest

from core import image_location
from core.tests import location_fixtures as fx
from lxml import etree
from PIL import ExifTags, Image

DC_FORMAT = etree.QName(fx.NS_DC, "format").text
HDRGM_VERSION = etree.QName(fx.NS_HDRGM, "Version").text


def _xmp_root(packet: bytes):
    """Rozebere paket XMP pro kontrolu výsledku.

    :param packet: Paket XMP.
    :return: Kořen dokumentu.
    """
    return image_location._parse_xmp(packet)


def _description(packet: bytes):
    """Vrátí první ``rdf:Description`` paketu.

    :param packet: Paket XMP.
    :return: Element ``rdf:Description``.
    """
    return next(_xmp_root(packet).iter(etree.QName(image_location.NS_RDF, "Description").text))


def _jpeg_xmp(data: bytes) -> bytes | None:
    """Vrátí paket XMP z hlavního obrázku JPEG.

    :param data: Obrázek JPEG.
    :return: Paket XMP, nebo ``None``.
    """
    segments, _ = image_location._parse_jpeg_header(data)
    for segment in segments:
        if image_location._app1(segment, image_location.XMP_JPEG_SIGNATURE):
            return segment.payload[len(image_location.XMP_JPEG_SIGNATURE) :]
    return None


class ExifInPlaceTests(unittest.TestCase):
    """GPS se z EXIF odstraní bez změny délky a ostatních struktur."""

    def test_gps_removed_and_values_zeroed(self):
        """Odkaz i hodnoty GPS zmizí, ostatní tagy a délka zůstanou."""
        original = fx.exif_bytes()
        latitude = struct.pack(">II", int(fx.LATITUDE[0]), 1)
        self.assertIn(latitude, original)
        cleaned = image_location.remove_exif_gps(original)
        self.assertEqual(len(cleaned), len(original))
        self.assertFalse(image_location.exif_has_gps(cleaned))
        self.assertNotIn(latitude, cleaned)
        exif = Image.Exif()
        exif.load(cleaned)
        self.assertNotIn(ExifTags.IFD.GPSInfo, exif)
        self.assertEqual(exif[ExifTags.Base.Make], "Cam")

    def test_thumbnail_ifd_is_preserved(self):
        """IFD1 s vloženým náhledem zůstane platný."""
        thumbnail = fx.jpeg(image=Image.new("RGB", (8, 8), "green")).getvalue()
        cleaned = image_location.remove_exif_gps(fx.exif_with_thumbnail(thumbnail))
        self.assertFalse(image_location.exif_has_gps(cleaned))
        exif = Image.Exif()
        exif.load(cleaned)
        ifd1 = exif.get_ifd(ExifTags.IFD.IFD1)
        start = len(image_location.EXIF_SIGNATURE) + ifd1[ExifTags.Base.JpegIFOffset]
        self.assertEqual(cleaned[start : start + ifd1[ExifTags.Base.JpegIFByteCount]], thumbnail)

    def test_without_gps_is_unchanged(self):
        """EXIF bez GPS se vrátí jako stejný objekt."""
        original = fx.exif_bytes(gps=False)
        self.assertIs(image_location.remove_exif_gps(original), original)

    def test_invalid_header_is_rejected(self):
        """EXIF s neplatným pořadím bajtů nelze bezpečně zpracovat."""
        with self.assertRaises(ValueError):
            image_location.exif_has_gps(image_location.EXIF_SIGNATURE + b"XX*\x00\x08\x00\x00\x00")


class XmpTests(unittest.TestCase):
    """Pravidlo polohy v XMP a jeho čištění."""

    def test_location_forms_are_removed(self):
        """Atribut, element, DJI i struktura LocationCreated zmizí, ostatní zůstane."""
        for name, packet in (
            ("attribute", fx.XMP_GPS_ATTRIBUTE),
            ("element", fx.XMP_GPS_ELEMENT),
            ("dji", fx.XMP_DJI),
            ("location_created", fx.XMP_LOCATION_CREATED),
        ):
            with self.subTest(form=name):
                self.assertTrue(image_location.has_xmp_location(packet))
                cleaned = image_location.strip_xmp_location(packet)
                self.assertFalse(image_location.has_xmp_location(cleaned))
                self.assertEqual(_description(cleaned).get(DC_FORMAT), "image/jpeg")
                self.assertNotIn(b"Praha", cleaned)
                self.assertTrue(cleaned.startswith(b"<?xpacket"))

    def test_clean_packet_is_unchanged(self):
        """XMP bez polohy se vrátí beze změny."""
        self.assertFalse(image_location.has_xmp_location(fx.XMP_CLEAN))
        self.assertIs(image_location.strip_xmp_location(fx.XMP_CLEAN), fx.XMP_CLEAN)

    def test_unparseable_packet(self):
        """Nečitelné XMP se považuje za polohu a zahodí se celé."""
        broken = b"<x:xmpmeta><rdf:RDF>"
        self.assertTrue(image_location.has_xmp_location(broken))
        self.assertIsNone(image_location.strip_xmp_location(broken))

    def test_entities_are_not_resolved(self):
        """Paket s DTD se nenačte (žádné externí entity) a zahodí se jako nečitelný."""
        packet = b'<!DOCTYPE x [<!ENTITY e SYSTEM "file:///etc/passwd">]><x>&e;</x>'
        self.assertIsNone(image_location.strip_xmp_location(packet))
        self.assertTrue(image_location.has_xmp_location(packet))


class JpegTests(unittest.TestCase):
    """JPEG se čistí bez rekomprese, včetně XMP a rozšířeného XMP."""

    def _clean(self, content):
        """Vyčistí JPEG a ověří, že výsledek je bez polohy.

        :param content: Stream JPEG.
        :return: Vyčištěné bajty.
        """
        output = image_location.remove_jpeg_location(content.getvalue())
        self.assertEqual(image_location.find_location_metadata(io.BytesIO(output)), [])
        self.assertEqual(fx.scan_data(output), fx.scan_data(content.getvalue()))
        return output

    def test_xmp_only_location(self):
        """GPS jen v XMP (bez EXIF GPS) se najde a odstraní."""
        for packet in (fx.XMP_GPS_ATTRIBUTE, fx.XMP_GPS_ELEMENT, fx.XMP_DJI, fx.XMP_LOCATION_CREATED):
            with self.subTest(packet=packet[:80]):
                content = fx.jpeg(exif=fx.exif_bytes(gps=False), xmp_packet=packet)
                self.assertEqual(image_location.find_location_metadata(content), ["jpeg[0].xmp"])
                output = self._clean(content)
                self.assertEqual(_description(_jpeg_xmp(output)).get(DC_FORMAT), "image/jpeg")

    def test_exif_and_xmp_keep_icc_and_quantization(self):
        """EXIF i XMP zmizí, ICC a kvantizační tabulky zůstanou."""
        icc = fx.icc_profile()
        content = fx.jpeg(exif=fx.exif_bytes(), xmp_packet=fx.XMP_GPS_ATTRIBUTE, icc=icc)
        self.assertEqual(image_location.find_location_metadata(content), ["jpeg[0].exif.gps", "jpeg[0].xmp"])
        output = self._clean(content)
        with Image.open(io.BytesIO(output)) as stored, Image.open(content) as original:
            self.assertEqual(stored.info["icc_profile"], icc)
            self.assertEqual(stored.quantization, original.quantization)
            self.assertEqual(stored.getexif()[ExifTags.Base.Make], "Cam")

    def test_extended_xmp(self):
        """Rozšířené XMP s polohou se zahodí i s odkazem HasExtendedXMP."""
        main = fx.xmp(
            f'dc:format="image/jpeg" xmpNote:HasExtendedXMP="{fx.EXTENDED_GUID.decode()}"/>',
            f'xmlns:xmpNote="{image_location.NS_XMP_NOTE}"',
        )
        segments = fx.extended_xmp_segments(fx.XMP_GPS_ELEMENT)
        self.assertGreater(len(segments), 1)
        content = fx.jpeg(xmp_packet=main, segments=segments)
        self.assertEqual(image_location.find_location_metadata(content), ["jpeg[0].xmp_extended"])
        output = self._clean(content)
        self.assertNotIn(image_location.XMP_EXTENSION_SIGNATURE, output)
        description = _description(_jpeg_xmp(output))
        self.assertIsNone(description.get(image_location.XMP_HAS_EXTENDED))
        self.assertEqual(description.get(DC_FORMAT), "image/jpeg")

    def test_unparseable_xmp_is_dropped(self):
        """Nečitelné XMP se zahodí a fotografie zůstane použitelná."""
        content = fx.jpeg(xmp_packet=b"<x:xmpmeta><broken")
        self.assertEqual(image_location.find_location_metadata(content), ["jpeg[0].xmp"])
        output = self._clean(content)
        self.assertIsNone(_jpeg_xmp(output))

    def test_no_location(self):
        """JPEG bez polohy nemá žádný blok."""
        content = fx.jpeg(exif=fx.exif_bytes(gps=False), xmp_packet=fx.XMP_CLEAN)
        self.assertEqual(image_location.find_location_metadata(content), [])

    def test_trailer_is_logged_and_kept(self):
        """Data za EOI se jen zapíšou do logu a ve výstupu zůstanou."""
        trailer = b"ftypmp42 motion photo video"
        content = io.BytesIO(fx.jpeg(exif=fx.exif_bytes()).getvalue() + trailer)
        with self.assertLogs("core.image_location", "WARNING") as logs:
            self.assertEqual(image_location.find_location_metadata(content), ["jpeg[0].exif.gps"])
        self.assertEqual(logs.records[0].block, "jpeg.trailer")
        self.assertTrue(image_location.remove_jpeg_location(content.getvalue()).endswith(trailer))


class MpoTests(unittest.TestCase):
    """Vedlejší obrázky indexu MPF se kontrolují a čistí jednotlivě."""

    def _images(self, data: bytes) -> list[bytes]:
        """Vrátí bajty obrázků podle indexu MPF.

        :param data: Soubor MPO.
        :return: Seznam obrázků.
        """
        return [data[start : start + size] for start, size in image_location._mpf_layout(data).images]

    def _assert_valid(self, output: bytes, original: bytes, pillow_mpo=True):
        """Ověří, že výstup je bez polohy a všechny obrázky indexu MPF jsou čitelné.

        :param output: Vyčištěné MPO.
        :param original: Původní MPO.
        :param pillow_mpo: Zda ověřit i otevření přes Pillow jako MPO; Pillow soubory
            Ultra HDR záměrně otevírá jako jednoduchý JPEG.
        """
        self.assertEqual(image_location.find_location_metadata(io.BytesIO(output)), [])
        self.assertEqual(image_location.image_count(io.BytesIO(output)), 2)
        images = self._images(output)
        with Image.open(io.BytesIO(images[1])) as secondary:
            self.assertEqual(secondary.size, (16, 16))
        if pillow_mpo:
            with Image.open(io.BytesIO(output)) as stored:
                self.assertEqual(stored.format, "MPO")
                self.assertEqual(stored.n_frames, 2)
                stored.seek(1)
                self.assertEqual(stored.size, (16, 16))
        for new, old in zip(images, self._images(original)):
            self.assertEqual(fx.scan_data(new), fx.scan_data(old))

    def test_gps_only_in_secondary_image(self):
        """GPS ve vedlejším obrázku se najde; hlavní obrázek zůstane bajtově shodný."""
        content = fx.mpo(primary_exif=fx.exif_bytes(gps=False), secondary_exif=fx.exif_bytes(make="Secondary"))
        original = content.getvalue()
        self.assertEqual(image_location.find_location_metadata(content), ["jpeg[1].exif.gps"])
        output = image_location.remove_jpeg_location(original)
        self._assert_valid(output, original)
        self.assertEqual(self._images(output)[0], self._images(original)[0])
        with Image.open(io.BytesIO(output)) as stored:
            stored.seek(1)
            self.assertEqual(stored.getexif()[ExifTags.Base.Make], "Secondary")

    def test_gps_only_in_primary_image(self):
        """GPS v hlavním obrázku se odstraní; vedlejší obrázek zůstane bajtově shodný."""
        content = fx.mpo(primary_exif=fx.exif_bytes(), secondary_exif=fx.exif_bytes(gps=False))
        original = content.getvalue()
        self.assertEqual(image_location.find_location_metadata(content), ["jpeg[0].exif.gps"])
        output = image_location.remove_jpeg_location(original)
        self._assert_valid(output, original)
        self.assertEqual(self._images(output)[1], self._images(original)[1])

    def test_primary_xmp_change_recomputes_offsets(self):
        """Zkrácení XMP hlavního obrázku posune vedlejší obrázek a index MPF se přepočítá."""
        content = fx.mpo(primary_xmp=fx.XMP_GPS_ELEMENT)
        original = content.getvalue()
        output = image_location.remove_jpeg_location(original)
        self.assertLess(len(output), len(original))
        self._assert_valid(output, original)
        self.assertEqual(self._images(output)[1], self._images(original)[1])

    def test_ultra_hdr_container_length_is_updated(self):
        """Změna délky mapy zesílení se promítne do Item:Length; hdrgm zůstane."""
        # Mapa zesílení má XMP s polohou, aby se po vyčištění zkrátila. Její délku zjistí
        # první sestavení; kódování vedlejšího obrázku nezávisí na metadatech hlavního.
        options = {"secondary_exif": fx.exif_bytes(make="GainMap"), "secondary_xmp": fx.XMP_GPS_ELEMENT}
        first = fx.mpo(primary_xmp=fx.container_xmp(0), **options).getvalue()
        content = fx.mpo(primary_xmp=fx.container_xmp(len(self._images(first)[1])), **options)
        original = content.getvalue()
        self.assertEqual(self._images(original)[1], self._images(first)[1])
        self.assertEqual(image_location.find_location_metadata(content), ["jpeg[1].exif.gps", "jpeg[1].xmp"])
        output = image_location.remove_jpeg_location(original)
        self._assert_valid(output, original, pillow_mpo=False)
        new_gain_map = self._images(output)[1]
        self.assertLess(len(new_gain_map), len(self._images(original)[1]))
        items = list(_xmp_root(_jpeg_xmp(self._images(output)[0])).iter(image_location.XMP_CONTAINER_ITEM))
        self.assertEqual(items[1].get(image_location.XMP_ITEM_LENGTH), str(len(new_gain_map)))
        self.assertEqual(_description(_jpeg_xmp(self._images(output)[0])).get(HDRGM_VERSION), "1.0")

    def test_container_mismatch_is_rejected(self):
        """Adresář Ultra HDR, který neodpovídá indexu MPF, nelze bezpečně upravit."""
        packet = fx.container_xmp(1).replace(b"</rdf:Seq>", b'<rdf:li rdf:parseType="Resource"/></rdf:Seq>')
        packet = packet.replace(
            b'<rdf:li rdf:parseType="Resource"/>',
            b'<rdf:li rdf:parseType="Resource"><Container:Item Item:Semantic="Depth" Item:Length="1"/></rdf:li>',
        )
        content = fx.mpo(primary_xmp=packet, secondary_xmp=fx.XMP_GPS_ATTRIBUTE)
        with self.assertRaises(ValueError):
            image_location.remove_jpeg_location(content.getvalue())


class PngTests(unittest.TestCase):
    """PNG: XMP v iTXt a surové profily ImageMagick v textových blocích."""

    def test_xmp_is_cleaned_and_other_text_kept(self):
        """XMP se vyčistí a zapíše zpět, ostatní textové bloky zůstanou."""
        content = fx.png(xmp_packet=fx.XMP_GPS_ELEMENT, texts=[("Comment", "keep")])
        self.assertEqual(image_location.find_location_metadata(content), ["png.xmp"])
        output = image_location.remove_png_location(content.getvalue())
        self.assertEqual(image_location.find_location_metadata(io.BytesIO(output)), [])
        with Image.open(io.BytesIO(output)) as stored:
            self.assertEqual(stored.text["Comment"], "keep")
            packet = stored.text[image_location.PNG_XMP_KEY].encode("utf-8")
        self.assertEqual(_description(packet).get(DC_FORMAT), "image/jpeg")

    def test_raw_profiles(self):
        """Surový profil EXIF s GPS se zahodí, profil XMP bez polohy zůstane."""
        clean_xmp = fx.raw_profile("xmp", fx.XMP_CLEAN)
        content = fx.png(
            exif=fx.exif_bytes(),
            texts=[
                ("Raw profile type exif", fx.raw_profile("exif", fx.exif_bytes())),
                ("Raw profile type xmp", clean_xmp),
                ("Comment", "keep"),
            ],
        )
        self.assertEqual(
            image_location.find_location_metadata(content), ["png.exif.gps", "png.text[Raw profile type exif]"]
        )
        output = image_location.remove_png_location(content.getvalue())
        self.assertEqual(image_location.find_location_metadata(io.BytesIO(output)), [])
        with Image.open(io.BytesIO(output)) as stored, Image.open(content) as original:
            self.assertNotIn("Raw profile type exif", stored.text)
            self.assertEqual(stored.text["Raw profile type xmp"], clean_xmp)
            self.assertEqual(stored.text["Comment"], "keep")
            self.assertEqual(stored.getexif()[ExifTags.Base.Make], "Cam")
            self.assertEqual(stored.tobytes(), original.tobytes())

    def test_unreadable_raw_profile_is_dropped(self):
        """Surový profil, který nelze dekódovat, se považuje za polohu."""
        content = fx.png(texts=[("Raw profile type exif", "\nexif\n   4\nzz\n")])
        self.assertEqual(image_location.find_location_metadata(content), ["png.text[Raw profile type exif]"])


class HeifTests(unittest.TestCase):
    """HEIF: XMP se kontroluje ve všech obrázcích kontejneru."""

    def test_xmp_location_is_detected(self):
        """Poloha jen v XMP se najde i bez EXIF GPS."""
        content = fx.heif(exif=fx.exif_bytes(gps=False), xmp_packet=fx.XMP_GPS_ATTRIBUTE)
        self.assertEqual(image_location.find_location_metadata(content), ["heif[0].xmp"])
        self.assertEqual(content.tell(), 0)
