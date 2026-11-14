"""Testovací fotografie s polohou v různých blocích metadat, sestavené v kódu."""

import io
import struct

import pillow_heif
from core import image_location
from PIL import ExifTags, Image, ImageCms, PngImagePlugin, TiffTags

LATITUDE = (50.0, 5.0, 0.0)
NS_EXIF = "http://ns.adobe.com/exif/1.0/"
NS_DC = "http://purl.org/dc/elements/1.1/"
NS_DJI = "http://www.dji.com/drone-dji/1.0/"
NS_HDRGM = "http://ns.adobe.com/hdr-gain-map/1.0/"
EXTENDED_GUID = b"0123456789ABCDEF0123456789ABCDEF"
EXTENDED_CHUNK_SIZE = 64


def exif_bytes(gps=True, make="Cam"):
    """Vytvoří EXIF s výrobcem a volitelně se zeměpisnou šířkou.

    :param gps: Zda přidat GPS IFD.
    :param make: Hodnota tagu Make.
    :return: EXIF se signaturou ``Exif\\0\\0``.
    """
    exif = Image.Exif()
    exif[ExifTags.Base.Make] = make
    if gps:
        exif[ExifTags.IFD.GPSInfo] = {ExifTags.GPS.GPSLatitudeRef: "N", ExifTags.GPS.GPSLatitude: LATITUDE}
    return exif.tobytes()


def exif_with_thumbnail(thumbnail: bytes, gps=True):
    """Ručně sestaví EXIF s IFD0, GPS IFD a IFD1 s vloženým náhledem JPEG.

    :param thumbnail: Bajty náhledu uloženého za IFD1.
    :param gps: Zda IFD0 odkazuje na GPS IFD.
    :return: Little-endian EXIF se signaturou ``Exif\\0\\0``.
    """

    def entry(tag, field_type, count, value):
        return struct.pack("<HHII", tag, field_type, count, value)

    ifd0_entries = 1 + int(gps)
    ifd0 = image_location.TIFF_HEADER_SIZE
    gps_ifd = ifd0 + image_location.TIFF_IFD_COUNT_SIZE + ifd0_entries * image_location.TIFF_IFD_ENTRY_SIZE + 4
    gps_size = image_location.TIFF_IFD_COUNT_SIZE + image_location.TIFF_IFD_ENTRY_SIZE + 4
    ifd1 = gps_ifd + (gps_size if gps else 0)
    thumbnail_offset = ifd1 + image_location.TIFF_IFD_COUNT_SIZE + 2 * image_location.TIFF_IFD_ENTRY_SIZE + 4
    data = b"II*\x00" + struct.pack("<I", ifd0)
    data += struct.pack("<H", ifd0_entries) + entry(ExifTags.Base.Orientation, TiffTags.SHORT, 1, 1)
    if gps:
        data += entry(ExifTags.IFD.GPSInfo, TiffTags.LONG, 1, gps_ifd)
    data += struct.pack("<I", ifd1)
    if gps:
        data += struct.pack("<H", 1) + struct.pack("<HHI", ExifTags.GPS.GPSLatitudeRef, TiffTags.ASCII, 2)
        data += b"N\x00\x00\x00" + struct.pack("<I", 0)
    data += struct.pack("<H", 2)
    data += entry(ExifTags.Base.JpegIFOffset, TiffTags.LONG, 1, thumbnail_offset)
    data += entry(ExifTags.Base.JpegIFByteCount, TiffTags.LONG, 1, len(thumbnail))
    data += struct.pack("<I", 0) + thumbnail
    return image_location.EXIF_SIGNATURE + data


def xmp(description: str, namespaces: str = "") -> bytes:
    """Zabalí popis RDF do paketu XMP s instrukcemi ``xpacket``.

    :param description: Obsah ``rdf:Description`` (atributy i potomci).
    :param namespaces: Deklarace jmenných prostorů pro ``rdf:Description``.
    :return: Paket XMP v UTF-8.
    """
    return (
        '<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>'
        '<x:xmpmeta xmlns:x="adobe:ns:meta/">'
        f'<rdf:RDF xmlns:rdf="{image_location.NS_RDF}">'
        f'<rdf:Description rdf:about="" xmlns:dc="{NS_DC}" xmlns:exif="{NS_EXIF}" {namespaces} {description}'
        "</rdf:RDF></x:xmpmeta>"
        '<?xpacket end="w"?>'
    ).encode("utf-8")


