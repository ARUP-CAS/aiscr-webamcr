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

      :param user: Uživatel, který změnu stavu provedl.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: set_odeslany()

      Přepne záznam do stavu „odeslaný“ a propíše navazující změny do souvisejících dat.

      Metoda zároveň posune navázané dokumenty a externí zdroje do odpovídajících stavů.

      :param user: Uživatel, který odeslání provedl.
      :param request: HTTP požadavek použitý při generování trvalých identifikátorů dokumentů.
      :param messages: Django message backend pro předání uživatelských hlášek.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: set_archivovany()

      Přepne záznam do stavu „archivovaný“ a zaznamená změnu do historie.

      U samostatné akce s dočasným identifikátorem se při archivaci nastaví trvalý ident.

      :param user: Uživatel, který archivaci provedl.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: set_vraceny()

      Metoda pro vrácení o jeden stav méně a uložení změny do historie.

      :param user: Uživatel, který vrácení stavu provedl.
      :param new_state: Cílový stav záznamu, do kterého má být záznam vrácen.
      :param poznamka: Poznámka uložená do historie k provedenému vrácení.

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

      Propíše nový základ identifikátoru do navázaných DJ a komponent.

      :param new_ident: Nový prefix identifikátoru archeologické akce.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: set_akce_ident()

      Nastaví nebo vygeneruje identifikátor akce a promítne změnu do navázaných dat.

      :param ident: Volitelný identifikátor; pokud není zadán, vygeneruje se nový.
      :param delete_container: Určuje, zda se při změně identifikátoru smaže původní kontejner.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: get_absolute_url()

      Vrátí detail URL archeologického záznamu nebo jeho dokumentační jednotky.

      :param dj_ident_cely: Identifikátor dokumentační jednotky pro detail DJ varianty.
      :return: URL detailu akce nebo lokality podle typu archeologického záznamu.

   .. py:method:: get_redirect()

      Vrátí redirect odpověď na detail archeologického záznamu.

      :param dj_ident_cely: Identifikátor dokumentační jednotky pro detail DJ varianty.
      :return: Redirect na URL vrácenou metodou ``get_absolute_url``.

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

      Vrátí ID navázaných částí dokumentu v okamžiku načtení instance.

      :return: Seznam ID částí dokumentu, případně prázdný seznam.

   .. py:method:: initial_pristupnost()

      Vrátí původní hodnotu přístupnosti záznamu.

      :return: Hodnota původní přístupnosti nebo ``None``.

   .. py:method:: initial_pristupnost()

      Nastaví interně uloženou původní hodnotu přístupnosti.

      :param value: Nová hodnota původní přístupnosti.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: save()

      Uloží změny objektu.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: igsn_lokalita_hide()

      Skryje IGSN záznam lokality, pokud je aktuální záznam typu lokalita.

      :param check_status: Při ``True`` ověří stav před provedením změny v IGSN.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: igsn_lokalita_publish()

      Publikuje IGSN lokality, pokud je záznam lokality archivovaný.

      :param check_status: Při ``True`` ověří stav před publikací v IGSN.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: igsn_lokalita_delete()

      Odstraní IGSN záznam lokality, pokud jde o záznam typu lokalita.

      :param check_status: Při ``True`` ověří stav před smazáním v IGSN.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: igsn_lokalita_update()

      Aktualizuje IGSN metadata lokality, pokud jde o záznam typu lokalita.

      :param check_status: Při ``True`` ověří stav před aktualizací v IGSN.
      :param reload_record: Určuje, zda se má záznam před aktualizací znovu načíst.
      :return: Funkce nevrací hodnotu (``None``).


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

      Vrátí původní projekt navázaný při inicializaci instance.

      :return: Instance projektu z ``initial_projekt_id`` nebo ``None``.

   .. py:method:: get_absolute_url()

      Vrátí URL detailu archeologického záznamu navázaného na akci.

      :return: Absolutní URL detailu akce.

   .. py:method:: vedouci_organizace()

      Vrátí seznam vedoucích organizací akce jako text.

      :return: Čárkou oddělený seznam názvů organizací.

   .. py:method:: vedouci()

      Vrátí textový seznam vedoucích osob navázaných na akci.

      :return: Čárkou oddělený seznam jmen vedoucích.

   .. py:method:: set_snapshots()

      Přepočítá a uloží snapshot textového výpisu vedoucích akce.

      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: redis_snapshot_id()

      Sestaví klíč Redis snapshotu pro seznam akci.

      :return: Identifikátor snapshotu používaný v Redis cache.

   .. py:method:: generate_redis_snapshot()

      Připraví data akce pro uložení snapshotu do Redis cache.

      :return: Dvojice ``(snapshot_id, data)`` nebo ``(None, None)``, pokud akce neexistuje.

   .. py:method:: get_by_ident_cely()

      Vrátí instanci akce podle identifikátoru archeologického záznamu.

      :param ident_cely: Identifikátor archeologického záznamu.
      :return: Nalezená instance ``Akce`` nebo ``None``.


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

      Vytvoří a vrátí Fedora transakci pro práci s externím odkazem.

      :param transaction_user: Vstupní hodnota ``transaction_user`` pro danou operaci.
      :return: Vrací nově vytvořený výsledek operace.


.. py:class:: LokalitaSekvence

   Model pro tabulku se sekvencemi lokalit.


.. py:class:: AkceSekvence

   Model pro tabulku se sekvencemi akcií.


Funkce
------

.. py:function:: get_akce_ident(region)

   Vygeneruje nový permanentní identifikátor akce pro zadaný region.

   :param region: Identifikátor regionu použitého jako prefix sekvence akcí.
   :return: Nový jednoznačný identifikátor archeologické akce.
