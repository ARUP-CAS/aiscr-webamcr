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

      :param record: Doménový objekt (Dokument, Lokalita, SamostatnyNalez), jehož metadata budou serializována.

   .. py:method:: format_date()

      Naformátuje datum do řetězce ve formátu ISO 8601 (YYYY-MM-DD).

      :param date: Objekt typu ``date`` určený k formátování.

      :return: Vrací výsledek volání ``strftime()``.

   .. py:method:: format_date_time()

      Naformátuje datum a čas do řetězce ve formátu ISO 8601 včetně časové zóny.

      :param date_time: Objekt typu ``datetime`` určený k formátování.

      :return: Vrací výsledek volání ``strftime()``.

   .. py:method:: _get_creators()

      Vrací creators.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _get_historie_queryset()

      Vrací historie queryset.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: get_ident_cely()

      Vrací ident cely.

   .. py:method:: _get_publication_year()

      Vrací publication year.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _get_language()

      Vrací language.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _get_prefix()

      Vrací prefix.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _get_soubory_queryset()

      Vrací soubory queryset.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _get_title()

      Vrací title.

      :param language: Textový název, klíč nebo zpráva ``language`` používaná v rámci operace.
      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _serialize_alternate_identifiers()

      Sestaví seznam alternativních identifikátorů záznamu pro DataCite, obsahující přístupové číslo AMČR.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _serialize_contributors()

      Sestaví seznam přispěvatelů záznamu pro DataCite, zahrnující AIS CR jako hostitelskou instituci.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _serialize_creators()

      Sestaví seznam tvůrců záznamu pro DataCite.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _serialize_dates()

      Sestaví seznam dat (vznik, odeslání, archivace apod.) pro DataCite metadata.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _serialize_descriptions()

      Sestaví seznam popisů záznamu pro DataCite (abstrakt, technické informace apod.).

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _serialize_geolocations()

      Sestaví seznam geografických souřadnic a lokalit záznamu pro DataCite metadata.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _serialize_related_identifiers()

      Sestaví seznam souvisejících identifikátorů záznamu pro DataCite, včetně odkazu na OAI-PMH metadata.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _serialize_rightslist()

      Sestaví seznam licenčních práv záznamu pro DataCite metadata.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _serialize_subjects()

      Sestaví základní seznam tematických klíčových slov pro DataCite, obsahující klasifikaci oboru archeologie.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _serialize_types()

      Sestaví slovník s typem zdroje záznamu pro DataCite metadata.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _get_formats()

      Vrací formats.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: serialize_delete()

      Sestaví DataCite payload pro skrytí záznamu s doplněním zprávy o odstranění z repozitáře AMČR.

      :return: Vrací slovník.

   .. py:method:: serialize_hide()

      Sestaví minimální DataCite payload s událostí ``hide`` pro skrytí záznamu.

      :return: Vrací slovník.

   .. py:method:: serialize_publish()

      Sestaví kompletní DataCite payload pro publikaci záznamu včetně všech povinných metadat.

      :return: Vrací proměnná ``data``.

   .. py:method:: serialize_update()

      Sestaví DataCite payload pro aktualizaci záznamu (bez pole ``event`` oproti publish).

      :return: Vrací proměnná ``result``.


