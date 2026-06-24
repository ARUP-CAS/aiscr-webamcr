Oprávnění
==========

Oprávnění využívá modely ``Permissions`` a ``PermissionsSkip`` a umožňuje řídit přístup k pohledům a záznamům.

Model Permissions
---------------

V modelu ``Permissions`` se nastavují konkrétní oprávnění která se mají pro adresu a roli zkontrolovat:

* ``address_in_app`` - adresa v aplikaci v urls, například ``projekt/zrusit/<str:ident_cely>``.
* ``role`` - uživatelská role, pro kterou je oprávnění nastaveno.
* ``action`` - uživatelská akce, pro kterou je oprávnění nastaveno (nepovinné).
* ``base`` - nastavení základního režimu přístupu (ano/ne).
* ``status`` - nastavení přístupu podle stavu záznamu. Vybírá se operátor porovnání (<, =, >).
* ``ownership`` - nastavení přístupu podle vlastnictví záznamu.
* ``accessibility`` - nastavení přístupu podle přístupnosti záznamu.

Model PermissionsSkip
-------------------

V modelu ``PermissionsSkip`` se nastavují výjimky z pravidel nastavených v modelu ``Permissions``. Pokud je pro danou identifikátor záznamu a roli nalezena shoda v tomto modelu, v modelu ``Permissions`` se aplikují pravidla tak, jako by šlo o vlastníka záznamu.

Import oprávnění
---------------------

Import oprávnění je řešen třídou ``PermissionAdmin`` v souboru ``webclient/core/admin.py``. Při importu se načítají data z tabulky ``webclient/core/resources/uzivatelska_prava.csv`` a vytvářejí se záznamy v modelu ``Permissions``.

Tabulka oprávnění
--------------------

Konkrétní oprávnění jsou definována v tabulce ``webclient/core/resources/uzivatelska_prava.csv``. Tabulka obsahuje následující sloupce:

* app = název aplikace
* URL = adresa v aplikaci
* action = název akce (používá se pro bližší specifikaci akce či součásti view, pro které se oprávnění uplatňuje)
* Základní_x (A-E) = nastavení základního režimu přístupu pro roli x (A-E)
* Stav_x (B-E) = nastavení přístupu podle stavu záznamu pro roli x (B-E)
* Vlastnictví_x (B-E) = nastavení přístupu podle vlastnictví záznamu pro roli x (B-E)
* Přístupnost_x (B-E) = nastavení přístupu podle přístupnosti pro roli x (B-E)
* spec = speciální podmínky, obvykle přímo implementované v kódu

Skupiny (role) uživatelů:

* A = anonymní uživatel
* B = registrovaný uživatel (badatel)
* C = archeolog
* D = archivář
* E = administrátor

Pole pro stavnovení přístupnosti:
* AZ = ``archeologicky_zaznam.pristupnost``
* D = ``dokument.pristupnost``
* P = ``projekt.pristupnost_pom``
* SN = ``samostatny_nalez.pristupnost``
* PI = ``pian.pristupnost_pom``

Hodnoty v jednotlivých sloupcích oprávnění:

* ``X`` = nepřístupné
* ``*`` = není omezeno daným kritériem
* ``&`` = logické AND
* ``|`` = logické OR
* ``x (my)`` / ``x (ours)`` = podmínka pro ignorování přístupnosti pro vlastní záznamy / záznamy stejné organizace¨ daného typu (x - viz přehled výše)

Způsob určování vlastnictví
-----------------------

