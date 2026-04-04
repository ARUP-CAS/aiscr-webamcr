Skript check_container_image_reference_parity.py
================================================

Automaticky generovaná dokumentace skriptu ``scripts/check_container_image_reference_parity.py``.

Přehled modulu
--------------

Kontrola a úprava shody pinů (tag/digest) u stejného container image v Dockerfileech a docker-compose.

- V jednom souboru: stejný image repozitář nesmí mít různé tagy/digesty (FROM nebo image:).
- docker-compose.yml je zdroj pravdy pro literály; spotřebitelské compose soubory se při --fix srovnají na prod.

Výstup pro CI: řádky na stderr s prefixem ``[image-ref-parity]``.

Třídy
------

.. py:class:: DockerfileScan

   Výsledek průchodu Dockerfile: agregace pinů podle repozitáře a metadata řádků pro přepis ``FROM``.


Funkce
------

.. py:function:: log_msg(message)

   Vypíše jeden řádek na stderr s prefixem pro grep v CI.

   **Parametry:**

   - ``message``: Text bez prefixu.
   - ``verbose_only``: Pokud True, vypíše jen při verbose režimu.
   - ``verbose``: Aktuální verbose příznak.


.. py:function:: is_pre_commit()

   Zjistí, zda skript běží jako pre-commit hook (pro implicitní verbose).

   **Návratová hodnota:**

   True, pokud je v prostředí nastavena proměnná ``PRE_COMMIT``.