.. py:class:: PartialSerializer

   Implementuje komponentu ``PartialSerializer`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param record: Doménový objekt, jehož metadata budou částečně serializována.

   .. py:method:: serialize_publish()

      Sestaví částečný DataCite payload pro publikaci záznamu (abstraktní implementace).


.. py:class:: DokumentSerializer

   Implementuje komponentu ``DokumentSerializer`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param record: Parametr ``record`` předává se do volání ``__init__()``.

   .. py:method:: _get_creators()

      Vrací creators.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _get_historie_queryset()

      Vrací historie queryset.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: get_ident_cely()

      Vrací ident cely.

      :return: Vrací atribut objektu.

   .. py:method:: _get_language()

      Vrací language.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _get_publication_year()

      Vrací publication year.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _get_prefix()

      Vrací prefix.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _get_soubory_queryset()

      Vrací soubory queryset.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _get_title()

      Vrací title.

      :param language: Textový název, klíč nebo zpráva ``language`` používaná v rámci operace.
      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _serialize_alternate_identifiers()

      Sestaví seznam alternativních identifikátorů dokumentu pro DataCite, včetně označení originálu.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _serialize_contributors()

      Sestaví seznam přispěvatelů dokumentu pro DataCite, zahrnující pozorovatele letu, vedoucí neidentifikovatelných akcí a vedoucí projektů.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _serialize_creators()

      Sestaví seznam tvůrců dokumentu pro DataCite ze seznamu autorů dokumentu.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _serialize_dates()

      Sestaví seznam dat dokumentu pro DataCite z jeho historie (zápis, odeslání, archivace, vrácení) a z období komponent.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _serialize_descriptions()

      Provádí operaci serialize descriptions.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _serialize_geolocations()

      Provádí operaci serialize geolocations.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _serialize_related_identifiers()

      Provádí operaci serialize related identifiers.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _serialize_rightslist()

      Provádí operaci serialize rightslist.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _serialize_subjects()

      Provádí operaci serialize subjects.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _serialize_types()

      Provádí operaci serialize types.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _get_formats()

      Vrací formats.

      :return: Načtená data odpovídající zadaným vstupům.


.. py:class:: SamostatnyNalezSerializer

   Implementuje komponentu ``SamostatnyNalezSerializer`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param record: Parametr ``record`` předává se do volání ``__init__()``.

   .. py:method:: _get_creators()

      Vrací creators.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _get_historie_queryset()

      Vrací historie queryset.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: get_ident_cely()

      Vrací ident cely.

      :return: Vrací atribut objektu.

   .. py:method:: _get_soubory_queryset()

      Vrací soubory queryset.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _get_prefix()

      Vrací prefix.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _get_publication_year()

      Vrací publication year.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _get_title()

      Vrací title.

      :param language: Textový název, klíč nebo zpráva ``language`` používaná v rámci operace.
      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _serialize_alternate_identifiers()

      Provádí operaci serialize alternate identifiers.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _serialize_contributors()

      Provádí operaci serialize contributors.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _serialize_creators()

      Provádí operaci serialize creators.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _serialize_dates()

      Provádí operaci serialize dates.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _serialize_descriptions()

      Provádí operaci serialize descriptions.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _serialize_geolocations()

      Provádí operaci serialize geolocations.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _serialize_related_identifiers()

      Provádí operaci serialize related identifiers.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _serialize_rightslist()

      Provádí operaci serialize rightslist.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _serialize_subjects()

      Provádí operaci serialize subjects.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _serialize_types()

      Provádí operaci serialize types.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _get_formats()

      Vrací formats.

      :return: Načtená data odpovídající zadaným vstupům.


.. py:class:: LokalitaSerializer

   Implementuje komponentu ``LokalitaSerializer`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param record: Parametr ``record`` předává se do volání ``__init__()``.

   .. py:method:: _get_creators()

      Vrací creators.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: get_ident_cely()

      Vrací ident cely.

      :return: Vrací atribut objektu.

   .. py:method:: _get_historie_queryset()

      Vrací historie queryset.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _get_prefix()

      Vrací prefix.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _serialize_contributors()

      Provádí operaci serialize contributors.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _get_soubory_queryset()

      Vrací soubory queryset.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _serialize_dates()

      Provádí operaci serialize dates.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _serialize_descriptions()

      Provádí operaci serialize descriptions.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _get_externi_odkaz_query()

      Vrací externi odkaz query.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _serialize_geolocations()

      Provádí operaci serialize geolocations.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _get_publication_year()

      Vrací publication year.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _serialize_rightslist()

      Provádí operaci serialize rightslist.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _get_title()

      Vrací title.

      :param language: Textový název, klíč nebo zpráva ``language`` používaná v rámci operace.
      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _serialize_alternate_identifiers()

      Provádí operaci serialize alternate identifiers.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _serialize_creators()

      Provádí operaci serialize creators.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _serialize_related_identifiers()

      Provádí operaci serialize related identifiers.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _serialize_related_items()

      Provádí operaci serialize related items.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _serialize_subjects()

      Provádí operaci serialize subjects.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _serialize_types()

      Provádí operaci serialize types.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _get_formats()

      Vrací formats.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: serialize_publish()

      Provádí operaci serialize publish.

      :return: Vrací proměnná ``publish``.

   .. py:method:: serialize_update()

      Provádí operaci serialize update.

      :return: Vrací proměnná ``result``.