.. list-table::
   :header-rows: 1

   * - Typ záznamu
     - Zkratka
     - my
     - ours
   * - Archeologický záznam
     - AZ
     - ``AZ01.uzivatel`` = ``uzivatel``
     - ``AZ01.uzivatel.organizace`` = ``uzivatel.organizace``
   * - Dokument
     - D
     - ``D01.uzivatel`` = ``uzivatel``
     - ``D01.uzivatel.organizace`` = ``uzivatel.organizace``
   * - Extený zdroj
     - EZ
     - ``EZ01.uzivatel = uzivatel``
     - ``EZ01.uzivatel.organizace``
     - ``uzivatel.organizace``
   * - Projekt
     - P
     - N/A
     - ``projekt.organizace`` = ``uzivatel.organizace``
   * - Samostatný nález
     - SN
     - ``SN01.uzivatel`` = ``uzivatel``
     - ``SN.projekt.organizace`` = ``uzivatel.organizace``
   * - Spolupráce
     - US
     - ``uzivatel_spoluprace.spolupracovnik`` = ``uzivatel``
     - ``uzivatel_spoluprace.vedouci.organizace`` = ``uzivatel.organizace``
   * - PIAN
     - PI
     - ``PI01.uzivatel`` = ``uzivatel`` OR ``AZ01.uzivatel`` = ``uzivatel``
     - ``PI01.uzivatel.organizace`` = ``uzivatel.organizace`` OR ``AZ01.uzivatel.organizace`` = ``uzivatel.organizace`` OR ``akce.projekt.organizace`` = ``uzivatel.organizace``
   * - Uživatel
     - U
     - ``auth_user`` = ``uzivatel``
     - N/A

Vlastník:

* **archeologického záznamu**, **dokumentu**, **exteního zdroje** či **samostatného nálezu** (a jejich potomků) = uživatel, který zapsal záznam
* **projektu** = nepoužívá se
* **PIAN** = uživatel, který PIAN vytvořil a uživatel, který zapsal archeologický záznam spojený s PIAN
* **spolupráce** = dotčený spolupracovník
* **uživatel** = dotčený uživatel

Stejná organizace:

* u **archeologického záznamu**, **dokumentu** či **exteního zdroje** (a jejich potomků) = uživatel (archeolog) s totožnou organizací, jako je organizace uživatele, který zapsal záznam
* u **projektu** = uživatel (archeolog) s totožnou organizací, jako je v poli projekt.organizace
* u **PIAN** = uživatel (archeolog) s totožnou organizací, jako je organizace uživatele, který PIAN vytvořil nebo zapsal archeologický záznam spojený s PIAN nebo patří k organizaci souvisejícího projektu
* u **samostatného nálezu** = uživatel (archeolog) s totožnou organizací, jako je organizace u projektu, ke kterému je samostatný nález připojený (``projekt.organizace``), nebo s totožnou organizací jako je cílová organizace, které byl nález předán (``predano_organizace``)
* u **spolupráce** = uživatel (archeolog) s totožnou organizací, jako je organizace dotčeného vedoucího
* u **uživatele** = nepoužívá se

Uživatelské akce řízené pomocí oprávnění
-----------------------------------------

Používá se pro bližší specifikaci akce či součásti view, pro které se oprávnění uplatňuje. Seznam všech akcí definovaných ve třídě ``Permissions.actionChoices``:

