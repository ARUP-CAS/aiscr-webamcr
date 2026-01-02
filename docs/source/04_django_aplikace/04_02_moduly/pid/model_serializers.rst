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

   .. py:method:: get_ident_cely()

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

   .. py:method:: get_ident_cely()


.. py:class:: SamostatnyNalezSerializer

   Popis není k dispozici.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: get_ident_cely()


.. py:class:: LokalitaSerializer

   Popis není k dispozici.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: get_ident_cely()

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
