ARCH_Z modely
=============

Definice modelů.

Třídy
------

.. py:class:: ArcheologickyZaznam

   Databázový model archeologického záznamu.

   **Metody:**

   .. py:method:: set_zapsany()

      Přepne archeologický záznam do stavu „zapsaný“ a zapíše změnu do historie.

      **Parametry:**

      - ``user``: Uživatel, který změnu stavu provedl.


   .. py:method:: set_odeslany()

      Přepne záznam do stavu „odeslaný“ a propíše navazující změny do souvisejících dat.

      Metoda zároveň posune navázané dokumenty a externí zdroje do odpovídajících stavů.

      **Parametry:**

      - ``user``: Uživatel, který odeslání provedl.
      - ``request``: HTTP požadavek použitý při generování trvalých identifikátorů dokumentů.
      - ``messages``: Django message backend pro předání uživatelských hlášek.


   .. py:method:: set_archivovany()

      Přepne záznam do stavu „archivovaný“ a zaznamená změnu do historie.

      U samostatné akce s dočasným identifikátorem se při archivaci nastaví trvalý ident.

      **Parametry:**

      - ``user``: Uživatel, který archivaci provedl.


   .. py:method:: set_vraceny()

      Metoda pro vrácení o jeden stav méně a uložení změny do historie.

      **Parametry:**

      - ``user``: Uživatel, který vrácení stavu provedl.
      - ``new_state``: Cílový stav záznamu, do kterého má být záznam vrácen.
      - ``poznamka``: Poznámka uložená do historie k provedenému vrácení.


   .. py:method:: check_pred_odeslanim()

      Metoda pro kontrolu prerekvizit před posunem do stavu odeslaný:

      polia: datum_zahajeni, datum_ukonceni, lokalizace_okolnosti, specifikace_data, hlavni_katastr, hlavni_vedouci a hlavni_typ jsou vyplněna.

      Akce má připojený dokument typu nálezová správa nebo je akce typu nz.

      Je připojená aspoň jedna dokumentační jednotka se všemi relevantními relacemi.

      **Návratová hodnota:**

      Vrací proměnná ``result``.


   .. py:method:: check_pred_archivaci()

      Metoda pro kontrolu prerekvizit před archivací:

      kontrola jako před odesláním a navíc

      všechny pripojené dokumenty jsou archivované.

      všechny DJ mají potvrzený pian

      **Návratová hodnota:**

      Vrací n-tici.


   .. py:method:: set_lokalita_permanent_ident_cely()

      Metoda pro nastavení permanentního identifikátoru lokality ze sekvence lokalit.

      **Výjimky:**

      - ``MaximalIdentNumberError``: Vyvolá se při splnění podmínky ``sequence.sekvence >= MAXIMUM``; nebo při splnění podmínky ``missing[0] >= MAXIMUM``.


   .. py:method:: _set_connected_records_ident()

      Propíše nový základ identifikátoru do navázaných DJ a komponent.

      **Parametry:**

      - ``new_ident``: Nový prefix identifikátoru archeologické akce.


   .. py:method:: set_akce_ident()

      Nastaví nebo vygeneruje identifikátor akce a promítne změnu do navázaných dat.

      **Parametry:**

      - ``ident``: Volitelný identifikátor; pokud není zadán, vygeneruje se nový.
      - ``delete_container``: Určuje, zda se při změně identifikátoru smaže původní kontejner.


   .. py:method:: get_absolute_url()

      Vrátí detail URL archeologického záznamu nebo jeho dokumentační jednotky.

      **Parametry:**

      - ``dj_ident_cely``: Identifikátor dokumentační jednotky pro detail DJ varianty.

      **Návratová hodnota:**

      Vrací výsledek volání ``reverse()``.


   .. py:method:: get_redirect()

      Vrátí redirect odpověď na detail archeologického záznamu.

      **Parametry:**

      - ``dj_ident_cely``: Identifikátor dokumentační jednotky pro detail DJ varianty.

      **Návratová hodnota:**

      Vrací výsledek volání ``redirect()``.


   .. py:method:: __str__()

      Metoda vrátí str reprezentaci modelu ident_cely.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: atribut objektu, str.


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


   .. py:method:: check_set_permanent_ident()

      Ověří set permanent ident.

      **Návratová hodnota:**

      Vrací proměnná ``poznamka_historie``.


   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.


   .. py:method:: initial_casti_dokumentu()

      Vrátí ID navázaných částí dokumentu v okamžiku načtení instance.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``values_list()``, seznam.


   .. py:method:: initial_pristupnost()

      Vrátí původní hodnotu přístupnosti záznamu.

      **Návratová hodnota:**

      Vrací atribut objektu.


   .. py:method:: initial_pristupnost()

      Nastaví interně uloženou původní hodnotu přístupnosti.

      **Parametry:**

      - ``value``: Nová hodnota původní přístupnosti.


   .. py:method:: save()

      Uloží změny objektu.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``save()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``save()``.


   .. py:method:: igsn_lokalita_hide()

      Skryje IGSN záznam lokality, pokud je aktuální záznam typu lokalita.

      **Parametry:**

      - ``check_status``: Při ``True`` ověří stav před provedením změny v IGSN.


   .. py:method:: igsn_lokalita_publish()

      Publikuje IGSN lokality, pokud je záznam lokality archivovaný.

      **Parametry:**

      - ``check_status``: Při ``True`` ověří stav před publikací v IGSN.


   .. py:method:: igsn_lokalita_delete()

      Odstraní IGSN záznam lokality, pokud jde o záznam typu lokalita.

      **Parametry:**

      - ``check_status``: Při ``True`` ověří stav před smazáním v IGSN.


   .. py:method:: igsn_lokalita_update()

      Aktualizuje IGSN metadata lokality, pokud jde o záznam typu lokalita.

      **Parametry:**

      - ``check_status``: Při ``True`` ověří stav před aktualizací v IGSN.
      - ``reload_record``: Určuje, zda se má záznam před aktualizací znovu načíst.



