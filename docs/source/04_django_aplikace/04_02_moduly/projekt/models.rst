PROJEKT modely
==============

Definice modelů.

Třídy
------

.. py:class:: Projekt

   Class pro db model projekt.

   **Metody:**

   .. py:method:: datum_oznameni()

   .. py:method:: pristupnost()

   .. py:method:: get_ident_cely_link()

   .. py:method:: save()

   .. py:method:: __init__()

   .. py:method:: send_ep01()

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

      Metoda na kontrolu prerekvizit pred posunem do stavu archivovaný:
      
          kontrola jako před uzavřením a navíc
      
          Připojení akce musejí být ve stavu archivovaná.

   .. py:method:: check_pred_navrzeni_k_zruseni()

      Metoda na kontrolu prerekvizit pred posunem do stavu navržen ke zrušení:
      
          Projekt nesmí mít pripojené akce.

   .. py:method:: check_pred_smazanim()

      Metoda na kontrolu prerekvizit pred smazaním projektu:
      
          Projekt nesmí mít žádnou akci, soubor ani samostatný nález.

   .. py:method:: check_pred_uzavrenim()

      Metoda na kontrolu prerekvizit pred posunem do stavu uzavřený:
      
          Projekt musí mít alespoň jednou akci která projde svou kontrolou před odesláním.

   .. py:method:: check_pred_zahajenim_v_terenu()

      Metoda na kontrolu prerekvizit pred posunem do stavu zahájen v terénu:
      
          Projektu musí mít lokalizaci

   .. py:method:: parse_ident_cely()

      Metoda pro rozdelení identu na region, rok, pořadové číslo a jestli je permanentí.

   .. py:method:: has_oznamovatel()

      Metoda na kontrolu jestli má projekt oznamovatele.

   .. py:method:: set_permanent_ident_cely()

      Metoda na nastavení permanentního identu akce z projektu sekvence.

   .. py:method:: create_cancel_confirmation_document()

      Metoda na vytvoření potvrzení o zrušení oznámení.

   .. py:method:: create_confirmation_document()

      Metoda na vytvoření oznámovací dokumentace.

   .. py:method:: expert_list_can_be_created()

   .. py:method:: create_expert_list()

   .. py:method:: should_generate_confirmation_document()

   .. py:method:: get_absolute_url()

   .. py:method:: set_pristupnost()

   .. py:method:: planovane_zahajeni_str()

   .. py:method:: planovane_zahajeni_vypis()

   .. py:method:: get_permission_object()

   .. py:method:: get_create_user()

   .. py:method:: get_create_org()

   .. py:method:: redis_snapshot_id()

   .. py:method:: generate_redis_snapshot()

   .. py:method:: get_kraje_s_emailem()


.. py:class:: ProjektKatastr

   Class pro db model dalších katastru proketu.

   **Metody:**

