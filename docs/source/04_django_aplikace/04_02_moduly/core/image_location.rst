CORE image_location
===================

Modul image_location.

Přehled modulu
--------------

Vyhledání a odstranění údajů o poloze v metadatech fotografií PAS.

Modul nezávisí na Djangu. Kontroluje GPS v EXIF, souřadnice v XMP (včetně rozšířeného
XMP v JPEG), textové bloky PNG s vloženým EXIF/XMP a vedlejší obrázky vícesnímkových
JPEG (MPF/MPO). EXIF upravuje na místě bez změny délky, takže offsety vnořených adresářů,
náhledu (IFD1), MakerNote i indexu MPF zůstanou platné. JPEG se nikdy znovu nekóduje.

Nezpracovává textové údaje o místě v IPTC-IIM, MakerNote, komentářích ani data za koncem
JPEG (např. video pohyblivé fotografie); ta pouze zapisuje do logu.

Třídy
------

.. py:class:: _JpegSegment

   Segment hlavičky JPEG před prvním skenem.


.. py:class:: _MpfLayout

   Rozložení vícesnímkového JPEG podle indexu MPF.


.. py:class:: _PngText

   Textový blok PNG po dekódování.


Funkce
------

.. py:function:: _tiff_layout(data)

   Najde začátek struktury TIFF v EXIF a její pořadí bajtů.

   :param data: EXIF s volitelnou signaturou ``Exif\0\0``.
   :return: Dvojice (pozice hlavičky TIFF, prefix ``struct`` pro pořadí bajtů).
   :raises ValueError: Pokud hlavička TIFF chybí nebo je neplatná.

.. py:function:: _tiff_ifd_chain(data, base, endian)

   Vrátí hlavní řetězec adresářů EXIF (IFD0, IFD1, ...).

   Neplatný ukazatel na další adresář ukončí řetězec stejně jako v Pillow; neplatný
   první adresář je chyba.

   :param data: EXIF data.
   :param base: Pozice hlavičky TIFF v ``data``.
   :param endian: Prefix ``struct`` pro pořadí bajtů.
   :return: Seznam dvojic (offset adresáře vůči hlavičce, počet položek).
   :raises ValueError: Pokud první adresář leží mimo data nebo řetězec obsahuje cyklus.

.. py:function:: _gps_entries(data, base, endian)

   Najde položky odkazující na GPS IFD ve všech hlavních adresářích.

   :param data: EXIF data.
   :param base: Pozice hlavičky TIFF.
   :param endian: Prefix ``struct`` pro pořadí bajtů.
   :return: Seznam dvojic (absolutní pozice položky, offset GPS IFD).

.. py:function:: exif_has_gps(exif)

   Zjistí, zda EXIF obsahuje odkaz na GPS IFD.

   :param exif: EXIF s volitelnou signaturou ``Exif\0\0``.
   :return: ``True``, pokud některý hlavní adresář odkazuje na GPS IFD.
   :raises ValueError: Pokud EXIF nelze rozebrat.

.. py:function:: _zero_gps_ifd(data, base, endian, offset)

   Přepíše nulami GPS IFD a jeho hodnoty uložené mimo položky.

   :param data: Upravovaná EXIF data.
   :param base: Pozice hlavičky TIFF.
   :param endian: Prefix ``struct`` pro pořadí bajtů.
   :param offset: Offset GPS IFD vůči hlavičce; neplatný offset se přeskočí.

.. py:function:: remove_exif_gps(exif)

   Odstraní GPS z EXIF na místě, bez změny délky a ostatních offsetů.

   Odkaz na GPS IFD se vyjme z adresáře (položky se posunou a uvolněné místo vynuluje)
   a samotný GPS IFD i jeho hodnoty se přepíší nulami.

   :param exif: EXIF s volitelnou signaturou ``Exif\0\0``.
   :return: EXIF stejné délky bez GPS; bez GPS vrací vstup beze změny.
   :raises ValueError: Pokud EXIF nelze rozebrat.

