Skript test_check_static_vendor_manifest.py
===========================================

Automaticky generovaná dokumentace skriptu ``scripts/test_check_static_vendor_manifest.py``.

Funkce
------

.. py:function:: _write(path, content)

   Popis není k dispozici.

.. py:function:: _library()

   Popis není k dispozici.

.. py:function:: _repo(tmp_path, libraries, dependencies)

   Popis není k dispozici.

.. py:function:: test_consistent_manifest_has_no_errors(tmp_path)

   Manifest pokrývající všechny soubory ve vendor/ projde bez chyb.

   :param tmp_path: Dočasný adresář pytestu použitý jako kořen repozitáře.

.. py:function:: test_file_in_vendor_missing_from_manifest(tmp_path)

   Nový soubor ve vendor/ bez záznamu v manifestu je chyba.

   :param tmp_path: Dočasný adresář pytestu použitý jako kořen repozitáře.

.. py:function:: test_missing_version_and_nonexistent_path(tmp_path)

   Prázdná verze a neexistující cesta se hlásí zvlášť.

   :param tmp_path: Dočasný adresář pytestu použitý jako kořen repozitáře.

.. py:function:: test_vendor_dir_duplicates_npm_dependency(tmp_path)

   Adresář ve vendor/ se jménem npm závislosti je duplicita.

   :param tmp_path: Dočasný adresář pytestu použitý jako kořen repozitáře.

.. py:function:: test_template_reference_outside_manifest(tmp_path)

   Šablona odkazující na soubor ve vendor/, který v manifestu není, je chyba.

   :param tmp_path: Dočasný adresář pytestu použitý jako kořen repozitáře.

.. py:function:: test_css_url_to_missing_file(tmp_path)

   Relativní url() v CSS z manifestu, které nemíří na existující soubor, je chyba.

   :param tmp_path: Dočasný adresář pytestu použitý jako kořen repozitáře.

Zdrojový kód
------------

.. literalinclude:: ../../../../scripts/test_check_static_vendor_manifest.py
   :language: python
   :linenos:
