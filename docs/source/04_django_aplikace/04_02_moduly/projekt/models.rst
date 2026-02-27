PROJEKT modely
==============

Definice modelů.

Třídy
------

.. py:class:: Projekt

   Databázový model projektu.

   **Metody:**

   .. py:method:: datum_oznameni()

      Provádí operaci datum oznameni.

      :return: Vrací výsledek provedené operace.

   .. py:method:: pristupnost()

      Provádí operaci pristupnost.

      :return: Vrací výsledek provedené operace.

   .. py:method:: get_ident_cely_link()

      Vrací ident cely link.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: save()

      Uloží změny objektu.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      :return: Vrací výsledek provedené operace.

   .. py:method:: send_ep01()

      Odešle ep01.

      :param rep_bin_file: Vstupní hodnota ``rep_bin_file`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: set_vytvoreny()

      Metoda pro nastavení pomocného stavu vytvořený.

   .. py:method:: set_oznameny()

      Metoda pro nastavení stavu oznámený a uložení změny do historie.

   .. py:method:: set_schvaleny()

      Metoda pro nastavení stavu schvýlený a uložení změny do historie.

   .. py:method:: set_zapsany()

      Metoda pro nastavení stavu zapsaný a uložení změny do historie.

   .. py:method:: set_prihlaseny()

      Metoda pro nastavení stavu prihlásený a uložení změny do historie.

   .. py:method:: set_zahajeny_v_terenu()

      Metoda pro nastavení stavu zahájený v terénu a uložení změny do historie.

   .. py:method:: set_ukoncen_v_terenu()

      Metoda pro nastavení stavu ukončený v terénu a uložení změny do historie.

   .. py:method:: set_uzavreny()

      Metoda pro nastavení stavu uzavřený a uložení změny do historie.

   .. py:method:: archive_project_documentation()

      Provádí operaci archive project documentation.

      :return: Vrací výsledek provedené operace.

   .. py:method:: set_archivovany()

      Metoda pro nastavení stavu archivovaný a uložení změny do historie.
      Součásti je archivace dokumentů a odesláni emailu.

   .. py:method:: set_navrzen_ke_zruseni()

      Metoda pro nastavení stavu navržen k zrušení a uložení změny do historie.

   .. py:method:: set_zruseny()

      Metoda pro nastavení stavu zrušený a uložení změny do historie.

   .. py:method:: set_vracen()

      Metoda pro vrácení stavu zpět a uložení změny do historie.

   .. py:method:: set_znovu_zapsan()

      Metoda pro nastavení stavu zapsaný ze stavu zrušen nebo navrh na zrušení a uložení změny do historie.

   .. py:method:: check_pred_archivaci()

      Metoda pro kontrolu prerekvizit před posunem do stavu archivovaný:

      kontrola jako před uzavřením a navíc

      Připojení akce musejí být ve stavu archivovaná.

   .. py:method:: check_pred_navrzeni_k_zruseni()

      Metoda pro kontrolu prerekvizit před posunem do stavu navržen ke zrušení:

      Projekt nesmí mít připojené akce.

   .. py:method:: check_pred_smazanim()

      Metoda pro kontrolu prerekvizit před smazáním projektu:

      Projekt nesmí mít žádnou akci, soubor ani samostatný nález.

   .. py:method:: check_pred_uzavrenim()

      Metoda pro kontrolu prerekvizit před posunem do stavu uzavřený:

      Projekt musí mít alespoň jednu akci, která projde svou kontrolou před odesláním.

   .. py:method:: check_pred_zahajenim_v_terenu()

      Metoda pro kontrolu prerekvizit před posunem do stavu „zahájen v terénu“:

      Projekt musí mít lokalizaci.

   .. py:method:: parse_ident_cely()

      Metoda pro rozdělení identu na region, rok, pořadové číslo a informaci, zda je permanentní.

   .. py:method:: has_oznamovatel()

      Metoda pro kontrolu, jestli má projekt oznamovatele.

   .. py:method:: set_permanent_ident_cely()

      Metoda na nastavení permanentního identu akce z projektu sekvence.

   .. py:method:: _save_document()

      Uloží document.

      :param creator: Vstupní hodnota ``creator`` pro danou operaci.
      :param fedora_transaction: Vstupní hodnota ``fedora_transaction`` pro danou operaci.
      :param user: Vstupní hodnota ``user`` pro danou operaci.
      :param check_duplicate: Vstupní hodnota ``check_duplicate`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: create_cancel_confirmation_document()

      Metoda na vytvoření potvrzení o zrušení oznámení.

   .. py:method:: create_confirmation_document()

      Metoda na vytvoření oznámovací dokumentace.

   .. py:method:: expert_list_can_be_created()

      Provádí operaci expert list can be created.

      :return: Vrací výsledek provedené operace.

   .. py:method:: create_expert_list()

      Vytvoří expert list.

      :param popup_parametry: Vstupní hodnota ``popup_parametry`` pro danou operaci.
      :return: Vrací nově vytvořený výsledek operace.

   .. py:method:: should_generate_confirmation_document()

      Provádí operaci should generate confirmation document.

      :return: Vrací výsledek provedené operace.

   .. py:method:: get_absolute_url()

      Vrací absolute url.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: set_pristupnost()

      Nastaví pristupnost.

      :param fixes: Vstupní hodnota ``fixes`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: planovane_zahajeni_str()

      Provádí operaci planovane zahajeni str.

      :return: Vrací výsledek provedené operace.

   .. py:method:: planovane_zahajeni_vypis()

      Provádí operaci planovane zahajeni vypis.

      :return: Vrací výsledek provedené operace.

   .. py:method:: get_permission_object()

      Vrací permission object.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_create_user()

      Vrací create user.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_create_org()

      Vrací create org.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: redis_snapshot_id()

      Provádí operaci redis snapshot id.

      :return: Vrací výsledek provedené operace.

   .. py:method:: generate_redis_snapshot()

      Vygeneruje redis snapshot.

      :return: Vrací nově vytvořený výsledek operace.

   .. py:method:: get_kraje_s_emailem()

      Vrací kraje s emailem.

      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: ProjektKatastr

   Databázový model dalších katastrů projektu.

   **Metody:**

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      :return: Vrací výsledek provedené operace.

