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

      **Návratová hodnota:**

      Vrací atribut objektu.


   .. py:method:: pristupnost()

      Provádí operaci pristupnost.

      **Návratová hodnota:**

      Vrací atribut objektu.


   .. py:method:: get_ident_cely_link()

      Vrací ident cely link.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování.


   .. py:method:: save()

      Uloží změny objektu.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``save()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``save()``.


   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.


   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: atribut objektu, str.


   .. py:method:: send_ep01()

      Odešle ep01. v aplikaci.

      **Parametry:**

      - ``rep_bin_file``: Parametr ``rep_bin_file`` se předává do volání ``debug()``, ``send_ep01a()``.


   .. py:method:: set_vytvoreny()

      Metoda pro nastavení pomocného stavu vytvořený.

   .. py:method:: set_oznameny()

      Metoda pro nastavení stavu oznámený a uložení změny do historie.

   .. py:method:: set_schvaleny()

      Metoda pro nastavení stavu schvýlený a uložení změny do historie.

      **Parametry:**

      - ``user``: Parametr ``user`` se předává do volání ``Historie()``.
      - ``old_ident``: Identifikátor ``old_ident`` používaný pro dohledání cílového záznamu.


   .. py:method:: set_zapsany()

      Metoda pro nastavení stavu zapsaný a uložení změny do historie.

      **Parametry:**

      - ``user``: Parametr ``user`` se předává do volání ``Historie()``.


   .. py:method:: set_prihlaseny()

      Metoda pro nastavení stavu prihlásený a uložení změny do historie.

      **Parametry:**

      - ``user``: Parametr ``user`` se předává do volání ``Historie()``.


   .. py:method:: set_zahajeny_v_terenu()

      Metoda pro nastavení stavu zahájený v terénu a uložení změny do historie.

      **Parametry:**

      - ``user``: Parametr ``user`` se předává do volání ``Historie()``.
      - ``info_text``: Číselná hodnota ``info_text`` použitá při výpočtu nebo transformaci.


   .. py:method:: set_ukoncen_v_terenu()

      Metoda pro nastavení stavu ukončený v terénu a uložení změny do historie.

      **Parametry:**

      - ``user``: Parametr ``user`` se předává do volání ``Historie()``.
      - ``info_text``: Číselná hodnota ``info_text`` použitá při výpočtu nebo transformaci.


   .. py:method:: set_uzavreny()

      Metoda pro nastavení stavu uzavřený a uložení změny do historie.

      **Parametry:**

      - ``user``: Parametr ``user`` se předává do volání ``Historie()``.


   .. py:method:: archive_project_documentation()

      Provádí operaci archive project documentation.

   .. py:method:: set_archivovany()

      Metoda pro nastavení stavu archivovaný a uložení změny do historie.

      Součásti je archivace dokumentů a odesláni emailu.

      **Parametry:**

      - ``user``: Parametr ``user`` se předává do volání ``Historie()``, ``send_ea01()``.


   .. py:method:: set_navrzen_ke_zruseni()

      Metoda pro nastavení stavu navržen k zrušení a uložení změny do historie.

      **Parametry:**

      - ``user``: Parametr ``user`` se předává do volání ``Historie()``.
      - ``poznamka``: Parametr ``poznamka`` se předává do volání ``Historie()``.


   .. py:method:: set_zruseny()

      Metoda pro nastavení stavu zrušený a uložení změny do historie.

      **Parametry:**

      - ``user``: Parametr ``user`` se předává do volání ``Historie()``.
      - ``poznamka``: Parametr ``poznamka`` se předává do volání ``Historie()``.
      - ``typ_zmeny``: Parametr ``typ_zmeny`` předává se do volání ``Historie()``.


   .. py:method:: set_vracen()

      Metoda pro vrácení stavu zpět a uložení změny do historie.

      **Parametry:**

      - ``user``: Parametr ``user`` se předává do volání ``Historie()``.
      - ``new_state``: Stavová nebo časová hodnota `new_state` používaná při rozhodování logiky.
      - ``poznamka``: Parametr ``poznamka`` se předává do volání ``Historie()``.


   .. py:method:: set_znovu_zapsan()

      Metoda pro nastavení stavu zapsaný ze stavu zrušen nebo navrh na zrušení a uložení změny do historie.

      **Parametry:**

      - ``user``: Parametr ``user`` se předává do volání ``Historie()``.
      - ``poznamka``: Parametr ``poznamka`` se předává do volání ``Historie()``.


   .. py:method:: check_pred_archivaci()

      Metoda pro kontrolu prerekvizit před posunem do stavu archivovaný:

      kontrola jako před uzavřením a navíc

      Připojení akce musejí být ve stavu archivovaná.

      **Návratová hodnota:**

      Vrací proměnná ``result``.


   .. py:method:: check_pred_navrzeni_k_zruseni()

      Metoda pro kontrolu prerekvizit před posunem do stavu navržen ke zrušení:

      Projekt nesmí mít připojené akce.

      **Návratová hodnota:**

      Vrací slovník.


   .. py:method:: check_pred_smazanim()

      Metoda pro kontrolu prerekvizit před smazáním projektu:

      Projekt nesmí mít žádnou akci, soubor ani samostatný nález.

      **Návratová hodnota:**

      Vrací výsledek operace.


   .. py:method:: check_pred_uzavrenim()

      Metoda pro kontrolu prerekvizit před posunem do stavu uzavřený:

      Projekt musí mít alespoň jednu akci, která projde svou kontrolou před odesláním.

      **Návratová hodnota:**

      Vrací proměnná ``result``.


   .. py:method:: check_pred_zahajenim_v_terenu()

      Metoda pro kontrolu prerekvizit před posunem do stavu „zahájen v terénu“:

      Projekt musí mít lokalizaci.

      **Návratová hodnota:**

      Vrací proměnná ``resp``.


   .. py:method:: parse_ident_cely()

      Metoda pro rozdělení identu na region, rok, pořadové číslo a informaci, zda je permanentní.

      **Návratová hodnota:**

      Vrací n-tici.


   .. py:method:: has_oznamovatel()

      Metoda pro kontrolu, jestli má projekt oznamovatele.

      **Návratová hodnota:**

      Vrací proměnná ``has_oznamovatel``.


   .. py:method:: set_permanent_ident_cely()

      Metoda na nastavení permanentního identu akce z projektu sekvence.

      **Parametry:**

      - ``update_repository``: Časový údaj ``update_repository`` použitý při filtrování nebo výpočtu.

      **Výjimky:**

      - ``MaximalIdentNumberError``: Vyvolá se při splnění podmínky ``sequence.sekvence >= MAXIMUM``; nebo při splnění podmínky ``missing[0] >= MAXIMUM``.
      - ``ValueError``: Vyvolá se s textem "No Fedora transaction".


   .. py:method:: _save_document()

      Uloží document.

      **Parametry:**

      - ``creator``: Parametr ``creator`` pracuje se s atributy ``build_document``.
      - ``fedora_transaction``: Parametr ``fedora_transaction`` předává se do volání ``debug()``, pracuje se s atributy ``uid``.
      - ``user``: Parametr ``user`` se předává do volání ``zaznamenej_nahrani()``, ovlivňuje větvení podmínek.
      - ``check_duplicate``: Parametr ``check_duplicate`` ovlivňuje větvení podmínek.

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice.


   .. py:method:: create_cancel_confirmation_document()

      Metoda na vytvoření potvrzení o zrušení oznámení.

      **Parametry:**

      - ``user``: Parametr ``user`` se předává do volání ``debug()``, ``_save_document()``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací výsledek operace.


   .. py:method:: create_confirmation_document()

      Metoda na vytvoření oznámovací dokumentace.

      **Parametry:**

      - ``fedora_transaction``: Parametr ``fedora_transaction`` předává se do volání ``debug()``, ``OznameniPDFCreator()``, pracuje se s atributy ``uid``, vstupuje do návratové hodnoty.
      - ``additional``: Kolekce nebo datová struktura `additional` zpracovávaná touto funkcí.
      - ``user``: Parametr ``user`` se předává do volání ``debug()``, ``_save_document()``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací výsledek operace.


   .. py:method:: expert_list_can_be_created()

      Provádí operaci expert list can be created.

      **Návratová hodnota:**

      Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.


   .. py:method:: create_expert_list()

      Vytvoří expert list.

      **Parametry:**

      - ``popup_parametry``: Číselná hodnota ``popup_parametry`` použitá při výpočtu nebo transformaci.

      **Návratová hodnota:**

      Vrací proměnná ``output``.


   .. py:method:: should_generate_confirmation_document()

      Provádí operaci should generate confirmation document.

      **Návratová hodnota:**

      Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.


   .. py:method:: get_absolute_url()

      Vrací absolute url.

      **Návratová hodnota:**

      Vrací výsledek volání ``reverse()``.


   .. py:method:: set_pristupnost()

      Nastaví pristupnost. v aplikaci.

      **Parametry:**

      - ``fixes``: Číselná hodnota ``fixes`` použitá při výpočtu nebo transformaci.


   .. py:method:: planovane_zahajeni_str()

      Provádí operaci planovane zahajeni str.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: hodnotu podle větve zpracování, str.


   .. py:method:: planovane_zahajeni_vypis()

      Provádí operaci planovane zahajeni vypis.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: hodnotu podle větve zpracování, str.


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


   .. py:method:: redis_snapshot_id()

      Provádí operaci redis snapshot id.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování.


   .. py:method:: generate_redis_snapshot()

      Vygeneruje redis snapshot.

      **Návratová hodnota:**

      Vrací n-tici.


   .. py:method:: get_kraje_s_emailem()

      Vrací kraje s emailem.

      **Návratová hodnota:**

      Vrací výsledek volání ``exclude()``.



.. py:class:: ProjektKatastr

   Databázový model dalších katastrů projektu.

   **Metody:**

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování.



Funkce
------

.. py:function:: get_show_oznamovatel(projekt, user)

   Vrátí, zda má být sekce oznamovatele zobrazena danému uživateli.

   Implementuje pravidla viditelnosti oznamovatele. Časová kritéria jsou vyhodnocována
   z polí ``projekt.datum_uzavreni`` a ``projekt.datum_prihlaseni``, která jsou udržována
   přímo na modelu (viz ``Projekt.set_uzavreny`` a ``Projekt.set_prihlaseny``).

   **Parametry:**

   - ``projekt``: Instance projektu, pro nějž se oprávnění vyhodnocuje.
   - ``user``: Přihlášený uživatel.

   **Návratová hodnota:**

   ``True``, pokud má být sekce oznamovatele zobrazena, jinak ``False``.

