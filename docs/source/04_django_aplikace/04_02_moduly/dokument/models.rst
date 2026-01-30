DOKUMENT modely
===============

Definice modelů.

Třídy
------

.. py:class:: Dokument

   Class pro db model dokument.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: __str__()

   .. py:method:: get_absolute_url()

      Metoda pro získaní absolut url záznamu podle typu dokumentu.

   .. py:method:: set_doi()

   .. py:method:: set_zapsany()

      Metoda pro nastavení stavu zapsaný a uložení změny do historie.

   .. py:method:: set_permanent_identificator()

   .. py:method:: set_odeslany()

      Metoda pro nastavení stavu odeslaný a uložení změny do historie.

   .. py:method:: set_archivovany()

      Metoda pro nastavení stavu archivovaný a uložení změny do historie.

   .. py:method:: set_vraceny()

      Metoda pro vrácení o jeden stav méně a uložení změny do historie.

   .. py:method:: check_pred_odeslanim()

      Metoda na kontrolu prerekvizit pred posunem do stavu odeslaný:

      polia: format, popis, duveryhodnost, obdobi, areal jsou vyplněna pro model 3D.

      polia: pristupnost, popis, ulozeni_originalu jsou vyplněna pro model 3D.

      Dokument má aspoň jeden dokument.

   .. py:method:: check_pred_archivaci()

      Metoda na kontrolu prerekvizit pred archivací:

      kontrola jako před odesláním

   .. py:method:: has_extra_data()

      Metoda na zjištení že dokument má extra data.

   .. py:method:: get_komponenta()

      Metoda na získaní všech komponent dokumentu.

   .. py:method:: set_permanent_ident_cely()

      Metoda pro nastavení permanentního ident celý pro dokument.
      Metoda bere pořadoví číslo z db dokument sekvence.
      Metoda zmení i ident připojených souborů.

   .. py:method:: set_datum_zverejneni()

      metoda pro nastavení datumu zvěřejnení.

   .. py:method:: get_permission_object()

   .. py:method:: get_create_user()

   .. py:method:: get_create_org()

   .. py:method:: thumbnail_image()

   .. py:method:: thumbnail_image_file()

   .. py:method:: large_thumbnail()

   .. py:method:: small_thumbnail()

   .. py:method:: set_snapshots()

   .. py:method:: redis_snapshot_id()

   .. py:method:: generate_redis_snapshot()

   .. py:method:: _get_doi_client()

   .. py:method:: doi_exists()

   .. py:method:: doi_delete()

   .. py:method:: doi_hide()

   .. py:method:: doi_publish()

   .. py:method:: doi_update()

   .. py:method:: doi_url()


.. py:class:: DokumentCast

   Class pro db model dokument část.

   **Metody:**

   .. py:method:: get_absolute_url()

      Metoda pro získaní absolut url.

   .. py:method:: get_permission_object()

   .. py:method:: __init__()

   .. py:method:: initial_archeologicky_zaznam()

      Vrátí objekt dokument na základě initial_archeologicky_zaznam_id (lazy-load).

   .. py:method:: initial_projekt()

   .. py:method:: create_transaction()

   .. py:method:: dokument_doi()


.. py:class:: DokumentExtraData

   Class pro db model dokument extra data.


.. py:class:: DokumentAutor

   Class pro db model dokument autori. Obsahuje pořadí.


.. py:class:: DokumentJazyk

   Class pro db model dokument jazyky.

   **Metody:**

   .. py:method:: __str__()


.. py:class:: DokumentOsoba

   Class pro db model dokument osoby.


.. py:class:: DokumentPosudek

   Class pro db model dokument posudky.

   **Metody:**

   .. py:method:: __str__()


.. py:class:: Tvar

   Class pro db model tvary.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: create_transaction()


.. py:class:: DokumentSekvence

   Class pro db model dokument sekvence. Obsahuje sekvenci po roku a řade.


.. py:class:: Let

   Class pro db model let.

   **Metody:**

   .. py:method:: __str__()

   .. py:method:: save()

   .. py:method:: get_absolute_url()


Funkce
------

.. py:function:: get_dokument_soubor_name(dokument, filename, add_to_index)

   Funkce pro získaní správného jména souboru.