XMP_GPS_ATTRIBUTE = xmp('dc:format="image/jpeg" exif:GPSLatitude="50,5.0N"/>')
XMP_GPS_ELEMENT = xmp(
    'dc:format="image/jpeg"><exif:GPSLatitude>50,5.0N</exif:GPSLatitude>'
    "<exif:GPSAreaInformation><rdf:Seq><rdf:li>area</rdf:li></rdf:Seq></exif:GPSAreaInformation>"
    "</rdf:Description>"
)
XMP_DJI = xmp(
    'dc:format="image/jpeg" drone-dji:GpsLatitude="50.08" drone-dji:GpsLongitude="14.42"/>',
    f'xmlns:drone-dji="{NS_DJI}"',
)
XMP_LOCATION_CREATED = xmp(
    'dc:format="image/jpeg"><Iptc4xmpExt:LocationCreated rdf:parseType="Resource">'
    "<Iptc4xmpExt:City>Praha</Iptc4xmpExt:City><exif:GPSLatitude>50,5.0N</exif:GPSLatitude>"
    "</Iptc4xmpExt:LocationCreated></rdf:Description>",
    f'xmlns:Iptc4xmpExt="{image_location.NS_IPTC_EXT}"',
)
XMP_CLEAN = xmp('dc:format="image/jpeg"/>')


def container_xmp(gain_map_length: int, gps=False) -> bytes:
    """Vytvoří XMP hlavního obrázku Ultra HDR s ``Container:Directory``.

    :param gain_map_length: Hodnota ``Item:Length`` mapy zesílení.
    :param gps: Zda přidat i souřadnice.
    :return: Paket XMP.
    """
    location = ' exif:GPSLatitude="50,5.0N"' if gps else ""
    return xmp(
        f'hdrgm:Version="1.0"{location}><Container:Directory><rdf:Seq>'
        '<rdf:li rdf:parseType="Resource"><Container:Item Item:Semantic="Primary" Item:Mime="image/jpeg"/></rdf:li>'
        '<rdf:li rdf:parseType="Resource"><Container:Item Item:Semantic="GainMap" Item:Mime="image/jpeg"'
        f' Item:Length="{gain_map_length}"/></rdf:li>'
        "</rdf:Seq></Container:Directory></rdf:Description>",
        f'xmlns:hdrgm="{NS_HDRGM}" xmlns:Container="{image_location.NS_CONTAINER}" '
        f'xmlns:Item="{image_location.NS_CONTAINER_ITEM}"',
    )


def icc_profile() -> bytes:
    """Vrátí profil sRGB pro kontrolu zachování ICC.

    :return: Binární profil ICC.
    """
    return ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()


def noise_image(size=64) -> Image.Image:
    """Vytvoří obrázek se šumem, aby se změna kvality projevila v datech.

    :param size: Šířka a výška obrázku.
    :return: Obrázek RGB.
    """
    return Image.effect_noise((size, size), 40).convert("RGB")


def jpeg(exif=None, xmp_packet=None, icc=None, segments=(), image=None) -> io.BytesIO:
    """Vytvoří JPEG s volitelnými metadaty a dalšími segmenty za SOI.

    :param exif: EXIF se signaturou, nebo ``None``.
    :param xmp_packet: Paket XMP, nebo ``None``.
    :param icc: Profil ICC, nebo ``None``.
    :param segments: Další hotové segmenty vložené hned za SOI.
    :param image: Zdrojový obrázek; výchozí je šum 64×64.
    :return: Stream JPEG na začátku.
    """
    options = {"quality": 95}
    for key, value in (("exif", exif), ("xmp", xmp_packet), ("icc_profile", icc)):
        if value:
            options[key] = value
    output = io.BytesIO()
    (image or noise_image()).save(output, "JPEG", **options)
    data = output.getvalue()
    soi = image_location.JPEG_MARKER_SIZE
    return io.BytesIO(data[:soi] + b"".join(segments) + data[soi:])