- ``adb_smazat``
- ``vb_smazat``
- ``adb_zapsat``
- ``archz_adb_zapsat``
- ``archz_komponenta_zapsat``
- ``archz_pian_zapsat``
- ``archz_vratit``
- ``archz_odeslat``
- ``archz_archivovat``
- ``archz_pian_edit``
- ``archz_vedouci_smazat``
- ``archz_edit``
- ``archz_smazat``
- ``archz_zmenit_proj``
- ``archz_zmenit_sam``
- ``archz_odpojit_dokument``
- ``archz_pripojit_dok``
- ``archz_pripojit_proj``
- ``archz_pripojit_dok_proj``
- ``archz_dj_zapsat``
- ``archz_pripojit_do_proj``
- ``dj_smazat``
- ``dj_zmenit_katastr``
- ``dok_pripojit_archz``
- ``dok_pripojit_proj``
- ``dok_cast_odpojit``
- ``dok_cast_edit``
- ``dok_cast_smazat``
- ``dok_cast_zapsat``
- ``dok_komponenta_zapsat``
- ``dok_edit``
- ``dok_smazat``
- ``dok_archivovat``
- ``dok_odeslat``
- ``dok_vratit``
- ``dok_tvary_edit``
- ``dok_tvary_smazat``
- ``dok_zapsat_do_archz``
- ``dok_zapsat_do_projekt``
- ``model_edit``
- ``neident_akce_edit``
- ``neident_akce_smazat``
- ``ez_edit``
- ``ez_odeslat``
- ``ez_potvrdit``
- ``ez_vratit``
- ``ez_smazat``
- ``eo_edit_ez``
- ``eo_edit_akce``
- ``eo_odpojit_ez``
- ``eo_odpojit_akce``
- ``eo_pripojit_akce``
- ``eo_pripojit_ez``
- ``lokalita_komponenta_zapsat``
- ``lokalita_pian_edit``
- ``lokalita_pian_zapsat``
- ``lokalita_dj_zapsat``
- ``lokalita_edit``
- ``komponenta_detail_akce``
- ``komponenta_detail_dok``
- ``komponenta_smazat_akce``
- ``komponenta_smazat_dok``
- ``komponenta_zapsat_akce``
- ``komponenta_zapsat_dok``
- ``nalez_smazat_dokument``
- ``nalez_smazat_akce``
- ``nalez_edit_dokument``
- ``nalez_edit_akce``
- ``notifikace_projekty``
- ``pas_edit``
- ``pas_archivovat``
- ``pas_odeslat``
- ``pas_potvrdit``
- ``pas_vratit``
- ``pas_smazat``
- ``pas_ulozeni_edit``
- ``pas_zapsat_do_projektu``
- ``mapa_pas``
- ``mapa_pian``
- ``pian_potvrdit``
- ``pian_odpojit``
- ``pian_zapsat``
- ``projekt_archivovat``
- ``projekt_dok_odpojit``
- ``projekt_dok_pripojit``
- ``projekt_edit``
- ``projekt_generovat_exp_list``
- ``projekt_generovat_oznameni``
- ``projekt_oznamovatel_zapsat``
- ``projekt_oznamovatel_edit``
- ``projekt_zadost_udaje_oznamovatel``
- ``projekt_smazat``
- ``projekt_navrh_ke_zruseni``
- ``projekt_prihlasit``
- ``projekt_schvalit``
- ``projekt_ukoncit_v_terenu``
- ``projekt_upravit_datum_oznameni``
- ``projekt_zadost_odhlaseni_projektu``
- ``projekt_zadost_zruseni_projektu``
- ``projekt_uzavrit``
- ``projekt_vratit_navrh_zruseni``
- ``projekt_vratit``
- ``projekt_zahajit_v_terenu``
- ``projekt_zrusit``
- ``projekt_autocomplete_archz``
- ``projekt_autocomplete_dokument``
- ``projekt_pas_zobrazit``
- ``soubor_nahrat_dokument``
- ``soubor_nahrat_model3d``
- ``soubor_nahrat_pas``
- ``soubor_nahrat_projekt``
- ``soubor_smazat_projekt``
- ``soubor_smazat_dokument``
- ``soubor_smazat_model3d``
- ``soubor_nahradit_model3d``
- ``soubor_smazat_pas``
- ``soubor_stahnout_projekt``
- ``soubor_stahnout_dokument``
- ``soubor_stahnout_model3d``
- ``soubor_stahnout_pas``
- ``soubor_nahradit_dokument``
- ``soubor_nahradit_pas``
- ``soubor_prejmenovat_dokument``
- ``soubor_prejmenovat_model3d``
- ``soubor_prejmenovat_pas``
- ``soubor_nahled_projekt``
- ``soubor_nahled_dokument``
- ``soubor_nahled_model3d``
- ``soubor_nahled_pas``
- ``spoluprace_zadost``
- ``spoluprace_aktivovat``
- ``spoluprace_deaktivovat``
- ``spoluprace_smazat``
- ``spoluprace_edit_projekty``
- ``pian_import_new``
- ``pian_import_change``
- ``akce_dj_zakladni``
- ``akce_pripojit_pian_mapa``
- ``akce_pripojit_pian_id``
- ``lokalita_dj_zakladni``
- ``lokalita_pripojit_pian_mapa``
- ``lokalita_pripojit_pian_id``
- ``dokumenty_tabulka_projekt``
- ``dokumenty_tabulka_arch_z``
- ``vypis_dokument``
- ``vypis_projekt``
- ``vypis_akce``
- ``vypis_lokalita``
- ``vypis_pas``
- ``vypis_model3d``
- ``vypis_ez``
- ``historie_fedora``

**Celkem:** 152 akcí