.. py:class:: ArcheologickyZaznamKatastr

   Databázový model vazeb archeologického záznamu na další katastry.


.. py:class:: Akce

   Databázový model akce.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.


   .. py:method:: initial_projekt()

      Vrátí původní projekt navázaný při inicializaci instance.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``get()``, None.


   .. py:method:: get_absolute_url()

      Vrátí URL detailu archeologického záznamu navázaného na akci.

      **Návratová hodnota:**

      Vrací výsledek volání ``reverse()``.


   .. py:method:: vedouci_organizace()

      Vrátí seznam vedoucích organizací akce jako text.

      **Návratová hodnota:**

      Vrací výsledek volání ``join()``.


   .. py:method:: vedouci()

      Vrátí textový seznam vedoucích osob navázaných na akci.

      **Návratová hodnota:**

      Vrací výsledek volání ``join()``.


   .. py:method:: set_snapshots()

      Přepočítá a uloží snapshot textového výpisu vedoucích akce.

   .. py:method:: redis_snapshot_id()

      Sestaví klíč Redis snapshotu pro seznam akci.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování.


   .. py:method:: generate_redis_snapshot()

      Připraví data akce pro uložení snapshotu do Redis cache.

      **Návratová hodnota:**

      Vrací n-tici.


   .. py:method:: get_by_ident_cely()

      Vrátí instanci akce podle identifikátoru archeologického záznamu.

      **Parametry:**

      - ``ident_cely``: Identifikátor archeologického záznamu.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``get()``, None.



.. py:class:: AkceVedouci

   Databázový model vazeb na další vedoucí archeologického záznamu.

   **Metody:**

   .. py:method:: __str__()

      Metoda vrátí str reprezentaci modelu vedouci.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování.


   .. py:method:: vypis_name()

      Metoda vrátí str reprezentaci modelu vedouci pro vypis.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování.



.. py:class:: ExterniOdkaz

   Databázový model externích odkazů archeologického záznamu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.


   .. py:method:: create_transaction()

      Vytvoří a vrátí Fedora transakci pro práci s externím odkazem.

      **Parametry:**

      - ``transaction_user``: Uživatel nebo osoba ``transaction_user``, v jejímž kontextu se operace provádí.

      **Návratová hodnota:**

      Vrací atribut objektu.



.. py:class:: LokalitaSekvence

   Model pro tabulku se sekvencemi lokalit.


.. py:class:: AkceSekvence

   Model pro tabulku se sekvencemi akcí.


Funkce
------

.. py:function:: get_akce_ident(region)

   Vygeneruje nový permanentní identifikátor akce pro zadaný region.

   **Parametry:**

   - ``region``: Identifikátor regionu použitého jako prefix sekvence akcí.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování.

   **Výjimky:**

   - ``MaximalIdentNumberError``: Vyvolá se při splnění podmínky ``sequence.sekvence >= MAXIMUM``; nebo při splnění podmínky ``missing[0] >= MAXIMUM``.

