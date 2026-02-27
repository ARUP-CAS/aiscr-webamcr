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

      :param record: Vstupní hodnota ``record`` pro danou operaci.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: format_date()

      Provádí operaci format date.

      :param date: Vstupní hodnota ``date`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: format_date_time()

      Provádí operaci format date time.

      :param date_time: Vstupní hodnota ``date_time`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: _get_creators()

      Vrací creators.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _get_historie_queryset()

      Vrací historie queryset.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_ident_cely()

      Vrací ident cely.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _get_publication_year()

      Vrací publication year.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _get_language()

      Vrací language.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _get_prefix()

      Vrací prefix.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _get_soubory_queryset()

      Vrací soubory queryset.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _get_title()

      Vrací title.

      :param language: Vstupní hodnota ``language`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _serialize_alternate_identifiers()

      Provádí operaci serialize alternate identifiers.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _serialize_contributors()

      Provádí operaci serialize contributors.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _serialize_creators()

      Provádí operaci serialize creators.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _serialize_dates()

      Provádí operaci serialize dates.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _serialize_descriptions()

      Provádí operaci serialize descriptions.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _serialize_geolocations()

      Provádí operaci serialize geolocations.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _serialize_related_identifiers()

      Provádí operaci serialize related identifiers.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _serialize_rightslist()

      Provádí operaci serialize rightslist.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _serialize_subjects()

      Provádí operaci serialize subjects.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _serialize_types()

      Provádí operaci serialize types.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _get_formats()

      Vrací formats.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: serialize_delete()

      Provádí operaci serialize delete.

      :return: Vrací výsledek provedené operace.

   .. py:method:: serialize_hide()

      Provádí operaci serialize hide.

      :return: Vrací výsledek provedené operace.

   .. py:method:: serialize_publish()

      Provádí operaci serialize publish.

      :return: Vrací výsledek provedené operace.

   .. py:method:: serialize_update()

      Provádí operaci serialize update.

      :return: Vrací výsledek provedené operace.


.. py:class:: PartialSerializer

   Implementuje komponentu ``PartialSerializer`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param record: Vstupní hodnota ``record`` pro danou operaci.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: serialize_publish()

      Provádí operaci serialize publish.

      :return: Vrací výsledek provedené operace.


.. py:class:: DokumentSerializer

   Implementuje komponentu ``DokumentSerializer`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param record: Vstupní hodnota ``record`` pro danou operaci.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: _get_creators()

      Vrací creators.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _get_historie_queryset()

      Vrací historie queryset.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_ident_cely()

      Vrací ident cely.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _get_language()

      Vrací language.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _get_publication_year()

      Vrací publication year.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _get_prefix()

      Vrací prefix.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _get_soubory_queryset()

      Vrací soubory queryset.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _get_title()

      Vrací title.

      :param language: Vstupní hodnota ``language`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _serialize_alternate_identifiers()

      Provádí operaci serialize alternate identifiers.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _serialize_contributors()

      Provádí operaci serialize contributors.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _serialize_creators()

      Provádí operaci serialize creators.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _serialize_dates()

      Provádí operaci serialize dates.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _serialize_descriptions()

      Provádí operaci serialize descriptions.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _serialize_geolocations()

      Provádí operaci serialize geolocations.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _serialize_related_identifiers()

      Provádí operaci serialize related identifiers.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _serialize_rightslist()

      Provádí operaci serialize rightslist.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _serialize_subjects()

      Provádí operaci serialize subjects.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _serialize_types()

      Provádí operaci serialize types.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _get_formats()

      Vrací formats.

      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: SamostatnyNalezSerializer

   Implementuje komponentu ``SamostatnyNalezSerializer`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param record: Vstupní hodnota ``record`` pro danou operaci.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: _get_creators()

      Vrací creators.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _get_historie_queryset()

      Vrací historie queryset.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_ident_cely()

      Vrací ident cely.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _get_soubory_queryset()

      Vrací soubory queryset.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _get_prefix()

      Vrací prefix.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _get_publication_year()

      Vrací publication year.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _get_title()

      Vrací title.

      :param language: Vstupní hodnota ``language`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _serialize_alternate_identifiers()

      Provádí operaci serialize alternate identifiers.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _serialize_contributors()

      Provádí operaci serialize contributors.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _serialize_creators()

      Provádí operaci serialize creators.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _serialize_dates()

      Provádí operaci serialize dates.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _serialize_descriptions()

      Provádí operaci serialize descriptions.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _serialize_geolocations()

      Provádí operaci serialize geolocations.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _serialize_related_identifiers()

      Provádí operaci serialize related identifiers.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _serialize_rightslist()

      Provádí operaci serialize rightslist.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _serialize_subjects()

      Provádí operaci serialize subjects.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _serialize_types()

      Provádí operaci serialize types.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _get_formats()

      Vrací formats.

      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: LokalitaSerializer

   Implementuje komponentu ``LokalitaSerializer`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param record: Vstupní hodnota ``record`` pro danou operaci.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: _get_creators()

      Vrací creators.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_ident_cely()

      Vrací ident cely.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _get_historie_queryset()

      Vrací historie queryset.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _get_prefix()

      Vrací prefix.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _serialize_contributors()

      Provádí operaci serialize contributors.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _get_soubory_queryset()

      Vrací soubory queryset.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _serialize_dates()

      Provádí operaci serialize dates.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _serialize_descriptions()

      Provádí operaci serialize descriptions.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _get_externi_odkaz_query()

      Vrací externi odkaz query.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _serialize_geolocations()

      Provádí operaci serialize geolocations.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _get_publication_year()

      Vrací publication year.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _serialize_rightslist()

      Provádí operaci serialize rightslist.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _get_title()

      Vrací title.

      :param language: Vstupní hodnota ``language`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _serialize_alternate_identifiers()

      Provádí operaci serialize alternate identifiers.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _serialize_creators()

      Provádí operaci serialize creators.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _serialize_related_identifiers()

      Provádí operaci serialize related identifiers.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _serialize_related_items()

      Provádí operaci serialize related items.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _serialize_subjects()

      Provádí operaci serialize subjects.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _serialize_types()

      Provádí operaci serialize types.

      :return: Vrací výsledek provedené operace.

   .. py:method:: _get_formats()

      Vrací formats.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: serialize_publish()

      Provádí operaci serialize publish.

      :return: Vrací výsledek provedené operace.

   .. py:method:: serialize_update()

      Provádí operaci serialize update.

      :return: Vrací výsledek provedené operace.


