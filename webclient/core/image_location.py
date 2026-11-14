"""Vyhledání a odstranění údajů o poloze v metadatech fotografií PAS.

Modul nezávisí na Djangu. Kontroluje GPS v EXIF, souřadnice v XMP (včetně rozšířeného
XMP v JPEG), textové bloky PNG s vloženým EXIF/XMP a vedlejší obrázky vícesnímkových
JPEG (MPF/MPO). EXIF upravuje na místě bez změny délky, takže offsety vnořených adresářů,
náhledu (IFD1), MakerNote i indexu MPF zůstanou platné. JPEG se nikdy znovu nekóduje.

Nezpracovává textové údaje o místě v IPTC-IIM, MakerNote, komentářích ani data za koncem
JPEG (např. video pohyblivé fotografie); ta pouze zapisuje do logu.
"""

import io
import logging
import struct
import zlib
from dataclasses import dataclass

import pillow_heif
from lxml import etree
from PIL import ExifTags, Image, PngImagePlugin, TiffImagePlugin, TiffTags

logger = logging.getLogger(__name__)

EXIF_SIGNATURE = b"Exif\x00\x00"
JPEG_SIGNATURE = b"\xff\xd8\xff"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
TIFF_SIGNATURES = (b"II*\x00", b"MM\x00*")
TIFF_LITTLE_ENDIAN = b"II"
TIFF_BIG_ENDIAN = b"MM"
TIFF_MAGIC = 42
TIFF_HEADER_SIZE = 8
TIFF_FIRST_IFD_POSITION = 4
TIFF_IFD_COUNT_SIZE = 2
TIFF_IFD_ENTRY_SIZE = 12
TIFF_OFFSET_SIZE = 4
TIFF_INLINE_VALUE_SIZE = 4
TIFF_ENTRY_VALUE_POSITION = 8
TIFF_MAX_IFDS = 64
TIFF_TYPE_SIZES = {
    TiffTags.BYTE: 1,
    TiffTags.ASCII: 1,
    TiffTags.SHORT: 2,
    TiffTags.LONG: 4,
    TiffTags.RATIONAL: 8,
    TiffTags.SIGNED_BYTE: 1,
    TiffTags.UNDEFINED: 1,
    TiffTags.SIGNED_SHORT: 2,
    TiffTags.SIGNED_LONG: 4,
    TiffTags.SIGNED_RATIONAL: 8,
    TiffTags.FLOAT: 4,
    TiffTags.DOUBLE: 8,
    TiffTags.IFD: 4,
    TiffTags.LONG8: 8,
}

JPEG_MARKER_PREFIX = 0xFF
JPEG_MARKER_SOI = 0xD8
JPEG_MARKER_EOI = 0xD9
JPEG_MARKER_SOS = 0xDA
JPEG_MARKER_APP1 = 0xE1
JPEG_MARKER_APP2 = 0xE2
JPEG_MARKER_TEM = 0x01
JPEG_MARKER_STUFFED_BYTE = 0x00
JPEG_MARKER_RST_FIRST = 0xD0
JPEG_MARKER_RST_LAST = 0xD7
JPEG_MARKER_SIZE = 2
JPEG_SEGMENT_LENGTH_SIZE = 2
JPEG_MAX_SEGMENT_LENGTH = 0xFFFF

XMP_JPEG_SIGNATURE = b"http://ns.adobe.com/xap/1.0/\x00"
XMP_EXTENSION_SIGNATURE = b"http://ns.adobe.com/xmp/extension/\x00"
XMP_EXTENSION_GUID_SIZE = 32
XMP_EXTENSION_HEADER = struct.Struct(">II")

MPF_SIGNATURE = b"MPF\x00"
MPF_TAG_MP_ENTRY = 0xB002
MPF_ENTRY_FORMAT = "IIIHH"
MPF_ENTRY_SIZE = struct.calcsize("<" + MPF_ENTRY_FORMAT)

PNG_CHUNK_HEADER = struct.Struct(">I4s")
PNG_CHUNK_CRC_SIZE = 4
PNG_CHUNK_EXIF = b"eXIf"
PNG_CHUNK_TEXT = b"tEXt"
PNG_CHUNK_ZTEXT = b"zTXt"
PNG_CHUNK_ITEXT = b"iTXt"
PNG_CHUNK_END = b"IEND"
PNG_TEXT_ENCODING = "latin-1"
PNG_XMP_KEY = "XML:com.adobe.xmp"
PNG_RAW_PROFILE_PREFIX = "Raw profile type "
PNG_MAX_TEXT_SIZE = 64 * 1024 * 1024

NS_RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
NS_IPTC_EXT = "http://iptc.org/std/Iptc4xmpExt/2008-02-29/"
NS_XMP_NOTE = "http://ns.adobe.com/xmp/note/"
NS_CONTAINER = "http://ns.google.com/photos/1.0/container/"
NS_CONTAINER_ITEM = "http://ns.google.com/photos/1.0/container/item/"
XMP_GPS_PREFIX = "gps"
XMP_LOCATION_PROPERTIES = frozenset({(NS_IPTC_EXT, "LocationCreated"), (NS_IPTC_EXT, "LocationShown")})
XMP_HAS_EXTENDED = etree.QName(NS_XMP_NOTE, "HasExtendedXMP").text
XMP_CONTAINER_ITEM = etree.QName(NS_CONTAINER, "Item").text
XMP_ITEM_LENGTH = etree.QName(NS_CONTAINER_ITEM, "Length").text
XMP_STRIP_CHARACTERS = b"\x00 \t\r\n"

GPS_IFD_TAG = ExifTags.IFD.GPSInfo
XMP_TIFF_TAG = ExifTags.Base.XMLPacket


# --- EXIF -----------------------------------------------------------------------------


