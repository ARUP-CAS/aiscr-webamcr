ARCH_Z modely
=============

Definice modelů.

Třídy
------

.. py:class:: ArcheologickyZaznam

   Class pro db model archeologicky_zaznam.

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

      Metoda na kontrolu prerekvizit pred posunem do stavu odeslaný:

      polia: datum_zahajeni, datum_ukonceni, lokalizace_okolnosti, specifikace_data, hlavni_katastr, hlavni_vedouci a hlavni_typ jsou vyplněna.

      Akce má připojený dokument typu nálezová správa nebo je akce typu nz.

      Je připojená aspoň jedna dokumentační jednotka se všemi relevantními relacemi.

   .. py:method:: check_pred_archivaci()

      Metoda na kontrolu prerekvizit pred archivací:

      kontrola jako před odesláním a navíc

      všechny pripojené dokumenty jsou archivované.

      všechny DJ mají potvrzený pian

   .. py:method:: set_lokalita_permanent_ident_cely()

      Metoda pro nastavení permanentního ident celý pro lokality z lokality sekvence.

   .. py:method:: _set_connected_records_ident()

   .. py:method:: set_akce_ident()

      Metoda pro nastavení ident celý pro akci a její relace.
      Nastaví ident z předaného argumentu ident nebo z metody get_akce_ident.

   .. py:method:: get_absolute_url()

      Metoda pro získaní absolut url záznamu podle typu arch záznamu a argumentu dj_ident_cely.

   .. py:method:: get_redirect()

      Metoda pro získaní redirect záznamu podle typu arch záznamu a argumentu dj_ident_cely.

   .. py:method:: __str__()

      Metoda vráti jako str reprezentaci modelu ident_cely.

   .. py:method:: get_permission_object()

   .. py:method:: get_create_user()

   .. py:method:: get_create_org()

   .. py:method:: check_set_permanent_ident()

   .. py:method:: __init__()

   .. py:method:: initial_casti_dokumentu()

   .. py:method:: initial_pristupnost()

   .. py:method:: initial_pristupnost()

   .. py:method:: save()

   .. py:method:: igsn_lokalita_hide()

   .. py:method:: igsn_lokalita_publish()

   .. py:method:: igsn_lokalita_delete()

   .. py:method:: igsn_lokalita_update()


.. py:class:: ArcheologickyZaznamKatastr

   Class pro db model archeologicky_zaznam_katastr, který drží v sobe relace na další katastry arch záznamu.


.. py:class:: Akce

   Class pro db model akce.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: initial_projekt()

   .. py:method:: get_absolute_url()

      Metoda pro získaní absolut url záznamu.

   .. py:method:: vedouci_organizace()

   .. py:method:: vedouci()

   .. py:method:: set_snapshots()

   .. py:method:: redis_snapshot_id()

   .. py:method:: generate_redis_snapshot()

   .. py:method:: get_by_ident_cely()


.. py:class:: AkceVedouci

   Class pro db model akce_vedouci, který drží v sobe relace na dalších vedoucích arch záznamu.

   **Metody:**

   .. py:method:: __str__()

      Metoda vráti jako str reprezentaci modelu vedouci.

   .. py:method:: vypis_name()

      Metoda vráti jako str reprezentaci modelu vedouci pro vypis.


.. py:class:: ExterniOdkaz

   Class pro db model externi_odkaz, který drží v sobe relace na externí odkazy arch záznamu.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: create_transaction()


.. py:class:: LokalitaSekvence

   Model pro tabulku se sekvencemi lokalit.


.. py:class:: AkceSekvence

   Model pro tabulku se sekvencemi akcií.


Funkce
------

.. py:function:: get_akce_ident(region)

   Metoda pro získaní permanentního ident celý pro akci z akce sekvence.
