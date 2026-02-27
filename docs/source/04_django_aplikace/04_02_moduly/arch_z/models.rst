ARCH_Z modely
=============

Definice modelů.

Třídy
------

.. py:class:: ArcheologickyZaznam

   Databázový model archeologického záznamu.

   **Metody:**

   .. py:method:: set_zapsany()

      Metoda pro nastavení stavu zapsaný a uložení změny do historie.

   .. py:method:: set_odeslany()

      Metoda pro nastavení stavu odeslaný a uložení změny do historie.
      Dokumenty se taky posouvají do stavu odeslaný.
      Externí zdroje se posouvají do stavu zapsaný.

   .. py:method:: set_archivovany()

      Metoda pro nastavení stavu archivovaný a uložení změny do historie.
      Pokud je akce samostatná a má dočasný ident, nastavý se konečný ident.

   .. py:method:: set_vraceny()

      Metoda pro vrácení o jeden stav méně a uložení změny do historie.

   .. py:method:: check_pred_odeslanim()

      Metoda pro kontrolu prerekvizit před posunem do stavu odeslaný:

      polia: datum_zahajeni, datum_ukonceni, lokalizace_okolnosti, specifikace_data, hlavni_katastr, hlavni_vedouci a hlavni_typ jsou vyplněna.

      Akce má připojený dokument typu nálezová správa nebo je akce typu nz.

      Je připojená aspoň jedna dokumentační jednotka se všemi relevantními relacemi.

   .. py:method:: check_pred_archivaci()

      Metoda pro kontrolu prerekvizit před archivací:

      kontrola jako před odesláním a navíc

      všechny pripojené dokumenty jsou archivované.

      všechny DJ mají potvrzený pian

   .. py:method:: set_lokalita_permanent_ident_cely()

      Metoda pro nastavení permanentního identifikátoru lokality ze sekvence lokalit.

   .. py:method:: _set_connected_records_ident()

      Nastaví connected records ident.

      :param new_ident: Vstupní hodnota ``new_ident`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: set_akce_ident()

      Nastaví akce ident.

      :param ident: Vstupní hodnota ``ident`` pro danou operaci.
      :param delete_container: Vstupní hodnota ``delete_container`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get_absolute_url()

      Metoda pro získaní absolut url záznamu podle typu arch záznamu a argumentu dj_ident_cely.

   .. py:method:: get_redirect()

      Metoda pro získaní redirect záznamu podle typu arch záznamu a argumentu dj_ident_cely.

   .. py:method:: __str__()

      Metoda vrátí str reprezentaci modelu ident_cely.

   .. py:method:: get_permission_object()

      Vrací permission object.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_create_user()

      Vrací create user.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_create_org()

      Vrací create org.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: check_set_permanent_ident()

      Ověří set permanent ident.

      :return: Vrací výsledek ověření nebo validačního pravidla.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: initial_casti_dokumentu()

      Provádí operaci initial casti dokumentu.

      :return: Vrací výsledek provedené operace.

   .. py:method:: initial_pristupnost()

      Provádí operaci initial pristupnost.

      :return: Vrací výsledek provedené operace.

   .. py:method:: initial_pristupnost()

      Provádí operaci initial pristupnost.

      :param value: Vstupní hodnota ``value`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: save()

      Uloží změny objektu.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.

   .. py:method:: igsn_lokalita_hide()

      Provádí operaci igsn lokalita hide.

      :param check_status: Vstupní hodnota ``check_status`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: igsn_lokalita_publish()

      Provádí operaci igsn lokalita publish.

      :param check_status: Vstupní hodnota ``check_status`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: igsn_lokalita_delete()

      Provádí operaci igsn lokalita delete.

      :param check_status: Vstupní hodnota ``check_status`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: igsn_lokalita_update()

      Provádí operaci igsn lokalita update.

      :param check_status: Vstupní hodnota ``check_status`` pro danou operaci.
      :param reload_record: Vstupní hodnota ``reload_record`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: ArcheologickyZaznamKatastr

   Databázový model vazeb archeologického záznamu na další katastry.


.. py:class:: Akce

   Databázový model akce.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: initial_projekt()

      Provádí operaci initial projekt.

      :return: Vrací výsledek provedené operace.

   .. py:method:: get_absolute_url()

      Metoda pro získaní absolut url záznamu.

   .. py:method:: vedouci_organizace()

      Provádí operaci vedouci organizace.

      :return: Vrací výsledek provedené operace.

   .. py:method:: vedouci()

      Provádí operaci vedouci.

      :return: Vrací výsledek provedené operace.

   .. py:method:: set_snapshots()

      Nastaví snapshots.

      :return: Vrací výsledek provedené operace.

   .. py:method:: redis_snapshot_id()

      Provádí operaci redis snapshot id.

      :return: Vrací výsledek provedené operace.

   .. py:method:: generate_redis_snapshot()

      Vygeneruje redis snapshot.

      :return: Vrací nově vytvořený výsledek operace.

   .. py:method:: get_by_ident_cely()

      Vrací by ident cely.

      :param ident_cely: Vstupní hodnota ``ident_cely`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: AkceVedouci

   Databázový model vazeb na další vedoucí archeologického záznamu.

   **Metody:**

   .. py:method:: __str__()

      Metoda vrátí str reprezentaci modelu vedouci.

   .. py:method:: vypis_name()

      Metoda vrátí str reprezentaci modelu vedouci pro vypis.


.. py:class:: ExterniOdkaz

   Databázový model externích odkazů archeologického záznamu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: create_transaction()

      Vytvoří transaction.

      :param transaction_user: Vstupní hodnota ``transaction_user`` pro danou operaci.
      :return: Vrací nově vytvořený výsledek operace.


.. py:class:: LokalitaSekvence

   Model pro tabulku se sekvencemi lokalit.


.. py:class:: AkceSekvence

   Model pro tabulku se sekvencemi akcií.


Funkce
------

.. py:function:: get_akce_ident(region)

   Metoda pro získání permanentního identifikátoru akce ze sekvence akcí.
