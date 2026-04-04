PID model_serializers
=====================

Modul model_serializers.

Třídy
------

.. py:class:: ModelSerializer

   Implementuje komponentu ``ModelSerializer`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``record``: Doménový objekt (Dokument, Lokalita, SamostatnyNalez), jehož metadata budou serializována.


   .. py:method:: format_date()

      Naformátuje datum do řetězce ve formátu ISO 8601 (YYYY-MM-DD).

      **Parametry:**

      - ``date``: Objekt typu ``date`` určený k formátování.

      **Návratová hodnota:**

      Vrací výsledek volání ``strftime()``.


   .. py:method:: format_date_time()

      Naformátuje datum a čas do řetězce ve formátu ISO 8601 včetně časové zóny.

      **Parametry:**

      - ``date_time``: Objekt typu ``datetime`` určený k formátování.

      **Návratová hodnota:**

      Vrací výsledek volání ``strftime()``.


   .. py:method:: _get_creators()

      Vrací creators.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: _get_historie_queryset()

      Vrací historie queryset.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: get_ident_cely()

      Vrací ident cely.

   .. py:method:: _get_publication_year()

      Vrací publication year.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: _get_language()

      Vrací language.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: _get_prefix()

      Vrací prefix.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: _get_soubory_queryset()

      Vrací soubory queryset.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: _get_title()

      Vrací title.

      **Parametry:**

      - ``language``: Textový název, klíč nebo zpráva ``language`` používaná v rámci operace.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: _serialize_alternate_identifiers()

      Sestaví seznam alternativních identifikátorů záznamu pro DataCite, obsahující přístupové číslo AMČR.

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice.


   .. py:method:: _serialize_contributors()

      Sestaví seznam přispěvatelů záznamu pro DataCite, zahrnující AIS CR jako hostitelskou instituci.

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice.


   .. py:method:: _serialize_creators()

      Sestaví seznam tvůrců záznamu pro DataCite.

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice.


   .. py:method:: _serialize_dates()

      Sestaví seznam dat (vznik, odeslání, archivace apod.) pro DataCite metadata.

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice.


   .. py:method:: _serialize_descriptions()

      Sestaví seznam popisů záznamu pro DataCite (abstrakt, technické informace apod.).

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice.


   .. py:method:: _serialize_geolocations()

      Sestaví seznam geografických souřadnic a lokalit záznamu pro DataCite metadata.

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice.


   .. py:method:: _serialize_related_identifiers()

      Sestaví seznam souvisejících identifikátorů záznamu pro DataCite, včetně odkazu na OAI-PMH metadata.

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice.


   .. py:method:: _serialize_rightslist()

      Sestaví seznam licenčních práv záznamu pro DataCite metadata.

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice.


   .. py:method:: _serialize_subjects()

      Sestaví základní seznam tematických klíčových slov pro DataCite, obsahující klasifikaci oboru archeologie.

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice.


   .. py:method:: _serialize_types()

      Sestaví slovník s typem zdroje záznamu pro DataCite metadata.

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice.


   .. py:method:: _get_formats()

      Vrací formats.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: serialize_delete()

      Sestaví DataCite payload pro skrytí záznamu s doplněním zprávy o odstranění z repozitáře AMČR.

      **Návratová hodnota:**

      Vrací slovník.


   .. py:method:: serialize_hide()

      Sestaví minimální DataCite payload s událostí ``hide`` pro skrytí záznamu.

      **Návratová hodnota:**

      Vrací slovník.


   .. py:method:: serialize_publish()

      Sestaví kompletní DataCite payload pro publikaci záznamu včetně všech povinných metadat.

      **Návratová hodnota:**

      Vrací proměnná ``data``.


   .. py:method:: serialize_update()

      Sestaví DataCite payload pro aktualizaci záznamu (bez pole ``event`` oproti publish).

      **Návratová hodnota:**

      Vrací proměnná ``result``.



.. py:class:: PartialSerializer

   Implementuje komponentu ``PartialSerializer`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``record``: Doménový objekt, jehož metadata budou částečně serializována.


   .. py:method:: serialize_publish()

      Sestaví částečný DataCite payload pro publikaci záznamu (abstraktní implementace).