def _tiff_layout(data) -> tuple[int, str]:
    """Najde začátek struktury TIFF v EXIF a její pořadí bajtů.

    :param data: EXIF s volitelnou signaturou ``Exif\\0\\0``.
    :return: Dvojice (pozice hlavičky TIFF, prefix ``struct`` pro pořadí bajtů).
    :raises ValueError: Pokud hlavička TIFF chybí nebo je neplatná.
    """
    base = len(EXIF_SIGNATURE) if bytes(data[: len(EXIF_SIGNATURE)]) == EXIF_SIGNATURE else 0
    order = bytes(data[base : base + len(TIFF_LITTLE_ENDIAN)])
    if order == TIFF_LITTLE_ENDIAN:
        endian = "<"
    elif order == TIFF_BIG_ENDIAN:
        endian = ">"
    else:
        raise ValueError("Invalid EXIF byte order")
    if len(data) < base + TIFF_HEADER_SIZE or struct.unpack_from(endian + "H", data, base + 2)[0] != TIFF_MAGIC:
        raise ValueError("Invalid EXIF header")
    return base, endian


def _tiff_ifd_chain(data, base: int, endian: str) -> list[tuple[int, int]]:
    """Vrátí hlavní řetězec adresářů EXIF (IFD0, IFD1, ...).

    Neplatný ukazatel na další adresář ukončí řetězec stejně jako v Pillow; neplatný
    první adresář je chyba.

    :param data: EXIF data.
    :param base: Pozice hlavičky TIFF v ``data``.
    :param endian: Prefix ``struct`` pro pořadí bajtů.
    :return: Seznam dvojic (offset adresáře vůči hlavičce, počet položek).
    :raises ValueError: Pokud první adresář leží mimo data nebo řetězec obsahuje cyklus.
    """
    chain = []
    seen = set()
    offset = struct.unpack_from(endian + "I", data, base + TIFF_FIRST_IFD_POSITION)[0]
    while offset:
        start = base + offset
        if start + TIFF_IFD_COUNT_SIZE > len(data):
            if not chain:
                raise ValueError("EXIF IFD0 out of bounds")
            break
        count = struct.unpack_from(endian + "H", data, start)[0]
        end = start + TIFF_IFD_COUNT_SIZE + count * TIFF_IFD_ENTRY_SIZE + TIFF_OFFSET_SIZE
        if end > len(data):
            if not chain:
                raise ValueError("EXIF IFD0 out of bounds")
            break
        if offset in seen or len(chain) >= TIFF_MAX_IFDS:
            raise ValueError("Cyclic EXIF IFD chain")
        seen.add(offset)
        chain.append((offset, count))
        offset = struct.unpack_from(endian + "I", data, end - TIFF_OFFSET_SIZE)[0]
    return chain


def _gps_entries(data, base: int, endian: str) -> list[tuple[int, int]]:
    """Najde položky odkazující na GPS IFD ve všech hlavních adresářích.

    :param data: EXIF data.
    :param base: Pozice hlavičky TIFF.
    :param endian: Prefix ``struct`` pro pořadí bajtů.
    :return: Seznam dvojic (absolutní pozice položky, offset GPS IFD).
    """
    entries = []
    for offset, count in _tiff_ifd_chain(data, base, endian):
        first = base + offset + TIFF_IFD_COUNT_SIZE
        for index in range(count):
            position = first + index * TIFF_IFD_ENTRY_SIZE
            if struct.unpack_from(endian + "H", data, position)[0] == GPS_IFD_TAG:
                value = struct.unpack_from(endian + "I", data, position + TIFF_ENTRY_VALUE_POSITION)[0]
                entries.append((position, value))
    return entries


def exif_has_gps(exif: bytes) -> bool:
    """Zjistí, zda EXIF obsahuje odkaz na GPS IFD.

    :param exif: EXIF s volitelnou signaturou ``Exif\\0\\0``.
    :return: ``True``, pokud některý hlavní adresář odkazuje na GPS IFD.
    :raises ValueError: Pokud EXIF nelze rozebrat.
    """
    base, endian = _tiff_layout(exif)
    return bool(_gps_entries(exif, base, endian))


def _zero_gps_ifd(data: bytearray, base: int, endian: str, offset: int) -> None:
    """Přepíše nulami GPS IFD a jeho hodnoty uložené mimo položky.

    :param data: Upravovaná EXIF data.
    :param base: Pozice hlavičky TIFF.
    :param endian: Prefix ``struct`` pro pořadí bajtů.
    :param offset: Offset GPS IFD vůči hlavičce; neplatný offset se přeskočí.
    """
    start = base + offset
    if not offset or start + TIFF_IFD_COUNT_SIZE > len(data):
        return
    count = struct.unpack_from(endian + "H", data, start)[0]
    end = min(len(data), start + TIFF_IFD_COUNT_SIZE + count * TIFF_IFD_ENTRY_SIZE + TIFF_OFFSET_SIZE)
    for index in range(count):
        position = start + TIFF_IFD_COUNT_SIZE + index * TIFF_IFD_ENTRY_SIZE
        if position + TIFF_IFD_ENTRY_SIZE > len(data):
            break
        _, field_type, field_count = struct.unpack_from(endian + "HHI", data, position)
        size = TIFF_TYPE_SIZES.get(field_type, 0) * field_count
        if size > TIFF_INLINE_VALUE_SIZE:
            value_start = base + struct.unpack_from(endian + "I", data, position + TIFF_ENTRY_VALUE_POSITION)[0]
            if value_start + size <= len(data):
                data[value_start : value_start + size] = bytes(size)
    data[start:end] = bytes(end - start)