.. py:function:: _parse_xmp(xmp)

   Bezpečně rozebere paket XMP bez DTD, entit a síťového přístupu.

   :param xmp: Paket XMP včetně případných instrukcí ``<?xpacket?>``.
   :return: Kořenový element dokumentu.
   :raises etree.XMLSyntaxError: Pokud paket není platné XML.
   :raises ValueError: Pokud paket obsahuje deklaraci DOCTYPE.

.. py:function:: _is_location_name(name)

   Rozhodne, zda kvalifikovaný název vlastnosti XMP nese polohu.

   :param name: Název elementu nebo atributu ve tvaru ``{namespace}local``.
   :return: ``True`` pro vlastnosti začínající ``GPS`` v libovolném jmenném prostoru
       a pro ``Iptc4xmpExt:LocationCreated``/``LocationShown``.

.. py:function:: _remove_element(element)

   Odstraní element a zachová text, který za ním následoval.

   :param element: Element XMP k odstranění.

.. py:function:: _remove_property(root, name)

   Odstraní všechny výskyty vlastnosti ve tvaru atributu i elementu.

   :param root: Kořen dokumentu XMP.
   :param name: Kvalifikovaný název vlastnosti.
   :return: ``True``, pokud se něco odstranilo.

.. py:function:: _strip_location(root)

   Odstraní z dokumentu XMP všechny vlastnosti nesoucí polohu.

   :param root: Kořen dokumentu XMP.
   :return: ``True``, pokud se něco odstranilo.

.. py:function:: has_xmp_location(xmp)

   Zjistí, zda paket XMP obsahuje polohu.

   :param xmp: Paket XMP.
   :return: ``True`` pro polohu i pro paket, který nelze rozebrat.

.. py:function:: _update_container_lengths(root, lengths)

   Aktualizuje délky vedlejších položek ``Container:Directory`` (Ultra HDR).

   :param root: Kořen dokumentu XMP hlavního obrázku.
   :param lengths: Nové délky vedlejších obrázků v pořadí souboru.
   :return: ``True``, pokud dokument adresář obsahuje a délky se nastavily.
   :raises ValueError: Pokud počet položek adresáře neodpovídá počtu obrázků.

.. py:function:: rewrite_xmp(xmp, container_lengths, drop_extended)

   Odstraní polohu z paketu XMP a volitelně upraví odkazy na další data.

   Ostatní vlastnosti (např. ``hdrgm:*`` a ``Container:Directory``) zůstanou zachovány.

   :param xmp: Paket XMP.
   :param container_lengths: Nové délky vedlejších obrázků pro ``Container:Directory``.
   :param drop_extended: Zda odstranit ``xmpNote:HasExtendedXMP`` po zahození rozšířeného XMP.
   :return: Upravený paket, původní paket beze změny, nebo ``None``, pokud ho nelze
       rozebrat a je nutné ho celý zahodit.
   :raises ValueError: Pokud ``Container:Directory`` neodpovídá počtu obrázků.

.. py:function:: strip_xmp_location(xmp)

   Odstraní z paketu XMP vlastnosti nesoucí polohu.

   :param xmp: Paket XMP.
   :return: Paket bez polohy, nebo ``None``, pokud ho nelze rozebrat.

.. py:function:: _parse_jpeg_header(data)

   Rozdělí hlavičku JPEG na segmenty až po první SOS.

   :param data: Jeden obrázek JPEG.
   :return: Seznam segmentů a pozice značky SOS.
   :raises ValueError: Pokud hlavička není úplná nebo obsahuje neplatnou značku.

.. py:function:: _jpeg_end(data, offset)

   Najde konec obrázku JPEG (za značkou EOI) průchodem komprimovaných dat.

   :param data: Obsah začínající obrázkem JPEG.
   :param offset: Pozice první značky SOS.
   :return: Pozice za EOI; délka dat, pokud EOI chybí.

.. py:function:: _segment(marker, payload)

   Sestaví segment JPEG se značkou a délkou.

   :param marker: Druhý bajt značky.
   :param payload: Obsah segmentu bez délky.
   :return: Celý segment.
   :raises ValueError: Pokud obsah překročí kapacitu segmentu.