.. py:class:: DokumentSerializer

   Implementuje komponentu ``DokumentSerializer`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``record``: Parametr ``record`` předává se do volání ``__init__()``.


   .. py:method:: _get_creators()

      Vrací creators.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: _get_historie_queryset()

      Vrací historie queryset.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: get_ident_cely()

      Vrací ident cely.

      **Návratová hodnota:**

      Vrací atribut objektu.


   .. py:method:: _get_language()

      Vrací language.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: _get_publication_year()

      Vrací publication year.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: _get_prefix()

      Vrací prefix.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: _get_soubory_queryset()

      Vrací soubory queryset.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: _get_title()

      Vrací title.

      **Parametry:**

      - ``language``: Textový název, klíč nebo zpráva ``language`` používaná v rámci operace.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: _serialize_alternate_identifiers()

      Sestaví seznam alternativních identifikátorů dokumentu pro DataCite, včetně označení originálu.

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice.


   .. py:method:: _serialize_contributors()

      Sestaví seznam přispěvatelů dokumentu pro DataCite, zahrnující pozorovatele letu, vedoucí neidentifikovatelných akcí a vedoucí projektů.

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice.


   .. py:method:: _serialize_creators()

      Sestaví seznam tvůrců dokumentu pro DataCite ze seznamu autorů dokumentu.

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice.


   .. py:method:: _serialize_dates()

      Sestaví seznam dat dokumentu pro DataCite z jeho historie (zápis, odeslání, archivace, vrácení) a z období komponent.

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice.


   .. py:method:: _serialize_descriptions()

      Serializuje popisy dokumentu (abstrakt a technické informace).

      **Návratová hodnota:**

      Seznam slovníků obsahujících jazykové varianty popisu.


   .. py:method:: _serialize_geolocations()

      Serializuje geografické lokalizace dokumentu z projektů, akcí a lokalit.

      **Návratová hodnota:**

      Seznam slovníků s geografickými souřadnicemi a metadaty.


   .. py:method:: _serialize_related_identifiers()

      Serializuje související identifikátory (soubory, archivní odkaz, související akce).

      **Návratová hodnota:**

      Seznam slovníků s identifikátory související obsahu.


   .. py:method:: _serialize_rightslist()

      Serializuje informace o právech a licencích dokumentu.

      **Návratová hodnota:**

      Seznam slovníků s údaji o licencích a právech.


   .. py:method:: _serialize_subjects()

      Serializuje předmětová hesla z posudků, osob, typů událostí a komponent.

      **Návratová hodnota:**

      Seznam slovníků s předmětovými hesly.


   .. py:method:: _serialize_types()

      Serializuje typ dokumentu do DataCite schématu.

      **Návratová hodnota:**

      Slovník s ResourceType a ResourceTypeGeneral.


   .. py:method:: _get_formats()

      Vrací formats.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.



.. py:class:: SamostatnyNalezSerializer

   Implementuje komponentu ``SamostatnyNalezSerializer`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``record``: Parametr ``record`` předává se do volání ``__init__()``.


   .. py:method:: _get_creators()

      Vrací creators.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: _get_historie_queryset()

      Vrací historie queryset.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: get_ident_cely()

      Vrací ident cely.

      **Návratová hodnota:**

      Vrací atribut objektu.


   .. py:method:: _get_soubory_queryset()

      Vrací soubory queryset.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: _get_prefix()

      Vrací prefix.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: _get_publication_year()

      Vrací publication year.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: _get_title()

      Vrací title.

      **Parametry:**

      - ``language``: Textový název, klíč nebo zpráva ``language`` používaná v rámci operace.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: _serialize_alternate_identifiers()

      Serializuje alternativní identifikátory nálezu (evidenční čísla).

      **Návratová hodnota:**

      Seznam slovníků s alternativními identifikátory.


   .. py:method:: _serialize_contributors()

      Serializuje přispěvatele (vedoucí projektu, organizaci, která nálezy převzala).

      **Návratová hodnota:**

      Seznam slovníků s informacemi o přispěvatelích.


   .. py:method:: _serialize_creators()

      Serializuje tvůrce nálezu (nálezce a jeho organizaci).

      **Návratová hodnota:**

      Seznam slovníků s údaji o nálezci.


   .. py:method:: _serialize_dates()

      Serializuje data nálezu (datum nálezu, vytvoření, potvrzení, archivace).

      **Návratová hodnota:**

      Seznam slovníků s daty a jejich typy.


   .. py:method:: _serialize_descriptions()

      Serializuje popisy nálezu (poznámky, okolnosti, hloubku, počet).

      **Návratová hodnota:**

      Seznam slovníků s jazykovými variantami popisu.


   .. py:method:: _serialize_geolocations()

      Serializuje geografické lokalizace dokumentu z projektů, akcí a lokalit.

      **Návratová hodnota:**

      Seznam slovníků s geografickými souřadnicemi a metadaty.


   .. py:method:: _serialize_related_identifiers()

      Serializuje související identifikátory (soubory, archivní odkaz, související akce).

      **Návratová hodnota:**

      Seznam slovníků s identifikátory související obsahu.


   .. py:method:: _serialize_rightslist()

      Serializuje informace o právech a licencích dokumentu.

      **Návratová hodnota:**

      Seznam slovníků s údaji o licencích a právech.


   .. py:method:: _serialize_subjects()

      Serializuje předmětová hesla z posudků, osob, typů událostí a komponent.

      **Návratová hodnota:**

      Seznam slovníků s předmětovými hesly.


   .. py:method:: _serialize_types()

      Serializuje typ nálezu do DataCite schématu.

      **Návratová hodnota:**

      Slovník s ResourceType a ResourceTypeGeneral.


   .. py:method:: _get_formats()

      Vrací formats.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.