Funkce
------

.. py:function:: convert_geo_location_to_dict(item)

   Převede geo location to dict.

   :param item: Vstupní hodnota ``item`` pro danou operaci.
   :return: Vrací výsledek provedené operace.

.. py:function:: serialize_ez_creator(autor)

   Provádí operaci serialize ez creator.

   :param autor: Vstupní hodnota ``autor`` pro danou operaci.
   :return: Vrací výsledek provedené operace.

.. py:function:: serialize_ez_contributor(contributor)

   Provádí operaci serialize ez contributor.

   :param contributor: Vstupní hodnota ``contributor`` pro danou operaci.
   :return: Vrací výsledek provedené operace.

.. py:function:: serialize_geom(geom, katastr, verejne)

   Provádí operaci serialize geom.

   :param geom: Vstupní hodnota ``geom`` pro danou operaci.
   :param katastr: Vstupní hodnota ``katastr`` pro danou operaci.
   :param verejne: Vstupní hodnota ``verejne`` pro danou operaci.
   :return: Vrací výsledek provedené operace.

.. py:function:: serialize_affiliation(organizace)

   Provádí operaci serialize affiliation.

   :param organizace: Vstupní hodnota ``organizace`` pro danou operaci.
   :return: Vrací výsledek provedené operace.

.. py:function:: serialize_organizace_contributor(organizace, contributor_type)

   Provádí operaci serialize organizace contributor.

   :param organizace: Vstupní hodnota ``organizace`` pro danou operaci.
   :param contributor_type: Vstupní hodnota ``contributor_type`` pro danou operaci.
   :return: Vrací výsledek provedené operace.

.. py:function:: serialize_osoba_identifiers(osoba)

   Provádí operaci serialize osoba identifiers.

   :param osoba: Vstupní hodnota ``osoba`` pro danou operaci.
   :return: Vrací výsledek provedené operace.

.. py:function:: serialize_osoba(osoba, organizace, contributor_type)

   Provádí operaci serialize osoba.

   :param osoba: Vstupní hodnota ``osoba`` pro danou operaci.
   :param organizace: Vstupní hodnota ``organizace`` pro danou operaci.
   :param contributor_type: Vstupní hodnota ``contributor_type`` pro danou operaci.
   :return: Vrací výsledek provedené operace.

.. py:function:: serialize_subject(serialized_record, subject_attr, lang)

   Provádí operaci serialize subject.

   :param serialized_record: Vstupní hodnota ``serialized_record`` pro danou operaci.
   :param subject_attr: Vstupní hodnota ``subject_attr`` pro danou operaci.
   :param lang: Vstupní hodnota ``lang`` pro danou operaci.
   :return: Vrací výsledek provedené operace.

.. py:function:: serialize_subjects_komponenty(komp)

   Provádí operaci serialize subjects komponenty.

   :param komp: Vstupní hodnota ``komp`` pro danou operaci.
   :return: Vrací výsledek provedené operace.

.. py:function:: serialize_dates_coverage(datace)

   Provádí operaci serialize dates coverage.

   :param datace: Vstupní hodnota ``datace`` pro danou operaci.
   :return: Vrací výsledek provedené operace.