.. py:function:: _app1(segment, signature)

   Zjistí, zda je segment APP1 s danou signaturou.

   :param segment: Segment hlavičky JPEG.
   :param signature: Očekávaný začátek obsahu.
   :return: ``True`` při shodě.

.. py:function:: _extended_xmp(segments)

   Složí rozšířené XMP z jednotlivých segmentů podle GUID a offsetu.

   :param segments: Segmenty hlavičky JPEG.
   :return: Složené pakety rozšířeného XMP.

.. py:function:: _jpeg_image_blocks(data, ident)

   Najde bloky s polohou v jednom obrázku JPEG.

   :param data: Jeden obrázek JPEG.
   :param ident: Označení obrázku pro výsledné identifikátory.
   :return: Identifikátory bloků s polohou.
   :raises ValueError: Pokud hlavičku nebo EXIF nelze rozebrat nebo obsahuje více EXIF.

.. py:function:: _clean_jpeg_image(data, container_lengths)

   Odstraní polohu z jednoho obrázku JPEG bez dekódování obrazových dat.

   EXIF se upraví na místě, XMP se nahradí vyčištěným paketem nebo zahodí a rozšířené
   XMP s polohou se zahodí celé. Ostatní segmenty a vše od SOS zůstane beze změny.

   :param data: Jeden obrázek JPEG.
   :param container_lengths: Nové délky vedlejších obrázků pro ``Container:Directory``.
   :return: Obrázek bez polohy.
   :raises ValueError: Pokud hlavičku nelze rozebrat nebo XMP nelze uložit do segmentu.

.. py:function:: _mpf_segment(data)

   Najde segment APP2 s indexem MPF v hlavním obrázku.

   :param data: Soubor JPEG začínající hlavním obrázkem.
   :return: Segment a absolutní pozice hlavičky TIFF indexu, nebo ``None``, pokud chybí.
   :raises ValueError: Pokud hlavičku JPEG nelze rozebrat.

.. py:function:: _mpf_layout(data)

   Rozebere index MPF hlavního obrázku a vrátí polohu všech obrázků.

   :param data: Celý soubor JPEG.
   :return: Rozložení obrázků, nebo ``None``, pokud soubor index MPF nemá.
   :raises ValueError: Pokud index odkazuje mimo soubor nebo se obrázky překrývají.

.. py:function:: _jpeg_trailer(data, layout)

   Spočítá délku nenulových dat za posledním obrázkem JPEG.

   :param data: Celý soubor JPEG.
   :param layout: Rozložení MPF, nebo ``None`` pro jednoduchý JPEG.
   :return: Počet bajtů za koncem posledního obrázku, pokud nejsou jen výplní.

.. py:function:: _jpeg_blocks(data)

   Najde bloky s polohou ve všech obrázcích souboru JPEG.

   :param data: Celý soubor JPEG.
   :return: Identifikátory bloků s polohou.

.. py:function:: remove_jpeg_location(data)

   Odstraní polohu ze všech obrázků JPEG včetně vedlejších obrázků MPF.

   Obrázky bez polohy zůstanou bajtově shodné. Po změně délky se přepočítá index MPF
   a délky v ``Container:Directory`` hlavního obrázku (Ultra HDR).

   :param data: Celý soubor JPEG.
   :return: Soubor bez polohy.
   :raises ValueError: Pokud soubor nelze rozebrat nebo index MPF nelze aktualizovat.

.. py:function:: _inflate(data)

   Rozbalí komprimovaný textový blok PNG s omezením velikosti.

   :param data: Data komprimovaná metodou zlib.
   :return: Rozbalená data.
   :raises ValueError: Pokud rozbalená data překročí ``PNG_MAX_TEXT_SIZE``.

.. py:function:: _png_chunks(data)

   Přečte EXIF a textové bloky PNG bez dekódování obrazových dat.

   :param data: Celý soubor PNG.
   :return: Obsah bloku ``eXIf`` (nebo ``None``) a dekódované textové bloky.
   :raises ValueError: Pokud je struktura bloků poškozená.

