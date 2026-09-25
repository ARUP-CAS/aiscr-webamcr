CORE distribution_names
=======================

Modul distribution_names.

Přehled modulu
--------------

Pravidla pro názvy alternativních distribucí a paradat souborů (issue #3527).

Název distribuce je zároveň cestou kontejneru ve Fedoře (``…/file/{uuid}/{distribuce}``),
takže musí projít stejnou kontrolou na obou vrstvách: při validaci importního CSV
(``core.import_data_mappers``) i těsně před zápisem do repozitáře
(``core.repository_connector``). Aby se obě vrstvy nemohly rozejít, žijí pravidla zde —
odděleně od ``core.constants``, kam patří jen konstanty bez logiky.

Funkce
------

.. py:function:: normalize_distribution_name(name)

   Sjednotí zápis názvu distribuce – odstraní bílé znaky a okrajová lomítka.

   Jediné místo, kde se název distribuce normalizuje; volají ho jak validace importu,
   tak connector, aby obě vrstvy pracovaly se stejnou hodnotou.

   :param name: Název distribuce z importu (např. `` /ocr/alto-xml/ ``).
   :return: Normalizovaný název, případně prázdný řetězec.

.. py:function:: is_reserved_distribution_name(name)

   Ověří, zda je název distribuce vyhrazený a nesmí být použit pro alternativní distribuci.

   Vyhrazený je jak samotný název, tak cokoli pod ním: ``paradata/alto-xml`` by zapsalo
   do kontejneru paradat mimo ``ParadataMapper`` a ``orig/x`` pod binární obsah souboru,
   kde by zápis stejně selhal až ve Fedoře.

   :param name: Název distribuce z importu (např. ``ocr/alto-xml``).
   :return: ``True``, pokud je název vyhrazený, jinak ``False``.

.. py:function:: has_unsafe_distribution_segments(name)

   Ověří, zda název distribuce obsahuje segment, který by vedl mimo kontejner souboru.

   Zachytí prázdné segmenty (``ocr//alto``) i průchod adresáři (``ocr/../orig``). Validace
   importu i connector používají tuto funkci, aby CSV neprošlo validací jen proto, že by
   chybu zachytil až zápis do Fedory.

   :param name: Název distribuce z importu.
   :return: ``True``, pokud je některý segment nepovolený, jinak ``False``.

.. py:function:: find_distribution_prefix_collisions(names)

   Najde dvojice názvů distribucí, kde jeden je předkem druhého v cestě.

   Název ``ocr`` je předkem ``ocr/alto-xml``: tentýž název nesmí být zároveň binární distribucí
   (list) i nadřazeným kontejnerem jiné distribuce. Zápis listu by ve Fedoře vytvořil binární
   uzel tam, kde pozdější ``ocr/alto-xml`` očekává kontejner, takže by zápis potomka selhal.
   Kontrola proto běží nad názvy jedné dávky (pro jeden soubor), kde jich jsou jednotky až
   desítky — kvadratické porovnání dvojic je tu levnější než budování indexu.

   :param names: Iterovatelný soubor názvů distribucí z importu (s duplicitami i mezerami).
   :return: Seznam dvojic ``(predchudce, potomek)`` v lexikografickém pořadí; prázdný,
       pokud nedošlo ke kolizi.