def remove_exif_gps(exif: bytes) -> bytes:
    """Odstraní GPS z EXIF na místě, bez změny délky a ostatních offsetů.

    Odkaz na GPS IFD se vyjme z adresáře (položky se posunou a uvolněné místo vynuluje)
    a samotný GPS IFD i jeho hodnoty se přepíší nulami.

    :param exif: EXIF s volitelnou signaturou ``Exif\\0\\0``.
    :return: EXIF stejné délky bez GPS; bez GPS vrací vstup beze změny.
    :raises ValueError: Pokud EXIF nelze rozebrat.
    """
    base, endian = _tiff_layout(exif)
    entries = _gps_entries(exif, base, endian)
    if not entries:
        return exif
    data = bytearray(exif)
    for offset, count in _tiff_ifd_chain(data, base, endian):
        first = base + offset + TIFF_IFD_COUNT_SIZE
        kept = []
        for index in range(count):
            entry = bytes(data[first + index * TIFF_IFD_ENTRY_SIZE : first + (index + 1) * TIFF_IFD_ENTRY_SIZE])
            if struct.unpack_from(endian + "H", entry)[0] != GPS_IFD_TAG:
                kept.append(entry)
        removed = count - len(kept)
        if not removed:
            continue
        next_position = first + count * TIFF_IFD_ENTRY_SIZE
        next_pointer = bytes(data[next_position : next_position + TIFF_OFFSET_SIZE])
        data[base + offset : next_position + TIFF_OFFSET_SIZE] = (
            struct.pack(endian + "H", len(kept)) + b"".join(kept) + next_pointer + bytes(removed * TIFF_IFD_ENTRY_SIZE)
        )
    for _, gps_offset in entries:
        _zero_gps_ifd(data, base, endian, gps_offset)
    return bytes(data)


# --- XMP ------------------------------------------------------------------------------


def _parse_xmp(xmp: bytes):
    """Bezpečně rozebere paket XMP bez DTD, entit a síťového přístupu.

    :param xmp: Paket XMP včetně případných instrukcí ``<?xpacket?>``.
    :return: Kořenový element dokumentu.
    :raises etree.XMLSyntaxError: Pokud paket není platné XML.
    :raises ValueError: Pokud paket obsahuje deklaraci DOCTYPE.
    """
    if isinstance(xmp, str):
        xmp = xmp.encode("utf-8")
    parser = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False, huge_tree=False)
    root = etree.fromstring(xmp.strip(XMP_STRIP_CHARACTERS), parser)
    # XMP nesmí obsahovat DTD; paket s DOCTYPE se považuje za nečitelný.
    if root.getroottree().docinfo.doctype:
        raise ValueError("XMP packet must not contain a DOCTYPE")
    return root


def _is_location_name(name: str) -> bool:
    """Rozhodne, zda kvalifikovaný název vlastnosti XMP nese polohu.

    :param name: Název elementu nebo atributu ve tvaru ``{namespace}local``.
    :return: ``True`` pro vlastnosti začínající ``GPS`` v libovolném jmenném prostoru
        a pro ``Iptc4xmpExt:LocationCreated``/``LocationShown``.
    """
    qname = etree.QName(name)
    return qname.localname.lower().startswith(XMP_GPS_PREFIX) or (
        (qname.namespace, qname.localname) in XMP_LOCATION_PROPERTIES
    )


def _remove_element(element) -> None:
    """Odstraní element a zachová text, který za ním následoval.

    :param element: Element XMP k odstranění.
    """
    parent = element.getparent()
    if element.tail:
        previous = element.getprevious()
        if previous is not None:
            previous.tail = (previous.tail or "") + element.tail
        else:
            parent.text = (parent.text or "") + element.tail
    parent.remove(element)


def _remove_property(root, name: str) -> bool:
    """Odstraní všechny výskyty vlastnosti ve tvaru atributu i elementu.

    :param root: Kořen dokumentu XMP.
    :param name: Kvalifikovaný název vlastnosti.
    :return: ``True``, pokud se něco odstranilo.
    """
    changed = False
    for element in list(root.iter(name)):
        _remove_element(element)
        changed = True
    for element in root.iter():
        if isinstance(element.tag, str) and name in element.attrib:
            del element.attrib[name]
            changed = True
    return changed


def _strip_location(root) -> bool:
    """Odstraní z dokumentu XMP všechny vlastnosti nesoucí polohu.

    :param root: Kořen dokumentu XMP.
    :return: ``True``, pokud se něco odstranilo.
    """
    changed = False
    for element in list(root.iter()):
        if not isinstance(element.tag, str):
            continue
        for name in [name for name in element.attrib if _is_location_name(name)]:
            del element.attrib[name]
            changed = True
    targets = [
        element
        for element in root.iter()
        if isinstance(element.tag, str) and _is_location_name(element.tag) and element.getparent() is not None
    ]
    # Potomci odstraňovaného elementu (např. položky struktury LocationCreated) zmizí s ním.
    for element in targets:
        if not any(isinstance(parent.tag, str) and _is_location_name(parent.tag) for parent in element.iterancestors()):
            _remove_element(element)
            changed = True
    return changed


def has_xmp_location(xmp: bytes) -> bool:
    """Zjistí, zda paket XMP obsahuje polohu.

    :param xmp: Paket XMP.
    :return: ``True`` pro polohu i pro paket, který nelze rozebrat.
    """
    try:
        root = _parse_xmp(xmp)
    except (etree.XMLSyntaxError, ValueError):
        return True
    return any(
        isinstance(element.tag, str)
        and (_is_location_name(element.tag) or any(_is_location_name(name) for name in element.attrib))
        for element in root.iter()
    )


