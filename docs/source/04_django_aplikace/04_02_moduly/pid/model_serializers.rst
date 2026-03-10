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

      :param record: Parametr ``record`` slouží jako vstup pro logiku funkce ``__init__``.

   .. py:method:: format_date()

      Provádí operaci format date.

      :param date: Časový údaj ``date`` použitý při filtrování nebo výpočtu.

      :return: Vrací výsledek volání ``strftime()``.

   .. py:method:: format_date_time()

      Provádí operaci format date time.

      :param date_time: Časový údaj ``date_time`` použitý při filtrování nebo výpočtu.

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

   .. py:method:: serialize_delete()

      Provádí operaci serialize delete.

      :return: Vrací slovník.

   .. py:method:: serialize_hide()

      Provádí operaci serialize hide.

      :return: Vrací slovník.

   .. py:method:: serialize_publish()

      Provádí operaci serialize publish.

      :return: Vrací proměnná ``data``.

   .. py:method:: serialize_update()

      Provádí operaci serialize update.

      :return: Vrací proměnná ``result``.


.. py:class:: PartialSerializer

   Implementuje komponentu ``PartialSerializer`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param record: Parametr ``record`` slouží jako vstup pro logiku funkce ``__init__``.

   .. py:method:: serialize_publish()

      Provádí operaci serialize publish.


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

   Provádí operaci serialize ez creator.

   :param autor: Parametr ``autor`` pracuje se s atributy ``vypis_cely``, ``jmeno``, vstupuje do návratové hodnoty.
   :return: Výstup funkce odpovídající implementované logice.

.. py:function:: serialize_ez_contributor(contributor)

   Provádí operaci serialize ez contributor.

   :param contributor: Parametr ``contributor`` pracuje se s atributy ``vypis_cely``, ``jmeno``, vstupuje do návratové hodnoty.
   :return: Výstup funkce odpovídající implementované logice.

.. py:function:: serialize_geom(geom, katastr, verejne)

   Provádí operaci serialize geom.

   :param geom: Parametr ``geom`` předává se do volání ``update()``, ``frozenset()``, pracuje se s atributy ``centroid``, ovlivňuje větvení podmínek.
   :param katastr: Parametr ``katastr`` pracuje se s atributy ``nazev``, ``okres``, ovlivňuje větvení podmínek.
   :param verejne: Parametr ``verejne`` ovlivňuje větvení podmínek.
   :return: Výstup funkce odpovídající implementované logice.

.. py:function:: serialize_affiliation(organizace)

   Provádí operaci serialize affiliation.

   :param organizace: Uživatel nebo osoba `organizace`, v jejímž kontextu se operace provádí.

   :return: Vrací proměnná ``serialized_affiliation``.

.. py:function:: serialize_organizace_contributor(organizace, contributor_type)

   Provádí operaci serialize organizace contributor.

   :param organizace: Uživatel nebo osoba `organizace`, v jejímž kontextu se operace provádí.
   :param contributor_type: Parametr ``contributor_type`` vstupuje do návratové hodnoty.

   :return: Vrací slovník.

.. py:function:: serialize_osoba_identifiers(osoba)

   Provádí operaci serialize osoba identifiers.

   :param osoba: Uživatel nebo osoba ``osoba``, v jejímž kontextu se operace provádí.

   :return: Vrací proměnná ``result``.

.. py:function:: serialize_osoba(osoba, organizace, contributor_type)

   Provádí operaci serialize osoba.

   :param osoba: Uživatel nebo osoba ``osoba``, v jejímž kontextu se operace provádí.
   :param organizace: Uživatel nebo osoba `organizace`, v jejímž kontextu se operace provádí.
   :param contributor_type: Parametr ``contributor_type`` ovlivňuje větvení podmínek.
   :return: Výstup funkce odpovídající implementované logice.

.. py:function:: serialize_subject(serialized_record, subject_attr, lang)

   Provádí operaci serialize subject.

   :param serialized_record: Parametr ``serialized_record`` předává se do volání ``getattr()``, pracuje se s atributy ``ident_cely``, ovlivňuje větvení podmínek.
   :param subject_attr: Textový nebo strukturální vstup `subject_attr` používaný při sestavení nebo zpracování obsahu.
   :param lang: Textová hodnota `lang` používaná pro vyhledání, pojmenování nebo hlášení stavu.

   :return: Vrací výsledek volání ``frozenset()``.

.. py:function:: serialize_subjects_komponenty(komp)

   Provádí operaci serialize subjects komponenty.

   :param komp: Komponenta nebo její serializovaný reprezentant.

   :return: Vrací proměnná ``result``.

.. py:function:: serialize_dates_coverage(datace)

   Provádí operaci serialize dates coverage.

   :param datace: Kolekce ``datace`` zpracovávaná touto funkcí.
   :return: Výstup funkce odpovídající implementované logice.
