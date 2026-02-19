PID model_serializers
=====================

Modul model_serializers.

Třídy
------

.. py:class:: ModelSerializer

   Popis není k dispozici.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: format_date()

   .. py:method:: format_date_time()

   .. py:method:: _get_creators()

   .. py:method:: _get_historie_queryset()

   .. py:method:: get_ident_cely()

   .. py:method:: _get_publication_year()

   .. py:method:: _get_language()

   .. py:method:: _get_prefix()

   .. py:method:: _get_soubory_queryset()

   .. py:method:: _get_title()

   .. py:method:: _serialize_alternate_identifiers()

   .. py:method:: _serialize_contributors()

   .. py:method:: _serialize_creators()

   .. py:method:: _serialize_dates()

   .. py:method:: _serialize_descriptions()

   .. py:method:: _serialize_geolocations()

   .. py:method:: _serialize_related_identifiers()

   .. py:method:: _serialize_rightslist()

   .. py:method:: _serialize_subjects()

   .. py:method:: _serialize_types()

   .. py:method:: _get_formats()

   .. py:method:: serialize_delete()

   .. py:method:: serialize_hide()

   .. py:method:: serialize_publish()

   .. py:method:: serialize_update()


.. py:class:: PartialSerializer

   Popis není k dispozici.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: serialize_publish()


.. py:class:: DokumentSerializer

   Popis není k dispozici.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: _get_creators()

   .. py:method:: _get_historie_queryset()

   .. py:method:: get_ident_cely()

   .. py:method:: _get_language()

   .. py:method:: _get_publication_year()

   .. py:method:: _get_prefix()

   .. py:method:: _get_soubory_queryset()

   .. py:method:: _get_title()

   .. py:method:: _serialize_alternate_identifiers()

   .. py:method:: _serialize_contributors()

   .. py:method:: _serialize_creators()

   .. py:method:: _serialize_dates()

   .. py:method:: _serialize_descriptions()

   .. py:method:: _serialize_geolocations()

   .. py:method:: _serialize_related_identifiers()

   .. py:method:: _serialize_rightslist()

   .. py:method:: _serialize_subjects()

   .. py:method:: _serialize_types()

   .. py:method:: _get_formats()


.. py:class:: SamostatnyNalezSerializer

   Popis není k dispozici.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: _get_creators()

   .. py:method:: _get_historie_queryset()

   .. py:method:: get_ident_cely()

   .. py:method:: _get_soubory_queryset()

   .. py:method:: _get_prefix()

   .. py:method:: _get_publication_year()

   .. py:method:: _get_title()

   .. py:method:: _serialize_alternate_identifiers()

   .. py:method:: _serialize_contributors()

   .. py:method:: _serialize_creators()

   .. py:method:: _serialize_dates()

   .. py:method:: _serialize_descriptions()

   .. py:method:: _serialize_geolocations()

   .. py:method:: _serialize_related_identifiers()

   .. py:method:: _serialize_rightslist()

   .. py:method:: _serialize_subjects()

   .. py:method:: _serialize_types()

   .. py:method:: _get_formats()


.. py:class:: LokalitaSerializer

   Popis není k dispozici.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: _get_creators()

   .. py:method:: get_ident_cely()

   .. py:method:: _get_historie_queryset()

   .. py:method:: _get_prefix()

   .. py:method:: _serialize_contributors()

   .. py:method:: _get_soubory_queryset()

   .. py:method:: _serialize_dates()

   .. py:method:: _serialize_descriptions()

   .. py:method:: _get_externi_odkaz_query()

   .. py:method:: _serialize_geolocations()

   .. py:method:: _get_publication_year()

   .. py:method:: _serialize_rightslist()

   .. py:method:: _get_title()

   .. py:method:: _serialize_alternate_identifiers()

   .. py:method:: _serialize_creators()

   .. py:method:: _serialize_related_identifiers()

   .. py:method:: _serialize_related_items()

   .. py:method:: _serialize_subjects()

   .. py:method:: _serialize_types()

   .. py:method:: _get_formats()

   .. py:method:: serialize_publish()

   .. py:method:: serialize_update()


Funkce
------

.. py:function:: convert_geo_location_to_dict(item)

   Popis není k dispozici.

.. py:function:: serialize_ez_creator(autor)

   Popis není k dispozici.

.. py:function:: serialize_ez_contributor(contributor)

   Popis není k dispozici.

.. py:function:: serialize_geom(geom, katastr, verejne)

   Popis není k dispozici.

.. py:function:: serialize_affiliation(organizace)

   Popis není k dispozici.

.. py:function:: serialize_organizace_contributor(organizace, contributor_type)

   Popis není k dispozici.

.. py:function:: serialize_osoba_identifiers(osoba)

   Popis není k dispozici.

.. py:function:: serialize_osoba(osoba, organizace, contributor_type)

   Popis není k dispozici.

.. py:function:: serialize_subject(serialized_record, subject_attr, lang)

   Popis není k dispozici.

.. py:function:: serialize_subjects_komponenty(komp)

   Popis není k dispozici.

.. py:function:: serialize_dates_coverage(datace)

   Popis není k dispozici.