def _update_container_lengths(root, lengths: list[int]) -> bool:
    """Aktualizuje délky vedlejších položek ``Container:Directory`` (Ultra HDR).

    :param root: Kořen dokumentu XMP hlavního obrázku.
    :param lengths: Nové délky vedlejších obrázků v pořadí souboru.
    :return: ``True``, pokud dokument adresář obsahuje a délky se nastavily.
    :raises ValueError: Pokud počet položek adresáře neodpovídá počtu obrázků.
    """
    items = list(root.iter(XMP_CONTAINER_ITEM))
    if not items:
        return False
    secondary = items[1:]
    if len(secondary) != len(lengths):
        raise ValueError("Container directory does not match MPF images")
    for item, length in zip(secondary, lengths):
        element = item.find(XMP_ITEM_LENGTH)
        if element is not None:
            element.text = str(length)
        else:
            item.set(XMP_ITEM_LENGTH, str(length))
    return True


def rewrite_xmp(xmp: bytes, container_lengths: list[int] | None = None, drop_extended: bool = False):
    """Odstraní polohu z paketu XMP a volitelně upraví odkazy na další data.

    Ostatní vlastnosti (např. ``hdrgm:*`` a ``Container:Directory``) zůstanou zachovány.

    :param xmp: Paket XMP.
    :param container_lengths: Nové délky vedlejších obrázků pro ``Container:Directory``.
    :param drop_extended: Zda odstranit ``xmpNote:HasExtendedXMP`` po zahození rozšířeného XMP.
    :return: Upravený paket, původní paket beze změny, nebo ``None``, pokud ho nelze
        rozebrat a je nutné ho celý zahodit.
    :raises ValueError: Pokud ``Container:Directory`` neodpovídá počtu obrázků.
    """
    try:
        root = _parse_xmp(xmp)
    except (etree.XMLSyntaxError, ValueError):
        return None
    changed = _strip_location(root)
    if drop_extended:
        changed = _remove_property(root, XMP_HAS_EXTENDED) or changed
    if container_lengths is not None:
        changed = _update_container_lengths(root, container_lengths) or changed
    if not changed:
        return xmp
    return etree.tostring(root.getroottree(), encoding="UTF-8")


def strip_xmp_location(xmp: bytes):
    """Odstraní z paketu XMP vlastnosti nesoucí polohu.

    :param xmp: Paket XMP.
    :return: Paket bez polohy, nebo ``None``, pokud ho nelze rozebrat.
    """
    return rewrite_xmp(xmp)


# --- JPEG -----------------------------------------------------------------------------


@dataclass
class _JpegSegment:
    """Segment hlavičky JPEG před prvním skenem."""

    marker: int
    start: int
    raw: bytes
    payload: bytes


def _parse_jpeg_header(data: bytes) -> tuple[list[_JpegSegment], int]:
    """Rozdělí hlavičku JPEG na segmenty až po první SOS.

    :param data: Jeden obrázek JPEG.
    :return: Seznam segmentů a pozice značky SOS.
    :raises ValueError: Pokud hlavička není úplná nebo obsahuje neplatnou značku.
    """
    if not data.startswith(JPEG_SIGNATURE):
        raise ValueError("Missing JPEG signature")
    segments = []
    offset = JPEG_MARKER_SIZE
    while offset < len(data):
        start = offset
        if data[offset] != JPEG_MARKER_PREFIX:
            raise ValueError("Invalid JPEG marker")
        while offset < len(data) and data[offset] == JPEG_MARKER_PREFIX:
            offset += 1
        if offset >= len(data):
            break
        marker = data[offset]
        offset += 1
        if marker == JPEG_MARKER_SOS:
            return segments, start
        if marker in (JPEG_MARKER_STUFFED_BYTE, JPEG_MARKER_SOI, JPEG_MARKER_EOI):
            raise ValueError("Unexpected JPEG marker")
        if marker == JPEG_MARKER_TEM or JPEG_MARKER_RST_FIRST <= marker <= JPEG_MARKER_RST_LAST:
            segments.append(_JpegSegment(marker, start, data[start:offset], b""))
            continue
        length = int.from_bytes(data[offset : offset + JPEG_SEGMENT_LENGTH_SIZE], "big")
        end = offset + length
        if length < JPEG_SEGMENT_LENGTH_SIZE or end > len(data):
            raise ValueError("Truncated JPEG segment")
        segments.append(_JpegSegment(marker, start, data[start:end], data[offset + JPEG_SEGMENT_LENGTH_SIZE : end]))
        offset = end
    raise ValueError("Missing JPEG scan")


def _jpeg_end(data: bytes, offset: int) -> int:
    """Najde konec obrázku JPEG (za značkou EOI) průchodem komprimovaných dat.

    :param data: Obsah začínající obrázkem JPEG.
    :param offset: Pozice první značky SOS.
    :return: Pozice za EOI; délka dat, pokud EOI chybí.
    """
    while offset + JPEG_MARKER_SIZE <= len(data):
        marker = data[offset + 1]
        if marker == JPEG_MARKER_EOI:
            return offset + JPEG_MARKER_SIZE
        length = int.from_bytes(data[offset + JPEG_MARKER_SIZE : offset + JPEG_MARKER_SIZE + 2], "big")
        offset += JPEG_MARKER_SIZE + length
        while True:
            index = data.find(bytes([JPEG_MARKER_PREFIX]), offset)
            if index < 0 or index + 1 >= len(data):
                return len(data)
            following = data[index + 1]
            if following == JPEG_MARKER_PREFIX:
                offset = index + 1
            elif following == JPEG_MARKER_STUFFED_BYTE or JPEG_MARKER_RST_FIRST <= following <= JPEG_MARKER_RST_LAST:
                offset = index + JPEG_MARKER_SIZE
            else:
                offset = index
                break
    return len(data)


def _segment(marker: int, payload: bytes) -> bytes:
    """Sestaví segment JPEG se značkou a délkou.

    :param marker: Druhý bajt značky.
    :param payload: Obsah segmentu bez délky.
    :return: Celý segment.
    :raises ValueError: Pokud obsah překročí kapacitu segmentu.
    """
    length = len(payload) + JPEG_SEGMENT_LENGTH_SIZE
    if length > JPEG_MAX_SEGMENT_LENGTH:
        raise ValueError("JPEG segment too large")
    return bytes([JPEG_MARKER_PREFIX, marker]) + length.to_bytes(JPEG_SEGMENT_LENGTH_SIZE, "big") + payload


