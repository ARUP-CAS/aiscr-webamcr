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

   .. py:method:: pristupnost()

      Provádí operaci pristupnost.

   .. py:method:: get_ident_cely_link()

      Vrací ident cely link.

   .. py:method:: save()

      Uloží změny objektu.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

   .. py:method:: send_ep01()

      Odešle ep01. v aplikaci.

      :param rep_bin_file: Cesta, URL nebo název zdroje ``rep_bin_file``, ze kterého funkce čte nebo kam zapisuje.

   .. py:method:: set_vytvoreny()

      Metoda pro nastavení pomocného stavu vytvořený.

   .. py:method:: set_oznameny()

      Metoda pro nastavení stavu oznámený a uložení změny do historie.

   .. py:method:: set_schvaleny()

      Metoda pro nastavení stavu schvýlený a uložení změny do historie.

      :param user: Uživatel, v jehož kontextu se operace provádí.
      :param old_ident: Identifikátor ``old_ident`` používaný pro dohledání cílového záznamu.

   .. py:method:: set_zapsany()

      Metoda pro nastavení stavu zapsaný a uložení změny do historie.

      :param user: Uživatel, v jehož kontextu se operace provádí.

   .. py:method:: set_prihlaseny()

      Metoda pro nastavení stavu prihlásený a uložení změny do historie.

      :param user: Uživatel, v jehož kontextu se operace provádí.

   .. py:method:: set_zahajeny_v_terenu()

      Metoda pro nastavení stavu zahájený v terénu a uložení změny do historie.

      :param user: Uživatel, v jehož kontextu se operace provádí.
      :param info_text: Číselná hodnota ``info_text`` použitá při výpočtu nebo transformaci.

   .. py:method:: set_ukoncen_v_terenu()

      Metoda pro nastavení stavu ukončený v terénu a uložení změny do historie.

      :param user: Uživatel, v jehož kontextu se operace provádí.
      :param info_text: Číselná hodnota ``info_text`` použitá při výpočtu nebo transformaci.

   .. py:method:: set_uzavreny()

      Metoda pro nastavení stavu uzavřený a uložení změny do historie.

      :param user: Uživatel, v jehož kontextu se operace provádí.

   .. py:method:: archive_project_documentation()

      Provádí operaci archive project documentation.

   .. py:method:: set_archivovany()

      Metoda pro nastavení stavu archivovaný a uložení změny do historie.

      Součásti je archivace dokumentů a odesláni emailu.

      :param user: Uživatel, v jehož kontextu se operace provádí.

   .. py:method:: set_navrzen_ke_zruseni()

      Metoda pro nastavení stavu navržen k zrušení a uložení změny do historie.

      :param user: Uživatel, v jehož kontextu se operace provádí.
      :param poznamka: Číselná nebo geometrická hodnota `poznamka` použitá při výpočtu nebo transformaci.

   .. py:method:: set_zruseny()

      Metoda pro nastavení stavu zrušený a uložení změny do historie.

      :param user: Uživatel, v jehož kontextu se operace provádí.
      :param poznamka: Číselná nebo geometrická hodnota `poznamka` použitá při výpočtu nebo transformaci.
      :param typ_zmeny: Název nebo typ ``typ_zmeny`` používaný pro volbu cílové logiky.

   .. py:method:: set_vracen()

      Metoda pro vrácení stavu zpět a uložení změny do historie.

      :param user: Uživatel, v jehož kontextu se operace provádí.
      :param new_state: Stavová nebo časová hodnota `new_state` používaná při rozhodování logiky.
      :param poznamka: Číselná nebo geometrická hodnota `poznamka` použitá při výpočtu nebo transformaci.

   .. py:method:: set_znovu_zapsan()

      Metoda pro nastavení stavu zapsaný ze stavu zrušen nebo navrh na zrušení a uložení změny do historie.

      :param user: Uživatel, v jehož kontextu se operace provádí.
      :param poznamka: Číselná nebo geometrická hodnota `poznamka` použitá při výpočtu nebo transformaci.

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
      :return: Vrací výsledek operace.

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

      :param update_repository: Časový údaj ``update_repository`` použitý při filtrování nebo výpočtu.

   .. py:method:: _save_document()

      Uloží document.

      :param creator: Číselná nebo geometrická hodnota `creator` použitá při výpočtu nebo transformaci.
      :param fedora_transaction: Příznak ``fedora_transaction`` určující průběh nebo rozsah zpracování.
      :param user: Uživatel, v jehož kontextu se operace provádí.
      :param check_duplicate: Příznak ``check_duplicate`` určující průběh nebo rozsah zpracování.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: create_cancel_confirmation_document()

      Metoda na vytvoření potvrzení o zrušení oznámení.

      :param user: Uživatel, v jehož kontextu se operace provádí.
      :return: Vrací výsledek operace.

   .. py:method:: create_confirmation_document()

      Metoda na vytvoření oznámovací dokumentace.

      :param fedora_transaction: Příznak ``fedora_transaction`` určující průběh nebo rozsah zpracování.
      :param additional: Kolekce nebo datová struktura `additional` zpracovávaná touto funkcí.
      :param user: Uživatel, v jehož kontextu se operace provádí.
      :return: Vrací výsledek operace.

   .. py:method:: expert_list_can_be_created()

      Provádí operaci expert list can be created.

   .. py:method:: create_expert_list()

      Vytvoří expert list.

      :param popup_parametry: Číselná hodnota ``popup_parametry`` použitá při výpočtu nebo transformaci.

   .. py:method:: should_generate_confirmation_document()

      Provádí operaci should generate confirmation document.

   .. py:method:: get_absolute_url()

      Vrací absolute url.

   .. py:method:: set_pristupnost()

      Nastaví pristupnost. v aplikaci.

      :param fixes: Číselná hodnota ``fixes`` použitá při výpočtu nebo transformaci.

   .. py:method:: planovane_zahajeni_str()

      Provádí operaci planovane zahajeni str.

   .. py:method:: planovane_zahajeni_vypis()

      Provádí operaci planovane zahajeni vypis.

   .. py:method:: get_permission_object()

      Vrací permission object.

   .. py:method:: get_create_user()

      Vrací create user.

   .. py:method:: get_create_org()

      Vrací create org.

   .. py:method:: redis_snapshot_id()

      Provádí operaci redis snapshot id.

   .. py:method:: generate_redis_snapshot()

      Vygeneruje redis snapshot.

   .. py:method:: get_kraje_s_emailem()

      Vrací kraje s emailem.


.. py:class:: ProjektKatastr

   Databázový model dalších katastrů projektu.

   **Metody:**

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

