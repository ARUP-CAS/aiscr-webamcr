Oprávnění
==========

Oprávnění využívá model ``Opravneni`` a ``KonkretniOpravneni`` a umožňuje řídit přístup k pohledům a záznamům.

Vlastník
--------

* akce či dokumentu (a jejích potomků) = uživatel, který zapsal záznam
* projektu = nepoužívá se

Stejná organizace
-----------------

* u projektu a podřízených DT (vč. akcí a dokumentů; jinde se nepoužívá) = uživatel (archeolog) s totožnou organizací, jako je v poli projekt.organizace

Model Opravneni
---------------

V Modelu ``Opravneni`` se nastavuje adresa a role pro kterou se použije pak konkrétní oprávnění:

* ``role`` - uživatelská role, pro kterou je oprávnění nastaveno.
* ``adresa_v_aplikaci`` - adresa v aplikaci v urls začínající s ``/``, například ``/projekt/zrusit/<str:ident_cely>``.

Model KonkretniOpravneni
------------------------

V Modelu ``KonkretniOpravneni`` se nastavují konkrétní oprávnění která se mají pro adresu a roli zkontrolovat:

* ``druh opravneni`` - nastavení úrovně oprávnění. Pole má následující možnosti:
    * ``Nic`` - přístup k pohledu není povolen.
    * ``Vlastni`` - přístup k vlastním záznamům.
    * ``Organizace`` - přístup k záznamům, které patří uživatelům ze stejné organizace.
    * ``Vse`` - přístup ke všem záznamům.
    * ``Stav`` - přístup k záznamům podle stavu. Pokud vybráno, pak povinné pole ``porovnani stavu`` a ``stav``.
    * ``Xid`` - přístup jen k záznamům, které mají dočasný ident (ident začíná s ``X``).
* ``porovani stavu`` - Povinné pokud vybrán druh ``Stav``. Vyberá se operátor porovnání (<, =, >).
* ``stav`` - Povinné pokud vybrán druh ``Stav``. Vyberá se stav který se má porovnávat.
* ``vazba na konkretni opravneni`` - Vyberá se pokud se mají 2 a více konkrétních oprávnění splnit spolu.

Dokumentace akcí
----------------

Dokumentace všech definovaných akcí v systému oprávnění.

Generování oprávnění
---------------------

Generování oprávnění je potřeba provést následujícími příkazy:

.. code-block:: bash

   python3 manage.py update_permissions --apps auth
   python3 manage.py update_permissions --apps dokument
   python3 manage.py update_permissions --apps heslar
   python3 manage.py update_permissions --apps uzivatel

Uživatelské akce řízené pomocí oprávnění
-----------------------------------------

Seznam všech akcí definovaných ve třídě ``Permissions.actionChoices``:

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
- ``soubor_nahled_projekt``
- ``soubor_nahled_dokument``
- ``soubor_nahled_model3d``
- ``soubor_nahled_pas``
- ``spoluprace_zadost``
- ``spoluprace_aktivovat``
- ``spoluprace_deaktivovat``
- ``spoluprace_smazat``
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

**Celkem:** 148 akcí