.. py:class:: LokalitaSerializer

   Implementuje komponentu ``LokalitaSerializer`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``record``: Parametr ``record`` předává se do volání ``__init__()``.


   .. py:method:: _get_creators()

      Vrací creators.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: get_ident_cely()

      Vrací ident cely.

      **Návratová hodnota:**

      Vrací atribut objektu.


   .. py:method:: _get_historie_queryset()

      Vrací historie queryset.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: _get_prefix()

      Vrací prefix.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: _serialize_contributors()

      Serializuje přispěvatele (vedoucí projektu, organizaci, která nálezy převzala).

      **Návratová hodnota:**

      Seznam slovníků s informacemi o přispěvatelích.


   .. py:method:: _get_soubory_queryset()

      Vrací soubory queryset.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: _serialize_dates()

      Serializuje data lokality (vytvoření, změny, archivace z historie archeologické akce).

      **Návratová hodnota:**

      Seznam slovníků s daty a jejich typy.


   .. py:method:: _serialize_descriptions()

      Serializuje popisy nálezu (poznámky, okolnosti, hloubku, počet).

      **Návratová hodnota:**

      Seznam slovníků s jazykovými variantami popisu.


   .. py:method:: _get_externi_odkaz_query()

      Vrací externi odkaz query.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: _serialize_geolocations()

      Serializuje geografické lokalizace dokumentu z projektů, akcí a lokalit.

      **Návratová hodnota:**

      Seznam slovníků s geografickými souřadnicemi a metadaty.


   .. py:method:: _get_publication_year()

      Vrací publication year.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: _serialize_rightslist()

      Serializuje informace o právech a licencích dokumentu.

      **Návratová hodnota:**

      Seznam slovníků s údaji o licencích a právech.


   .. py:method:: _get_title()

      Vrací title.

      **Parametry:**

      - ``language``: Textový název, klíč nebo zpráva ``language`` používaná v rámci operace.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: _serialize_alternate_identifiers()

      Serializuje alternativní identifikátory nálezu (evidenční čísla).

      **Návratová hodnota:**

      Seznam slovníků s alternativními identifikátory.


   .. py:method:: _serialize_creators()

      Serializuje tvůrce nálezu (nálezce a jeho organizaci).

      **Návratová hodnota:**

      Seznam slovníků s údaji o nálezci.


   .. py:method:: _serialize_related_identifiers()

      Serializuje související identifikátory (soubory, archivní odkaz, související akce).

      **Návratová hodnota:**

      Seznam slovníků s identifikátory související obsahu.


   .. py:method:: _serialize_related_items()

      Serializuje související položky (externí zdroje související s lokalitou).

      **Návratová hodnota:**

      Seznam slovníků se související obsahu.


   .. py:method:: _serialize_subjects()

      Serializuje předmětová hesla z posudků, osob, typů událostí a komponent.

      **Návratová hodnota:**

      Seznam slovníků s předmětovými hesly.


   .. py:method:: _serialize_types()

      Serializuje typ nálezu do DataCite schématu.

      **Návratová hodnota:**

      Slovník s ResourceType a ResourceTypeGeneral.


   .. py:method:: _get_formats()

      Vrací formats.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: serialize_publish()

      Serializuje lokalitu pro publikaci s přidáním souvisejících položek.

      **Návratová hodnota:**

      Slovník s připraveným datovým balíčkem pro DataCite.


   .. py:method:: serialize_update()

      Serializuje lokalitu pro aktualizaci se smazáním pole event.

      **Návratová hodnota:**

      Slovník s připraveným datovým balíčkem pro DataCite.



Funkce
------

.. py:function:: convert_geo_location_to_dict(item)

   Převede geo location to dict.

   **Parametry:**

   - ``item``: Jedna položka zpracovávané kolekce.

   **Návratová hodnota:**

   Výstup funkce odpovídající implementované logice.


.. py:function:: serialize_ez_creator(autor)

   Serializuje osobu jako tvůrce externího zdroje do formátu DataCite.

   **Parametry:**

   - ``autor``: Osoba vystupující jako autor externího zdroje v systému AMČR.

   **Návratová hodnota:**

   Výstup funkce odpovídající implementované logice.


.. py:function:: serialize_ez_contributor(contributor)

   Serializuje osobu jako přispěvatele (editora) externího zdroje do formátu DataCite.

   **Parametry:**

   - ``contributor``: Osoba vystupující jako editor externího zdroje v systému AMČR.

   **Návratová hodnota:**

   Výstup funkce odpovídající implementované logice.


.. py:function:: serialize_geom(geom, katastr, verejne)

   Serializuje geometrii a katastr do formátu geoLocationPoint/geoLocationPlace pro DataCite metadata.

   **Parametry:**

   - ``geom``: Geometrie záznamu (bod nebo polygon), z níž se použije centroid; ``None`` přeskočí souřadnice.
   - ``katastr``: Katastrální území záznamu použité pro textový popis polohy; ``None`` přeskočí lokalitu.
   - ``verejne``: Příznak, zda má být záznam zobrazen veřejně — ovlivňuje úroveň detailu souřadnic.

   **Návratová hodnota:**

   Výstup funkce odpovídající implementované logice.


.. py:function:: serialize_affiliation(organizace)

   Serializuje organizaci jako institucionální příslušnost osoby do formátu DataCite.

   **Parametry:**

   - ``organizace``: Organizace AMČR, jejíž název a případný ROR identifikátor budou zahrnuty.

   **Návratová hodnota:**

   Vrací proměnná ``serialized_affiliation``.


.. py:function:: serialize_organizace_contributor(organizace, contributor_type)

   Serializuje organizaci jako přispěvatele záznamu do formátu DataCite.

   **Parametry:**

   - ``organizace``: Organizace AMČR, která má být zahrnuta jako přispěvatel.
   - ``contributor_type``: Typ přispěvatele dle schématu DataCite (např. ``DataCurator``, ``HostingInstitution``).

   **Návratová hodnota:**

   Vrací slovník.


.. py:function:: serialize_osoba_identifiers(osoba)

   Sestaví seznam identifikátorů osoby (AMČR, ORCID, Wikidata) pro DataCite metadata.

   **Parametry:**

   - ``osoba``: Osoba z číselníku AMČR, jejíž identifikátory mají být zahrnuty.

   **Návratová hodnota:**

   Vrací proměnná ``result``.


.. py:function:: serialize_osoba(osoba, organizace, contributor_type)

   Serializuje osobu (autora nebo přispěvatele) do formátu DataCite včetně identifikátorů a příslušnosti.

   **Parametry:**

   - ``osoba``: Osoba z číselníku AMČR, která má být serializována.
   - ``organizace``: Organizace, ke které je osoba přiřazena; ``None`` vynechá příslušnost.
   - ``contributor_type``: Typ přispěvatele dle DataCite; pokud je zadán, bude přidán do výsledku.

   **Návratová hodnota:**

   Výstup funkce odpovídající implementované logice.


.. py:function:: serialize_subject(serialized_record, subject_attr, lang)

   Serializuje heslo ze slovníku AMČR jako tematické klíčové slovo pro DataCite metadata.

   **Parametry:**

   - ``serialized_record``: Heslo ze slovníku AMČR (Heslar), které má být serializováno; ``None`` vrátí prázdnou množinu.
   - ``subject_attr``: Název atributu objektu ``serialized_record``, jehož hodnota bude použita jako text hesla.
   - ``lang``: Kód jazyka dle ISO 639-1 pro pole ``lang`` ve výstupu DataCite.

   **Návratová hodnota:**

   Vrací výsledek volání ``frozenset()``.


.. py:function:: serialize_subjects_komponenty(komp)

   Sestaví seznam tematických klíčových slov ze všech atributů komponenty (období, areál, aktivity, objekty, předměty).

   **Parametry:**

   - ``komp``: Komponenta dokumentační jednotky nebo části dokumentu v systému AMČR.

   **Návratová hodnota:**

   Vrací proměnná ``result``.


.. py:function:: serialize_dates_coverage(datace)

   Serializuje časové pokrytí komponenty (období) do formátu DataCite date Coverage.

   **Parametry:**

   - ``datace``: Heslo ze slovníku AMČR reprezentující dataci s vazbou na rozsah let.

   **Návratová hodnota:**

   Výstup funkce odpovídající implementované logice.