.. py:function:: _raw_profile(text)

   Dekóduje hexadecimální profil ImageMagick (``Raw profile type ...``).

   :param text: Textový blok PNG.
   :return: Binární obsah profilu, nebo ``None``, pokud blok není surový profil.
   :raises ValueError: Pokud profil nelze dekódovat.

.. py:function:: _raw_profile_has_location(profile)

   Zjistí, zda surový profil PNG obsahuje polohu.

   :param profile: Dekódovaný obsah profilu (EXIF, APP1 nebo XMP).
   :return: ``True`` pro polohu i pro profil, který nelze rozebrat.

.. py:function:: _png_text_has_location(text)

   Zjistí, zda textový blok PNG nese polohu.

   :param text: Textový blok PNG.
   :return: ``True`` pro XMP nebo surový profil s polohou.

.. py:function:: _png_blocks(data)

   Najde bloky s polohou v PNG.

   :param data: Celý soubor PNG.
   :return: Identifikátory bloků s polohou.
   :raises ValueError: Pokud strukturu PNG nebo EXIF nelze rozebrat.

.. py:function:: remove_png_location(data)

   Odstraní polohu z PNG a zachová ostatní textové bloky.

   Obrazová data se znovu uloží bezeztrátově. XMP se zapíše vyčištěné, surové profily
   s polohou se zahodí a ostatní textové bloky se přenesou beze změny.

   :param data: Celý soubor PNG.
   :return: PNG bez polohy.
   :raises ValueError: Pokud PNG nelze rozebrat.

.. py:function:: tiff_xmp(image)

   Vrátí paket XMP aktuálního snímku TIFF.

   :param image: Otevřený obrázek TIFF nastavený na požadovaný snímek.
   :return: Paket XMP, nebo ``None``, pokud ho snímek nemá.

.. py:function:: _tiff_blocks(data)

   Najde bloky s polohou ve všech snímcích TIFF.

   :param data: Celý soubor TIFF.
   :return: Identifikátory bloků s polohou.

.. py:function:: _heif_blocks(content)

   Najde bloky s polohou ve všech obrázcích kontejneru HEIF.

   :param content: Obsah HEIF.
   :return: Identifikátory bloků s polohou.

.. py:function:: is_heif(content)

   Rozpozná HEIF podle obsahu a vrátí stream na začátek.

   :param content: Binární obsah fotografie.
   :return: Zda hlavička odpovídá formátu podporovanému knihovnou libheif.

.. py:function:: is_tiff(content)

   Rozpozná TIFF podle signatury.

   :param content: Binární obsah fotografie.
   :return: Zda obsah začíná signaturou TIFF.

.. py:function:: find_location_metadata(content)

   Najde všechny bloky metadat, které nesou polohu.

   Kontroluje EXIF GPS, XMP (u JPEG i rozšířené XMP), surové profily PNG a u JPEG
   všechny obrázky indexu MPF. Data za koncem JPEG jen zapíše do logu.

   :param content: Obsah fotografie; pozice streamu se vrátí na začátek.
   :return: Identifikátory bloků (např. ``jpeg[1].exif.gps``); prázdný seznam, pokud
       soubor polohu nenese.
   :raises ValueError: Pokud metadata nelze rozebrat.

.. py:function:: image_count(content)

   Spočítá obrázky v souboru (snímky TIFF/PNG, obrázky HEIF a MPF).

   :param content: Obsah fotografie; pozice streamu se vrátí na začátek.
   :return: Počet obrázků.

.. py:function:: remove_location_metadata(content)

   Odstraní polohu z JPEG nebo PNG.

   HEIF a TIFF zpracovává ``Soubor.remove_heif_gps_data`` a ``Soubor.remove_tiff_gps_data``.

   :param content: Obsah fotografie.
   :return: Nový stream bez polohy na pozici nula.
   :raises ValueError: Pokud formát není podporován nebo ho nelze zpracovat.