def _app1(segment: _JpegSegment, signature: bytes) -> bool:
    """Zjistí, zda je segment APP1 s danou signaturou.

    :param segment: Segment hlavičky JPEG.
    :param signature: Očekávaný začátek obsahu.
    :return: ``True`` při shodě.
    """
    return segment.marker == JPEG_MARKER_APP1 and segment.payload.startswith(signature)


def _extended_xmp(segments: list[_JpegSegment]) -> list[bytes]:
    """Složí rozšířené XMP z jednotlivých segmentů podle GUID a offsetu.

    :param segments: Segmenty hlavičky JPEG.
    :return: Složené pakety rozšířeného XMP.
    """
    chunks: dict[bytes, list[tuple[int, bytes]]] = {}
    header_size = len(XMP_EXTENSION_SIGNATURE) + XMP_EXTENSION_GUID_SIZE + XMP_EXTENSION_HEADER.size
    for segment in segments:
        if not _app1(segment, XMP_EXTENSION_SIGNATURE) or len(segment.payload) < header_size:
            continue
        guid_start = len(XMP_EXTENSION_SIGNATURE)
        guid = segment.payload[guid_start : guid_start + XMP_EXTENSION_GUID_SIZE]
        _, chunk_offset = XMP_EXTENSION_HEADER.unpack_from(segment.payload, guid_start + XMP_EXTENSION_GUID_SIZE)
        chunks.setdefault(guid, []).append((chunk_offset, segment.payload[header_size:]))
    return [b"".join(chunk for _, chunk in sorted(parts)) for parts in chunks.values()]


def _jpeg_image_blocks(data: bytes, ident: str) -> list[str]:
    """Najde bloky s polohou v jednom obrázku JPEG.

    :param data: Jeden obrázek JPEG.
    :param ident: Označení obrázku pro výsledné identifikátory.
    :return: Identifikátory bloků s polohou.
    :raises ValueError: Pokud hlavičku nebo EXIF nelze rozebrat nebo obsahuje více EXIF.
    """
    segments, _ = _parse_jpeg_header(data)
    blocks = []
    exif = [segment for segment in segments if _app1(segment, EXIF_SIGNATURE)]
    if len(exif) > 1:
        raise ValueError("Multiple EXIF segments")
    if exif and exif_has_gps(exif[0].payload):
        blocks.append(f"{ident}.exif.gps")
    for segment in segments:
        if _app1(segment, XMP_JPEG_SIGNATURE) and has_xmp_location(segment.payload[len(XMP_JPEG_SIGNATURE) :]):
            blocks.append(f"{ident}.xmp")
    if any(has_xmp_location(packet) for packet in _extended_xmp(segments)):
        blocks.append(f"{ident}.xmp_extended")
    return blocks


def _clean_jpeg_image(data: bytes, container_lengths: list[int] | None = None) -> bytes:
    """Odstraní polohu z jednoho obrázku JPEG bez dekódování obrazových dat.

    EXIF se upraví na místě, XMP se nahradí vyčištěným paketem nebo zahodí a rozšířené
    XMP s polohou se zahodí celé. Ostatní segmenty a vše od SOS zůstane beze změny.

    :param data: Jeden obrázek JPEG.
    :param container_lengths: Nové délky vedlejších obrázků pro ``Container:Directory``.
    :return: Obrázek bez polohy.
    :raises ValueError: Pokud hlavičku nelze rozebrat nebo XMP nelze uložit do segmentu.
    """
    segments, sos = _parse_jpeg_header(data)
    drop_extended = any(has_xmp_location(packet) for packet in _extended_xmp(segments))
    output = [data[:JPEG_MARKER_SIZE]]
    for segment in segments:
        if _app1(segment, EXIF_SIGNATURE):
            output.append(_segment(JPEG_MARKER_APP1, remove_exif_gps(segment.payload)))
        elif _app1(segment, XMP_JPEG_SIGNATURE):
            xmp = rewrite_xmp(segment.payload[len(XMP_JPEG_SIGNATURE) :], container_lengths, drop_extended)
            if xmp is not None:
                output.append(_segment(JPEG_MARKER_APP1, XMP_JPEG_SIGNATURE + xmp))
        elif _app1(segment, XMP_EXTENSION_SIGNATURE) and drop_extended:
            continue
        else:
            output.append(segment.raw)
    output.append(data[sos:])
    return b"".join(output)


@dataclass
class _MpfLayout:
    """Rozložení vícesnímkového JPEG podle indexu MPF."""

    header_position: int
    endian: str
    entries: bytes
    records: list[tuple]
    images: list[tuple[int, int]]


def _mpf_segment(data: bytes) -> tuple[_JpegSegment, int] | None:
    """Najde segment APP2 s indexem MPF v hlavním obrázku.

    :param data: Soubor JPEG začínající hlavním obrázkem.
    :return: Segment a absolutní pozice hlavičky TIFF indexu, nebo ``None``, pokud chybí.
    :raises ValueError: Pokud hlavičku JPEG nelze rozebrat.
    """
    segments, _ = _parse_jpeg_header(data)
    for segment in segments:
        if segment.marker == JPEG_MARKER_APP2 and segment.payload.startswith(MPF_SIGNATURE):
            return segment, segment.start + JPEG_MARKER_SIZE + JPEG_SEGMENT_LENGTH_SIZE + len(MPF_SIGNATURE)
    return None