.. py:function:: is_literal_image_ref(value)

   Určí, zda hodnota ``image:`` v compose lze použít pro porovnání pinů (bez rozšíření proměnných).

   **Parametry:**

   - ``value``: Řetězec z pole ``image`` u služby.

   **Návratová hodnota:**

   False pro prázdný řetězec, obsah ``${`` / ``$$``; jinak True.


.. py:function:: _strip_platform_flags(rest)

   Odstraní z řetězce za ``FROM`` všechny úvodní příznaky ``--platform=...``.

   **Parametry:**

   - ``rest``: Část řádku za ``FROM`` před případným ``AS``.

   **Návratová hodnota:**

   Zbytek začínající odkazem na image, nebo prázdný řetězec při neplatném tvaru.


.. py:function:: parse_from_instruction(line)

   Parsuje řádek Dockerfile začínající ``FROM`` na odkaz na image a volitelné jméno stage.

   **Parametry:**

   - ``line``: Jeden řádek souboru (může obsahovat koncový komentář ``#``).

   **Návratová hodnota:**

   ``(image_ref, as_name)`` nebo None, pokud řádek není platný ``FROM``.


.. py:function:: repository_and_pin(image_ref)

   Rozdělí odkaz na container image na klíč repozitáře a normalizovaný pin (tag a/nebo digest).

   **Parametry:**

   - ``image_ref``: Řetězec image bez části ``AS`` (např. ``ghcr.io/foo:1.0``).

   **Návratová hodnota:**

   ``(repo_key, pin_key)`` — obě části malými písmeny pro porovnání.


.. py:function:: choose_canonical_pin(pins)

   Vybere jeden kanonický pin z množiny normalizovaných pinů (malá písmena).

   **Parametry:**

   - ``pins``: Množina pin_key.

   **Návratová hodnota:**

   Vítězný pin_key.


.. py:function:: pick_display_ref_for_pin(refs_by_pin, pin_key)

   Vrátí reprezentaci image pro zápis (zachovává casing z jednoho výskytu).

   **Parametry:**

   - ``refs_by_pin``: Mapa pin_key -> původní řetězce image.
   - ``pin_key``: Normalizovaný pin.

   **Návratová hodnota:**

   Původní řetězec image.


.. py:function:: build_yaml()

   Vytvoří nakonfigurovanou instanci ``ruamel.yaml.YAML`` pro čtení/zápis compose se zachováním uvozovek.

   **Návratová hodnota:**

   YAML loader/dumper vhodný pro úpravy compose souborů.


.. py:function:: scan_dockerfile(text)

   Projde text Dockerfile a sejme externí base image (mimo ``scratch`` a odkazy na již definované stage).

   **Parametry:**

   - ``text``: Celý obsah Dockerfile.

   **Návratová hodnota:**

   Struktura s množinami pinů, mapou původních řetězců a ``line_info`` pro ``FROM_IMG_RE``.


.. py:function:: fix_dockerfile_text(text, fix, path, _verbose)

   Zkontroluje nebo opraví konflikty pinů u stejného ``repo_key`` v jednom Dockerfile.

   **Parametry:**

   - ``text``: Původní obsah souboru.
   - ``fix``: Pokud True, přepíše ``FROM`` řádky na kanonický pin; pokud False, jen hlásí chyby.
   - ``path``: Cesta pro hlášky v chybách.
   - ``_verbose``: Rezervováno (aktuálně nepoužito).

   **Návratová hodnota:**

   Trojice ``(nový_text, seznam_chyb, byl_upraven)``.


.. py:function:: iter_compose_service_images(data)

   Projde ``services`` v načteném compose a vrátí služby s řetězcovým ``image``.

   **Parametry:**

   - ``data``: Kořenový dict compose (např. z ``yaml.load``), očekává se klíč ``services``.

   **Návratová hodnota:**

   Iterátor trojic (viz ``:yield:``); při neplatném ``data`` nebo ``services`` nic nevygeneruje.

   **Generuje:**

   ``(název_služby, hodnota_image, spec_dict)`` — ``spec_dict`` umožní při ``--fix`` změnit ``image`` na místě.


.. py:function:: scan_compose_intra(data, _path)

   Shromáždí literální ``image`` z jednoho compose souboru pro intra-file kontrolu shody pinů.

   **Parametry:**

   - ``data``: Parsovaný obsah compose.
   - ``_path``: Cesta k souboru (pro rozhraní; aktuálně se nepoužívá).

   **Návratová hodnota:**

   ``(pins_by_repo, refs_by_repo_pin, počet_přeskočených_neliterálních_image)``.


.. py:function:: apply_compose_intra_fix(data, path, pins_by_repo, refs_by_repo_pin, fix, _verbose)

   U jednoho compose sjednotí literální ``image`` se stejným ``repo_key`` na jeden kanonický pin.

   **Parametry:**

   - ``data``: Parsovaný strom compose (mění se in-place při ``fix=True``).
   - ``path``: Cesta k souboru pro chybové hlášky.
   - ``pins_by_repo``: Agregace pinů ze :func:`scan_compose_intra`.
   - ``refs_by_repo_pin``: Mapa původních řetězců image podle pinu.
   - ``fix``: Zapnout zápis oprav do ``data``.
   - ``_verbose``: Rezervováno (nepoužito).

   **Návratová hodnota:**

   ``(seznam_chyb, byl_proveden_zápis_do_dat)``.


.. py:function:: extract_prod_literal_map(data)

   Z produkčního compose vytvoří mapu ``repo_key`` → literální řetězec ``image`` (první výskyt).

   **Parametry:**

   - ``data``: Parsovaný ``docker-compose.yml`` (nebo ekvivalent).

   **Návratová hodnota:**

   Slovník pro cross-file srovnání se spotřebitelskými compose.


.. py:function:: apply_compose_cross_fix(consumer_data, consumer_path, prod_map, fix, verbose)

   Porovná literální image ve spotřebitelském compose s mapou z produkce a případně je srovná.

   **Parametry:**

   - ``consumer_data``: Parsovaný compose spotřebitele (mění se in-place při ``fix=True``).
   - ``consumer_path``: Cesta k souboru spotřebitele (logy a chyby).
   - ``prod_map``: Výstup :func:`extract_prod_literal_map` z ``docker-compose.yml``.
   - ``fix``: Pokud True, přepíše ``image`` na hodnotu z prod při nesouladu pinu.
   - ``verbose``: Zapíná podrobné SKIP logy u neliterálních image (přes ``log_msg``).

   **Návratová hodnota:**

   ``(seznam_chyb při fix=False, byl_proveden_zápis)``.


.. py:function:: process_dockerfiles(root, fix, verbose)

   Zpracuje všechny Dockerfile z konstanty ``DOCKERFILE_PATHS`` pod kořenem ``root``.

   **Parametry:**

   - ``root``: Kořen repozitáře (aktuální pracovní adresář při běhu z pre-commit).
   - ``fix``: Předáno do :func:`fix_dockerfile_text`; při True zapíše změny na disk.
   - ``verbose``: Předáno dál pro případné budoucí logování (část volání zachována kvůli API).

   **Návratová hodnota:**

   ``(souhrnné_chyby, seznam_cest_upravených_souborů)``.


.. py:function:: process_compose_files(root, fix, verbose)

   Načte prod a spotřebitelské compose, provede intra-file a cross-file kontrolu nebo opravu.

   Zapisuje pouze soubory, u kterých došlo ke změně dat (ne přeformátovává prod zbytečně).

   **Parametry:**

   - ``root``: Kořen repozitáře.
   - ``fix``: Zapne zápis YAML a cross-file úpravy spotřebitelů.
   - ``verbose``: Statistiky přeskočených neliterálních referencí a SKIP u cross-file.

   **Návratová hodnota:**

   ``(souhrnné_chyby, seznam_cest_upravených_souborů)``.


.. py:function:: main(argv)

   Vstupní bod CLI: spustí kontrolu Dockerfile a compose, volitelně s opravami.

   **Parametry:**

   - ``argv``: Argumenty příkazové řádky (bez ``sys.argv[0]``); None znamená ``sys.argv[1:]``.

   **Návratová hodnota:**

   0 při úspěchu; 1 při nalezených chybách (bez ``--fix``) nebo po úpravě souborů (s ``--fix``, aby pre-commit znovu zstageoval).

Zdrojový kód
------------

.. literalinclude:: ../../../../scripts/check_container_image_reference_parity.py
   :language: python
   :linenos:
