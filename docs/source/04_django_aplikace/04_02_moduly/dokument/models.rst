DOKUMENT modely
===============

Definice modelů.

Třídy
------

.. py:class:: Dokument

   Databázový model dokumentu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.


   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

      **Návratová hodnota:**

      Vrací atribut objektu.


   .. py:method:: get_absolute_url()

      Metoda pro získaní absolut url záznamu podle typu dokumentu.

      **Návratová hodnota:**

      Vrací výsledek volání ``reverse()``.


   .. py:method:: set_doi()

      Nastaví doi. v aplikaci.

   .. py:method:: set_zapsany()

      Metoda pro nastavení stavu zapsaný a uložení změny do historie.

      **Parametry:**

      - ``user``: Parametr ``user`` se předává do volání ``Historie()``.


   .. py:method:: set_permanent_identificator()

      Nastaví permanent identificator.

      **Parametry:**

      - ``dokument``: Parametr ``dokument`` předává se do volání ``get_dokument_rada()``, ``set_permanent_ident_cely()``, pracuje se s atributy ``ident_cely``, ``typ_dokumentu``.
      - ``request``: Parametr ``request`` předává se do volání ``add_message()``.
      - ``messages``: Parametr ``messages`` předává se do volání ``add_message()``, pracuje se s atributy ``add_message``, ``SUCCESS``.
      - ``fedora_transaction``: Parametr ``fedora_transaction`` pracuje se s atributy ``rollback_transaction``.

      **Návratová hodnota:**

      Vrací hodnotu typu ``Optional[JsonResponse]`` (výsledek volání ``JsonResponse()``).

      Výsledek provedené změny nad cílovým objektem.

   .. py:method:: set_odeslany()

      Metoda pro nastavení stavu odeslaný a uložení změny do historie.

      **Parametry:**

      - ``user``: Parametr ``user`` se předává do volání ``Historie()``.
      - ``old_ident``: Identifikátor ``old_ident`` používaný pro dohledání cílového záznamu.


   .. py:method:: set_archivovany()

      Metoda pro nastavení stavu archivovaný a uložení změny do historie.

      **Parametry:**

      - ``user``: Parametr ``user`` se předává do volání ``Historie()``.
      - ``old_ident``: Identifikátor ``old_ident`` používaný pro dohledání cílového záznamu.


   .. py:method:: set_vraceny()

      Metoda pro vrácení o jeden stav méně a uložení změny do historie.

      **Parametry:**

      - ``user``: Parametr ``user`` se předává do volání ``Historie()``.
      - ``new_state``: Stavová nebo časová hodnota `new_state` používaná při rozhodování logiky.
      - ``poznamka``: Parametr ``poznamka`` se předává do volání ``Historie()``.


   .. py:method:: check_pred_odeslanim()

      Metoda na kontrolu prerekvizit pred posunem do stavu odeslaný:

      polia: format, popis, duveryhodnost, obdobi, areal jsou vyplněna pro model 3D.

      polia: pristupnost, popis, ulozeni_originalu jsou vyplněna pro model 3D.

      Dokument má aspoň jeden dokument.

      **Návratová hodnota:**

      Vrací proměnná ``result``.


   .. py:method:: check_pred_archivaci()

      Metoda na kontrolu prerekvizit pred archivací:

      kontrola jako před odesláním

      **Návratová hodnota:**

      Vrací proměnná ``result``.


   .. py:method:: has_extra_data()

      Metoda na zjištení že dokument má extra data.

      **Návratová hodnota:**

      Vrací proměnná ``has_extra_data``.


   .. py:method:: get_komponenta()

      Metoda na získaní všech komponent dokumentu.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: vybranou hodnotu z kolekce, None.

      **Výjimky:**

      - ``UnexpectedDataRelations``: Vyvolá se s textem "Neleze ziskat komponentu modelu 3D.".


   .. py:method:: set_permanent_ident_cely()

      Metoda pro nastavení permanentního ident celý pro dokument.

      Metoda bere pořadoví číslo z db dokument sekvence.
      Metoda zmení i ident připojených souborů.

      **Parametry:**

      - ``region``: Parametr ``region`` se předává do volání ``get()``, ``create()``.
      - ``rada``: Parametr ``rada`` se předává do volání ``get()``, ``create()``, pracuje se s atributy ``zkratka``.

      **Výjimky:**

      - ``MaximalIdentNumberError``: Vyvolá se při splnění podmínky ``sequence.sekvence >= MAXIMUM``; nebo při splnění podmínky ``missing[0] >= MAXIMUM``.


   .. py:method:: set_datum_zverejneni()

      metoda pro nastavení datumu zvěřejnení.

   .. py:method:: get_permission_object()

      Vrací permission object.

      **Návratová hodnota:**

      Vrací proměnná ``self``.


   .. py:method:: get_create_user()

      Vrací create user.

      **Návratová hodnota:**

      Vrací n-tici.


   .. py:method:: get_create_org()

      Vrací create org.

      **Návratová hodnota:**

      Vrací n-tici.


   .. py:method:: thumbnail_image()

      Vrací ID prvního souboru jako náhled.

      **Návratová hodnota:**

      ID prvního souboru nebo None.


   .. py:method:: thumbnail_image_file()

      Vrací první soubor jako náhled (seřazeny abecedně).

      **Návratová hodnota:**

      První seřazený soubor nebo None.


   .. py:method:: large_thumbnail()

      Vrací velký náhled prvního souboru.

      **Návratová hodnota:**

      URL velkého náhledu nebo None.


   .. py:method:: small_thumbnail()

      Vrací malý náhled prvního souboru.

      **Návratová hodnota:**

      URL malého náhledu nebo None.


   .. py:method:: set_snapshots()

      Nastaví snapshots. v aplikaci.

   .. py:method:: redis_snapshot_id()

      Generuje klíč pro uložení snapshotu seznamu dokumentů v Redisu.

      **Návratová hodnota:**

      Klíč Redis snapshot (3D nebo běžný dokument).


   .. py:method:: generate_redis_snapshot()

      Vygeneruje redis snapshot.

      **Návratová hodnota:**

      Vrací n-tici.


   .. py:method:: _get_doi_client()

      Vrací doi client.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: doi_exists()

      Zjistí, zda existuje DOI záznam.

      **Návratová hodnota:**

      Vrací výsledek volání ``check_record_exists()``.


   .. py:method:: doi_delete()

      Odstraní DOI záznam z registru.

      **Parametry:**

      - ``check_status``: Zda ověřit status odpovědi serveru.

      **Návratová hodnota:**

      Vrací výsledek volání ``delete_record()``.


   .. py:method:: doi_hide()

      Skryje DOI záznam v registru bez odstranění.

      **Parametry:**

      - ``check_status``: Zda ověřit status odpovědi serveru.

      **Návratová hodnota:**

      Vrací výsledek volání ``hide_record()``.


   .. py:method:: doi_publish()

      Publikuje DOI záznam v registru.

      **Parametry:**

      - ``check_status``: Zda ověřit status odpovědi serveru.

      **Návratová hodnota:**

      Vrací výsledek volání ``publish_record()``.


   .. py:method:: doi_update()

      Aktualizuje DOI metadata v registru.

      **Parametry:**

      - ``check_status``: Zda ověřit status odpovědi serveru.
      - ``reload_record``: Zda znovu načíst data záznamu po aktualizaci.

      **Návratová hodnota:**

      Vrací výsledek volání ``update_record()``.


   .. py:method:: doi_url()

      Vrací URL adresu DOI záznamu.

      **Návratová hodnota:**

      Vrací výsledek volání ``get_record_url()``.



.. py:class:: DokumentCast

   Databázový model části dokumentu.

   **Metody:**

   .. py:method:: get_absolute_url()

      Metoda pro získaní absolut url.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``get_absolute_url()``, výsledek volání ``reverse()``.


   .. py:method:: get_permission_object()

      Vrací permission object.

      **Návratová hodnota:**

      Vrací výsledek volání ``get_permission_object()``.


   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.


   .. py:method:: initial_archeologicky_zaznam()

      Vrátí objekt dokument na základě initial_archeologicky_zaznam_id (líné načtení).

      **Návratová hodnota:**

      Vrací výsledek operace.


   .. py:method:: initial_projekt()

      Vrací projekt předaný při vytvoření součásti, pokud je dostupný.

      **Návratová hodnota:**

      Projekt instance nebo None.


   .. py:method:: create_transaction()

      Vytvoří transaction. v aplikaci.

      **Parametry:**

      - ``transaction_user``: Uživatel nebo osoba ``transaction_user``, v jejímž kontextu se operace provádí.
      - ``success_message``: Parametr ``success_message`` předává se do volání ``FedoraTransaction()``.
      - ``error_message``: Parametr ``error_message`` předává se do volání ``FedoraTransaction()``.

      **Návratová hodnota:**

      Vrací atribut objektu.


   .. py:method:: dokument_doi()

      Vrací DOI identifikátor nadřazeného dokumentu.

      **Návratová hodnota:**

      DOI řetězec nebo None.



.. py:class:: DokumentExtraData

   Databázový model doplňkových dat dokumentu.


.. py:class:: DokumentAutor

   Databázový model autorů dokumentu (včetně pořadí).


.. py:class:: DokumentJazyk

   Databázový model jazyků dokumentu.

   **Metody:**

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování.



.. py:class:: DokumentOsoba

   Databázový model osob dokumentu.


.. py:class:: DokumentPosudek

   Databázový model posudků dokumentu.

   **Metody:**

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování.



.. py:class:: Tvar

   Databázový model tvarů.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.


   .. py:method:: create_transaction()

      Vytvoří transaction. v aplikaci.

      **Parametry:**

      - ``transaction_user``: Uživatel nebo osoba ``transaction_user``, v jejímž kontextu se operace provádí.
      - ``success_message``: Parametr ``success_message`` předává se do volání ``FedoraTransaction()``.
      - ``error_message``: Parametr ``error_message`` předává se do volání ``FedoraTransaction()``.

      **Návratová hodnota:**

      Vrací atribut objektu.



.. py:class:: DokumentSekvence

   Databázový model sekvence dokumentu podle roku a řady.


.. py:class:: Let

   Databázový model letu.

   **Metody:**

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

      **Návratová hodnota:**

      Vrací atribut objektu.


   .. py:method:: save()

      Uloží změny objektu.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``save()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``save()``.

      **Výjimky:**

      - ``ValidationError``: Vyvolá se při splnění podmínky ``not self._state.adding or FedoraRepositoryConnector.check_container_deleted_or_not_exists(self.ident_cely, 'let')``.


   .. py:method:: get_absolute_url()

      Vrací absolute url.

      **Návratová hodnota:**

      Vrací výsledek volání ``reverse()``.



Funkce
------

.. py:function:: get_dokument_soubor_name(dokument, filename, add_to_index)

   Funkce pro získaní správného jména souboru.

   **Parametry:**

   - ``dokument``: Parametr ``dokument`` předává se do volání ``debug()``, ``filter()``, pracuje se s atributy ``ident_cely``, ``soubory``, vstupuje do návratové hodnoty.
   - ``filename``: Parametr ``filename`` se předává do volání ``splitext()``, vstupuje do návratové hodnoty.
   - ``add_to_index``: Číselná hodnota ``add_to_index`` použitá při výpočtu nebo transformaci.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: hodnotu podle větve zpracování, bool.