def _mpf_layout(data: bytes) -> _MpfLayout | None:
    """Rozebere index MPF hlavního obrázku a vrátí polohu všech obrázků.

    :param data: Celý soubor JPEG.
    :return: Rozložení obrázků, nebo ``None``, pokud soubor index MPF nemá.
    :raises ValueError: Pokud index odkazuje mimo soubor nebo se obrázky překrývají.
    """
    found = _mpf_segment(data)
    if found is None:
        return None
    segment, header_position = found
    tiff = segment.payload[len(MPF_SIGNATURE) :]
    _, endian = _tiff_layout(tiff)
    directory = TiffImagePlugin.ImageFileDirectory_v2(tiff[:TIFF_HEADER_SIZE])
    stream = io.BytesIO(tiff)
    stream.seek(directory.next)
    directory.load(stream)
    entries = directory.get(MPF_TAG_MP_ENTRY)
    if not isinstance(entries, bytes) or not entries or len(entries) % MPF_ENTRY_SIZE:
        raise ValueError("Invalid MPF entries")
    records = [
        struct.unpack_from(endian + MPF_ENTRY_FORMAT, entries, index * MPF_ENTRY_SIZE)
        for index in range(len(entries) // MPF_ENTRY_SIZE)
    ]
    images = []
    for index, (_, size, offset, _, _) in enumerate(records):
        start = 0 if index == 0 else header_position + offset
        if size <= 0 or start + size > len(data):
            raise ValueError("MPF image out of bounds")
        images.append((start, size))
    ordered = sorted(images)
    if any(previous[0] + previous[1] > current[0] for previous, current in zip(ordered, ordered[1:])):
        raise ValueError("Overlapping MPF images")
    return _MpfLayout(header_position, endian, entries, records, images)


def _jpeg_trailer(data: bytes, layout: _MpfLayout | None) -> int:
    """Spočítá délku nenulových dat za posledním obrázkem JPEG.

    :param data: Celý soubor JPEG.
    :param layout: Rozložení MPF, nebo ``None`` pro jednoduchý JPEG.
    :return: Počet bajtů za koncem posledního obrázku, pokud nejsou jen výplní.
    """
    if layout is None:
        _, sos = _parse_jpeg_header(data)
        end = _jpeg_end(data, sos)
    else:
        end = max(start + size for start, size in layout.images)
    trailer = data[end:]
    return len(trailer) if trailer.strip(b"\x00") else 0


def _jpeg_blocks(data: bytes) -> list[str]:
    """Najde bloky s polohou ve všech obrázcích souboru JPEG.

    :param data: Celý soubor JPEG.
    :return: Identifikátory bloků s polohou.
    """
    layout = _mpf_layout(data)
    images = layout.images if layout else [(0, len(data))]
    blocks = []
    for index, (start, size) in enumerate(images):
        blocks.extend(_jpeg_image_blocks(data[start : start + size], f"jpeg[{index}]"))
    trailer = _jpeg_trailer(data, layout)
    if trailer:
        logger.warning("core.image_location.jpeg_trailer", extra={"block": "jpeg.trailer", "size": trailer})
    return blocks


def remove_jpeg_location(data: bytes) -> bytes:
    """Odstraní polohu ze všech obrázků JPEG včetně vedlejších obrázků MPF.

    Obrázky bez polohy zůstanou bajtově shodné. Po změně délky se přepočítá index MPF
    a délky v ``Container:Directory`` hlavního obrázku (Ultra HDR).

    :param data: Celý soubor JPEG.
    :return: Soubor bez polohy.
    :raises ValueError: Pokud soubor nelze rozebrat nebo index MPF nelze aktualizovat.
    """
    layout = _mpf_layout(data)
    if layout is None:
        return _clean_jpeg_image(data)
    images = [data[start : start + size] for start, size in layout.images]
    cleaned = [images[0]]
    for index, image in enumerate(images[1:], start=1):
        cleaned.append(_clean_jpeg_image(image) if _jpeg_image_blocks(image, f"jpeg[{index}]") else image)
    secondary_changed = any(len(new) != len(old) for new, old in zip(cleaned[1:], images[1:]))
    container_lengths = [len(image) for image in cleaned[1:]] if secondary_changed else None
    if container_lengths is not None or _jpeg_image_blocks(images[0], "jpeg[0]"):
        cleaned[0] = _clean_jpeg_image(images[0], container_lengths)
    _, header_position = _mpf_segment(cleaned[0])
    output = bytearray()
    new_starts = [0] * len(images)
    previous_end = 0
    for index in sorted(range(len(images)), key=lambda item: layout.images[item][0]):
        start, size = layout.images[index]
        output.extend(data[previous_end:start])
        new_starts[index] = len(output)
        output.extend(cleaned[index])
        previous_end = start + size
    output.extend(data[previous_end:])
    entries = b"".join(
        struct.pack(
            layout.endian + MPF_ENTRY_FORMAT,
            attribute,
            len(cleaned[index]),
            0 if index == 0 else new_starts[index] - header_position,
            first_dependent,
            second_dependent,
        )
        for index, (attribute, _, _, first_dependent, second_dependent) in enumerate(layout.records)
    )
    primary = bytes(output[: len(cleaned[0])])
    if primary.count(layout.entries) != 1:
        raise ValueError("Cannot locate MPF entries")
    position = primary.index(layout.entries)
    output[position : position + len(entries)] = entries
    return bytes(output)


# --- PNG ------------------------------------------------------------------------------


@dataclass
class _PngText:
    """Textový blok PNG po dekódování."""

    chunk: bytes
    key: str
    value: str
    language: str = ""
    translated_key: str = ""
    compressed: bool = False


def _inflate(data: bytes) -> bytes:
    """Rozbalí komprimovaný textový blok PNG s omezením velikosti.

    :param data: Data komprimovaná metodou zlib.
    :return: Rozbalená data.
    :raises ValueError: Pokud rozbalená data překročí ``PNG_MAX_TEXT_SIZE``.
    """
    decompressor = zlib.decompressobj()
    result = decompressor.decompress(data, PNG_MAX_TEXT_SIZE)
    if decompressor.unconsumed_tail:
        raise ValueError("PNG text chunk too large")
    return result


def _png_chunks(data: bytes) -> tuple[bytes | None, list[_PngText]]:
    """Přečte EXIF a textové bloky PNG bez dekódování obrazových dat.

    :param data: Celý soubor PNG.
    :return: Obsah bloku ``eXIf`` (nebo ``None``) a dekódované textové bloky.
    :raises ValueError: Pokud je struktura bloků poškozená.
    """
    offset = len(PNG_SIGNATURE)
    exif = None
    texts = []
    while offset + PNG_CHUNK_HEADER.size <= len(data):
        length, chunk = PNG_CHUNK_HEADER.unpack_from(data, offset)
        start = offset + PNG_CHUNK_HEADER.size
        end = start + length
        if end + PNG_CHUNK_CRC_SIZE > len(data):
            raise ValueError("Truncated PNG chunk")
        body = data[start:end]
        if chunk == PNG_CHUNK_EXIF:
            exif = body
        elif chunk == PNG_CHUNK_TEXT:
            key, _, value = body.partition(b"\x00")
            texts.append(_PngText(chunk, key.decode(PNG_TEXT_ENCODING), value.decode(PNG_TEXT_ENCODING)))
        elif chunk == PNG_CHUNK_ZTEXT:
            key, _, value = body.partition(b"\x00")
            text = _inflate(value[1:]).decode(PNG_TEXT_ENCODING)
            texts.append(_PngText(chunk, key.decode(PNG_TEXT_ENCODING), text, compressed=True))
        elif chunk == PNG_CHUNK_ITEXT:
            key, _, rest = body.partition(b"\x00")
            compressed = bool(rest[0])
            language, _, rest = rest[2:].partition(b"\x00")
            translated, _, value = rest.partition(b"\x00")
            value = _inflate(value) if compressed else value
            texts.append(
                _PngText(
                    chunk,
                    key.decode(PNG_TEXT_ENCODING),
                    value.decode("utf-8"),
                    language.decode(PNG_TEXT_ENCODING),
                    translated.decode("utf-8"),
                    compressed,
                )
            )
        elif chunk == PNG_CHUNK_END:
            break
        offset = end + PNG_CHUNK_CRC_SIZE
    return exif, texts


def _raw_profile(text: _PngText) -> bytes | None:
    """Dekóduje hexadecimální profil ImageMagick (``Raw profile type ...``).

    :param text: Textový blok PNG.
    :return: Binární obsah profilu, nebo ``None``, pokud blok není surový profil.
    :raises ValueError: Pokud profil nelze dekódovat.
    """
    if not text.key.startswith(PNG_RAW_PROFILE_PREFIX):
        return None
    lines = text.value.strip().split("\n")
    return bytes.fromhex("".join(line.strip() for line in lines[2:]))


def _raw_profile_has_location(profile: bytes) -> bool:
    """Zjistí, zda surový profil PNG obsahuje polohu.

    :param profile: Dekódovaný obsah profilu (EXIF, APP1 nebo XMP).
    :return: ``True`` pro polohu i pro profil, který nelze rozebrat.
    """
    try:
        if profile.startswith(XMP_JPEG_SIGNATURE):
            return has_xmp_location(profile[len(XMP_JPEG_SIGNATURE) :])
        if profile.startswith(EXIF_SIGNATURE) or profile[:4] in TIFF_SIGNATURES:
            return exif_has_gps(profile)
        return has_xmp_location(profile)
    except ValueError:
        return True


def _png_text_has_location(text: _PngText) -> bool:
    """Zjistí, zda textový blok PNG nese polohu.

    :param text: Textový blok PNG.
    :return: ``True`` pro XMP nebo surový profil s polohou.
    """
    if text.key == PNG_XMP_KEY:
        return has_xmp_location(text.value.encode("utf-8"))
    try:
        profile = _raw_profile(text)
    except ValueError:
        return True
    return profile is not None and _raw_profile_has_location(profile)


def _png_blocks(data: bytes) -> list[str]:
    """Najde bloky s polohou v PNG.

    :param data: Celý soubor PNG.
    :return: Identifikátory bloků s polohou.
    :raises ValueError: Pokud strukturu PNG nebo EXIF nelze rozebrat.
    """
    exif, texts = _png_chunks(data)
    blocks = ["png.exif.gps"] if exif and exif_has_gps(exif) else []
    for text in texts:
        if _png_text_has_location(text):
            blocks.append("png.xmp" if text.key == PNG_XMP_KEY else f"png.text[{text.key}]")
    return blocks


def remove_png_location(data: bytes) -> bytes:
    """Odstraní polohu z PNG a zachová ostatní textové bloky.

    Obrazová data se znovu uloží bezeztrátově. XMP se zapíše vyčištěné, surové profily
    s polohou se zahodí a ostatní textové bloky se přenesou beze změny.

    :param data: Celý soubor PNG.
    :return: PNG bez polohy.
    :raises ValueError: Pokud PNG nelze rozebrat.
    """
    exif, texts = _png_chunks(data)
    info = PngImagePlugin.PngInfo()
    for text in texts:
        value = text.value
        if text.key == PNG_XMP_KEY:
            cleaned = strip_xmp_location(value.encode("utf-8"))
            if cleaned is None:
                continue
            value = cleaned.decode("utf-8")
        elif _png_text_has_location(text):
            continue
        if text.chunk == PNG_CHUNK_ITEXT:
            info.add_itxt(text.key, value, text.language, text.translated_key, text.compressed)
        else:
            info.add_text(text.key, value, zip=text.compressed)
    with Image.open(io.BytesIO(data)) as image:
        options = {"pnginfo": info}
        if exif:
            options["exif"] = remove_exif_gps(exif)
        if "dpi" in image.info:
            options["dpi"] = image.info["dpi"]
        output = io.BytesIO()
        image.save(output, format="PNG", **options)
    return output.getvalue()


# --- TIFF a HEIF ----------------------------------------------------------------------


def tiff_xmp(image) -> bytes | None:
    """Vrátí paket XMP aktuálního snímku TIFF.

    :param image: Otevřený obrázek TIFF nastavený na požadovaný snímek.
    :return: Paket XMP, nebo ``None``, pokud ho snímek nemá.
    """
    xmp = image.tag_v2.get(XMP_TIFF_TAG)
    if isinstance(xmp, str):
        return xmp.encode("utf-8")
    if isinstance(xmp, tuple):
        return bytes(xmp)
    return xmp or None


def _tiff_blocks(data: bytes) -> list[str]:
    """Najde bloky s polohou ve všech snímcích TIFF.

    :param data: Celý soubor TIFF.
    :return: Identifikátory bloků s polohou.
    """
    blocks = []
    with Image.open(io.BytesIO(data)) as image:
        for index in range(getattr(image, "n_frames", 1)):
            image.seek(index)
            if GPS_IFD_TAG in image.tag_v2 or GPS_IFD_TAG in image.getexif():
                blocks.append(f"tiff[{index}].exif.gps")
            xmp = tiff_xmp(image)
            if xmp and has_xmp_location(xmp):
                blocks.append(f"tiff[{index}].xmp")
    return blocks


def _heif_blocks(content: io.BytesIO) -> list[str]:
    """Najde bloky s polohou ve všech obrázcích kontejneru HEIF.

    :param content: Obsah HEIF.
    :return: Identifikátory bloků s polohou.
    """
    content.seek(0)
    blocks = []
    for index, image in enumerate(pillow_heif.open_heif(content, convert_hdr_to_8bit=False)):
        exif = image.info.get("exif")
        if exif and exif_has_gps(exif):
            blocks.append(f"heif[{index}].exif.gps")
        xmp = image.info.get("xmp")
        if xmp and has_xmp_location(xmp):
            blocks.append(f"heif[{index}].xmp")
    content.seek(0)
    return blocks


# --- Společné rozhraní ----------------------------------------------------------------


def is_heif(content: io.BytesIO) -> bool:
    """Rozpozná HEIF podle obsahu a vrátí stream na začátek.

    :param content: Binární obsah fotografie.
    :return: Zda hlavička odpovídá formátu podporovanému knihovnou libheif.
    """
    content.seek(0)
    try:
        return pillow_heif.is_supported(content)
    finally:
        content.seek(0)


def is_tiff(content: io.BytesIO) -> bool:
    """Rozpozná TIFF podle signatury.

    :param content: Binární obsah fotografie.
    :return: Zda obsah začíná signaturou TIFF.
    """
    return content.getvalue()[: len(TIFF_SIGNATURES[0])] in TIFF_SIGNATURES


def find_location_metadata(content: io.BytesIO) -> list[str]:
    """Najde všechny bloky metadat, které nesou polohu.

    Kontroluje EXIF GPS, XMP (u JPEG i rozšířené XMP), surové profily PNG a u JPEG
    všechny obrázky indexu MPF. Data za koncem JPEG jen zapíše do logu.

    :param content: Obsah fotografie; pozice streamu se vrátí na začátek.
    :return: Identifikátory bloků (např. ``jpeg[1].exif.gps``); prázdný seznam, pokud
        soubor polohu nenese.
    :raises ValueError: Pokud metadata nelze rozebrat.
    """
    try:
        if is_heif(content):
            return _heif_blocks(content)
        data = content.getvalue()
        if data.startswith(JPEG_SIGNATURE):
            return _jpeg_blocks(data)
        if data.startswith(PNG_SIGNATURE):
            return _png_blocks(data)
        if is_tiff(content):
            return _tiff_blocks(data)
        with Image.open(io.BytesIO(data)) as image:
            exif = image.getexif()
            xmp = image.info.get("xmp")
            blocks = ["image.exif.gps"] if GPS_IFD_TAG in exif else []
            return blocks + (["image.xmp"] if xmp and has_xmp_location(xmp) else [])
    finally:
        content.seek(0)


def image_count(content: io.BytesIO) -> int:
    """Spočítá obrázky v souboru (snímky TIFF/PNG, obrázky HEIF a MPF).

    :param content: Obsah fotografie; pozice streamu se vrátí na začátek.
    :return: Počet obrázků.
    """
    try:
        if is_heif(content):
            return len(pillow_heif.open_heif(content, convert_hdr_to_8bit=False))
        data = content.getvalue()
        if data.startswith(JPEG_SIGNATURE):
            layout = _mpf_layout(data)
            return len(layout.images) if layout else 1
        with Image.open(io.BytesIO(data)) as image:
            return getattr(image, "n_frames", 1)
    finally:
        content.seek(0)


def remove_location_metadata(content: io.BytesIO) -> io.BytesIO:
    """Odstraní polohu z JPEG nebo PNG.

    HEIF a TIFF zpracovává ``Soubor.remove_heif_gps_data`` a ``Soubor.remove_tiff_gps_data``.

    :param content: Obsah fotografie.
    :return: Nový stream bez polohy na pozici nula.
    :raises ValueError: Pokud formát není podporován nebo ho nelze zpracovat.
    """
    data = content.getvalue()
    if data.startswith(JPEG_SIGNATURE):
        return io.BytesIO(remove_jpeg_location(data))
    if data.startswith(PNG_SIGNATURE):
        return io.BytesIO(remove_png_location(data))
    raise ValueError("Unsupported image format for location removal")