def extended_xmp_segments(packet: bytes) -> list[bytes]:
    """Rozdělí paket do segmentů rozšířeného XMP podle specifikace Adobe.

    :param packet: Paket XMP uložený jako rozšíření.
    :return: Hotové segmenty APP1.
    """
    segments = []
    for offset in range(0, len(packet), EXTENDED_CHUNK_SIZE):
        payload = (
            image_location.XMP_EXTENSION_SIGNATURE
            + EXTENDED_GUID
            + image_location.XMP_EXTENSION_HEADER.pack(len(packet), offset)
            + packet[offset : offset + EXTENDED_CHUNK_SIZE]
        )
        segments.append(image_location._segment(image_location.JPEG_MARKER_APP1, payload))
    return segments


def mpo(primary_exif=None, primary_xmp=None, secondary_exif=None, secondary_xmp=None) -> io.BytesIO:
    """Vytvoří JPEG s indexem MPF a jedním vedlejším obrázkem.

    :param primary_exif: EXIF hlavního obrázku.
    :param primary_xmp: XMP hlavního obrázku.
    :param secondary_exif: EXIF vedlejšího obrázku.
    :param secondary_xmp: XMP vedlejšího obrázku.
    :return: Stream MPO na začátku.
    """
    secondary = Image.new("RGB", (16, 16), "blue")
    # Vedlejší obrázek by jinak zdědil metadata hlavního obrázku.
    secondary.encoderinfo = {"exif": secondary_exif or b"", "xmp": secondary_xmp or b""}
    options = {"save_all": True, "append_images": [secondary], "quality": 95}
    if primary_exif:
        options["exif"] = primary_exif
    if primary_xmp:
        options["xmp"] = primary_xmp
    output = io.BytesIO()
    noise_image().save(output, "MPO", **options)
    output.seek(0)
    return output


def png(exif=None, xmp_packet=None, texts=()) -> io.BytesIO:
    """Vytvoří PNG s volitelným EXIF, XMP a dalšími textovými bloky.

    :param exif: EXIF se signaturou, nebo ``None``.
    :param xmp_packet: Paket XMP uložený jako ``iTXt``.
    :param texts: Dvojice (klíč, hodnota) uložené jako komprimované ``zTXt``.
    :return: Stream PNG na začátku.
    """
    info = PngImagePlugin.PngInfo()
    if xmp_packet:
        info.add_itxt(image_location.PNG_XMP_KEY, xmp_packet.decode("utf-8"))
    for key, value in texts:
        info.add_text(key, value, zip=True)
    options = {"pnginfo": info}
    if exif:
        options["exif"] = exif
    output = io.BytesIO()
    noise_image().save(output, "PNG", **options)
    output.seek(0)
    return output


def raw_profile(profile_type: str, payload: bytes) -> str:
    """Zakóduje profil ve formátu ImageMagick ``Raw profile type``.

    :param profile_type: Název profilu (např. ``exif``).
    :param payload: Binární obsah profilu.
    :return: Text bloku PNG.
    """
    hex_data = payload.hex()
    lines = "\n".join(hex_data[index : index + 72] for index in range(0, len(hex_data), 72))
    return f"\n{profile_type}\n{len(payload):8d}\n{lines}\n"


def heif(exif=None, xmp_packet=None) -> io.BytesIO:
    """Vytvoří HEIF s volitelným EXIF a XMP.

    :param exif: EXIF se signaturou, nebo ``None``.
    :param xmp_packet: Paket XMP, nebo ``None``.
    :return: Stream HEIF na začátku.
    """
    image = Image.new("RGB", (32, 32), "red")
    if exif:
        image.info["exif"] = exif
    if xmp_packet:
        image.info["xmp"] = xmp_packet
    output = io.BytesIO()
    pillow_heif.from_pillow(image).save(output)
    output.seek(0)
    return output


def scan_data(data: bytes) -> bytes:
    """Vrátí obrazová data JPEG od první značky SOS.

    :param data: Jeden obrázek JPEG.
    :return: Bajty od SOS do konce.
    """
    _, sos = image_location._parse_jpeg_header(data)
    return data[sos:]