Funkce
------

.. py:function:: convert_geo_location_to_dict(item)

   Převede geo location to dict.

   :param item: Jedna položka zpracovávané kolekce.
   :return: Výstup funkce odpovídající implementované logice.

.. py:function:: serialize_ez_creator(autor)

   Serializuje osobu jako tvůrce externího zdroje do formátu DataCite.

   :param autor: Osoba vystupující jako autor externího zdroje v systému AMČR.
   :return: Výstup funkce odpovídající implementované logice.

.. py:function:: serialize_ez_contributor(contributor)

   Serializuje osobu jako přispěvatele (editora) externího zdroje do formátu DataCite.

   :param contributor: Osoba vystupující jako editor externího zdroje v systému AMČR.
   :return: Výstup funkce odpovídající implementované logice.

.. py:function:: serialize_geom(geom, katastr, verejne)

   Serializuje geometrii a katastr do formátu geoLocationPoint/geoLocationPlace pro DataCite metadata.

   :param geom: Geometrie záznamu (bod nebo polygon), z níž se použije centroid; ``None`` přeskočí souřadnice.
   :param katastr: Katastrální území záznamu použité pro textový popis polohy; ``None`` přeskočí lokalitu.
   :param verejne: Příznak, zda má být záznam zobrazen veřejně — ovlivňuje úroveň detailu souřadnic.
   :return: Výstup funkce odpovídající implementované logice.

.. py:function:: serialize_affiliation(organizace)

   Serializuje organizaci jako institucionální příslušnost osoby do formátu DataCite.

   :param organizace: Organizace AMČR, jejíž název a případný ROR identifikátor budou zahrnuty.

   :return: Vrací proměnná ``serialized_affiliation``.

.. py:function:: serialize_organizace_contributor(organizace, contributor_type)

   Serializuje organizaci jako přispěvatele záznamu do formátu DataCite.

   :param organizace: Organizace AMČR, která má být zahrnuta jako přispěvatel.
   :param contributor_type: Typ přispěvatele dle schématu DataCite (např. ``DataCurator``, ``HostingInstitution``).

   :return: Vrací slovník.

.. py:function:: serialize_osoba_identifiers(osoba)

   Sestaví seznam identifikátorů osoby (AMČR, ORCID, Wikidata) pro DataCite metadata.

   :param osoba: Osoba z číselníku AMČR, jejíž identifikátory mají být zahrnuty.

   :return: Vrací proměnná ``result``.

.. py:function:: serialize_osoba(osoba, organizace, contributor_type)

   Serializuje osobu (autora nebo přispěvatele) do formátu DataCite včetně identifikátorů a příslušnosti.

   :param osoba: Osoba z číselníku AMČR, která má být serializována.
   :param organizace: Organizace, ke které je osoba přiřazena; ``None`` vynechá příslušnost.
   :param contributor_type: Typ přispěvatele dle DataCite; pokud je zadán, bude přidán do výsledku.
   :return: Výstup funkce odpovídající implementované logice.

.. py:function:: serialize_subject(serialized_record, subject_attr, lang)

   Serializuje heslo ze slovníku AMČR jako tematické klíčové slovo pro DataCite metadata.

   :param serialized_record: Heslo ze slovníku AMČR (Heslar), které má být serializováno; ``None`` vrátí prázdnou množinu.
   :param subject_attr: Název atributu objektu ``serialized_record``, jehož hodnota bude použita jako text hesla.
   :param lang: Kód jazyka dle ISO 639-1 pro pole ``lang`` ve výstupu DataCite.

   :return: Vrací výsledek volání ``frozenset()``.

.. py:function:: serialize_subjects_komponenty(komp)

   Sestaví seznam tematických klíčových slov ze všech atributů komponenty (období, areál, aktivity, objekty, předměty).

   :param komp: Komponenta dokumentační jednotky nebo části dokumentu v systému AMČR.

   :return: Vrací proměnná ``result``.

.. py:function:: serialize_dates_coverage(datace)

   Serializuje časové pokrytí komponenty (období) do formátu DataCite date Coverage.

   :param datace: Heslo ze slovníku AMČR reprezentující dataci s vazbou na rozsah let.
   :return: Výstup funkce odpovídající implementované logice.
