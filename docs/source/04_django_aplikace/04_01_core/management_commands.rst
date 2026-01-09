Management příkazy
==================

Dokumentace všech Django management příkazů v aplikaci.

Příkazy se spouští pomocí ``python manage.py <název_příkazu> [parametry]``


``check_pian_properties``
-------------------------

Django management příkaz pro kontrolu a opravu vlastností PIANů.

Tento příkaz kontroluje a případně opravuje:

- Typ geometrie (typ) - musí odpovídat skutečnému typu geometrie (bod/linie/plocha)
- Základní mapy ZM10 a ZM50 - určí se podle pozice geometrie

Pro každý PIAN:

- Ověří, zda typ geometrie odpovídá skutečnosti
- Vypočítá reprezentativní bod geometrie (střed u linie, centroid u plochy)
- Určí příslušnost k základním mapám ZM10 a ZM50
- Pokud se některá hodnota liší, provede aktualizaci

Poznámka:
    - Aktualizace jsou prováděny včetně Fedora transakcí a metadat
    - Proces může trvat delší dobu v závislosti na počtu PIANů

Příklady použití::

    python manage.py check_pian_properties

.. automodule:: core.management.commands.check_pian_properties
   :members: Command
   :undoc-members:
   :show-inheritance:


``generate_metadata``
---------------------

Django management příkaz pro generování a ukládání XML metadat.

Tento příkaz zpracovává záznamy z databáze a pro každý záznam vygeneruje XML metadata
podle AMČR schématu. Vygenerovaná metadata jsou následně uložena do Fedora repozitáře
prostřednictvím metody save_metadata.

Parametry:
    - --model: Název třídy modelu (např. Projekt, ArcheologickyZaznam). Pokud není zadán, zpracují se všechny dostupné modely
    - --limit: Maximální počet záznamů ke zpracování
    - --start-with-pk: Primární klíč, od kterého začít zpracování

Příklady použití::

    python manage.py generate_metadata
    python manage.py generate_metadata --model Projekt --limit 100
    python manage.py generate_metadata --model Adb --start-with-pk 1000 --limit 50

.. automodule:: core.management.commands.generate_metadata
   :members: Command
   :undoc-members:
   :show-inheritance:

**Parametry:**

.. list-table::
   :header-rows: 1
   :widths: 30 20 20 30

   * - Název
     - Typ
     - Výchozí hodnota
     - Popis
   * - ``--model``
     - ``str``
     - ``None``
     - core.management.commands.generate_metadata.Command.add_arguments.model_help
   * - ``--limit``
     - ``int``
     - ``None``
     - core.management.commands.generate_metadata.Command.add_arguments.limit_help
   * - ``--start-with-pk``
     - ``int``
     - ``None``
     - core.management.commands.generate_metadata.Command.add_arguments.start_with_pk_help


``generate_thumbs``
-------------------

Django management příkaz pro generování náhledů souborů.

Tento příkaz zpracuje dávku souborů a pro každý soubor zkontroluje,
zda existují náhledy v Fedora repozitáři. Pokud náhledy neexistují,
vygeneruje je ze zdrojového souboru.

Parametry (vzájemně se vylučují):
    - --pks: Seznam primárních klíčů souborů (odděleno mezerami)
    - --range: Rozsah primárních klíčů ve formátu "start end"
    - --csv: Cesta k CSV souboru s listem cest v sloupci "record" (repository path)

Poznámka:
    - Musí být zadán právě jeden z parametrů --pks, --range, nebo --csv
    - Náhledy jsou generovány pouze pro obrazové formáty podporované systémem

Příklady použití::

    python manage.py generate_thumbs --pks 1 2 3
    python manage.py generate_thumbs --range 100 200
    python manage.py generate_thumbs --range 1 1000
    python manage.py generate_thumbs --csv /tmp/missing_thumbs.csv

.. automodule:: core.management.commands.generate_thumbs
   :members: Command
   :undoc-members:
   :show-inheritance:

**Parametry:**

.. list-table::
   :header-rows: 1
   :widths: 30 20 20 30

   * - Název
     - Typ
     - Výchozí hodnota
     - Popis
   * - ``--pks``
     - ``int``
     - 
     - core.management.commands.generate_thumbs.Command.add_arguments.pks_help
   * - ``--range``
     - ``int``
     - 
     - core.management.commands.generate_thumbs.Command.add_arguments.range_help
   * - ``--csv``
     - ``str``
     - 
     - core.management.commands.generate_thumbs.Command.add_arguments.csv_help


``import_permissions``
----------------------

Django management příkaz pro import uživatelských oprávnění z CSV souboru.

Tento příkaz načte CSV soubor ``core/resources/uzivatelska_prava.csv``
a importuje uživatelská oprávnění do databáze pomocí PermissionService.

CSV soubor obsahuje definice uživatelských práv a jejich přiřazení.
Při importu se kontroluje správnost formátu a hodnot.

Poznámka:
    - CSV soubor musí být umístěn v adresáři ``core/resources/``
    - Při chybě ve formátu CSV se import přeruší a zobrazí se chybová hláška
    - Úspěšný import zobrazí počet importovaných oprávnění a případné chybějící hodnoty

Příklady použití::

    python manage.py import_permissions

.. automodule:: core.management.commands.import_permissions
   :members: Command
   :undoc-members:
   :show-inheritance:


``remove_gps_data``
-------------------

Django management příkaz pro odstranění GPS dat z existujících souborů.

Tento příkaz načte CSV soubor obsahující seznam souborů (cesty v Fedora repozitáři)
a pro každý záznam odstraní GPS metadata z obrázků (EXIF data).
Po odstranění GPS dat je soubor aktualizován v Fedora repozitáři.

CSV soubor musí obsahovat sloupec "record" s cestami k souborům.

Argumenty:
    - csv_file: Cesta k CSV souboru se seznamem souborů

Formát CSV souboru::

    record
    /path/to/image1.jpg
    /path/to/image2.jpg
    /path/to/image3.jpg

Poznámka:
    - Pouze soubory, které mají GPS data, budou aktualizovány
    - Pro každou aktualizaci se zaznamená nová verze souboru

Příklady použití::

    python manage.py remove_gps_data /tmp/files_with_gps.csv
    python manage.py remove_gps_data /var/data/images.csv

.. automodule:: core.management.commands.remove_gps_data
   :members: Command
   :undoc-members:
   :show-inheritance:

**Parametry:**

.. list-table::
   :header-rows: 1
   :widths: 30 20 20 30

   * - Název
     - Typ
     - Výchozí hodnota
     - Popis
   * - ``csv_file``
     - ``str``
     - 
     - core.management.commands.remove_gps_data.Command.add_arguments.csv_file_help


``save_files_from_storage``
---------------------------

Django management příkaz pro uložení více souborů ze storage.

Tento příkaz zpracuje dávku souborů z lokálního úložiště.
Pro každý soubor provede kontroly (MIME type, antivirus) a uloží jej
do Fedora repozitáře včetně aktualizace metadat v databázi.

Argumenty:
    - storage_path: Cesta k adresáři obsahujícímu soubory (každý soubor musí mít název rovný PK záznamu v DB včetně přípony, např. 123.jpg)

Parametry:
    - --pks: Seznam primárních klíčů souborů (odděleno mezerami)
    - --range: Rozsah primárních klíčů ve formátu "start end"
    - --save-thumbs: Generovat náhledy pro obrazové soubory
    - --disable-antivirus: Přeskočit antivirovou kontrolu

Poznámka:
    - Musí být zadán buď --pks nebo --range, ne oba současně

Příklady použití::

    python manage.py save_files_from_storage /tmp/files --pks 1 2 3
    python manage.py save_files_from_storage /tmp/files --range 100 200
    python manage.py save_files_from_storage /tmp/files --pks 10 20 --save-thumbs

.. automodule:: core.management.commands.save_files_from_storage
   :members: Command
   :undoc-members:
   :show-inheritance:

**Parametry:**

.. list-table::
   :header-rows: 1
   :widths: 30 20 20 30

   * - Název
     - Typ
     - Výchozí hodnota
     - Popis
   * - ``storage_path``
     - ``str``
     - 
     - core.management.commands.save_files_from_storage.Command.add_arguments.storage_path_help
   * - ``--pks``
     - ``int``
     - 
     - core.management.commands.save_files_from_storage.Command.add_arguments.pks_help
   * - ``--range``
     - ``int``
     - 
     - core.management.commands.save_files_from_storage.Command.add_arguments.range_help
   * - ``--save-thumbs``
     - 
     - 
     - core.management.commands.save_files_from_storage.Command.add_arguments.save_thumbs_help
   * - ``--disable-antivirus``
     - 
     - 
     - core.management.commands.save_files_from_storage.Command.add_arguments.disable_antivirus_help


``save_single_file_from_storage``
---------------------------------

Django management příkaz pro uložení jednotlivého souboru ze storage.

Tento příkaz načte soubor z lokálního úložiště podle jeho primárního klíče,
provede kontroly (MIME type, antivirus), a uloží jej do Fedora repozitáře
včetně aktualizace metadat v databázi.

Argumenty:
    - pk: Primární klíč záznamu souboru v databázi
    - storage_path: Cesta k adresáři obsahujícímu soubory

Parametry:
    - --save-thumbs: Generovat náhledy pro obrazové soubory
    - --disable-antivirus: Přeskočit antivirovou kontrolu

Příklady použití::

    python manage.py save_single_file_from_storage 123 /tmp/files
    python manage.py save_single_file_from_storage 456 /var/storage --save-thumbs

.. automodule:: core.management.commands.save_single_file_from_storage
   :members: Command
   :undoc-members:
   :show-inheritance:

**Parametry:**

.. list-table::
   :header-rows: 1
   :widths: 30 20 20 30

   * - Název
     - Typ
     - Výchozí hodnota
     - Popis
   * - ``pk``
     - ``int``
     - 
     - core.management.commands.save_single_file_from_storage.Command.add_arguments.pk_help
   * - ``storage_path``
     - ``str``
     - 
     - core.management.commands.save_single_file_from_storage.Command.add_arguments.storage_path_help
   * - ``--save-thumbs``
     - 
     - 
     - core.management.commands.save_single_file_from_storage.Command.add_arguments.save_thumbs_help
   * - ``--disable-antivirus``
     - 
     - 
     - core.management.commands.save_single_file_from_storage.Command.add_arguments.disable_antivirus_help


``transform_to_sjtsk``
----------------------

Django management příkaz pro transformaci souřadnic do systému S-JTSK.

Tento příkaz transformuje geometrie z WGS84 do souřadnicového systému S-JTSK
pro různé typy záznamů (PIAN, nález, projekt, dokument).

Parametry:
    - model: Typ modelu pro transformaci (pian, nalez, projekt, dokument)

Poznámka:
    - Transformuje pouze záznamy, které mají vyplněnou geometrii (geom) ale nemají vyplněnou S-JTSK geometrii (geom_sjtsk)

Příklady použití::

    python manage.py transform_to_sjtsk pian
    python manage.py transform_to_sjtsk nalez
    python manage.py transform_to_sjtsk projekt
    python manage.py transform_to_sjtsk dokument

.. automodule:: core.management.commands.transform_to_sjtsk
   :members: Command
   :undoc-members:
   :show-inheritance:

**Parametry:**

.. list-table::
   :header-rows: 1
   :widths: 30 20 20 30

   * - Název
     - Typ
     - Výchozí hodnota
     - Popis
   * - ``model``
     - ``str``
     - 
     - core.management.commands.transform_to_sjtsk.Command.add_arguments.model_help


``update_pristupnost_snapshot``
-------------------------------

Django management příkaz pro aktualizaci snímku přístupnosti projektů.

Tento příkaz prochází všechny projekty a aktualizuje jejich pole pristupnost_snapshot
pomocí metody set_pristupnost(). Projekty jsou zpracovávány v dávkách pro optimalizaci
výkonu a zamezení přílišnému zatížení databáze.

Parametry:
    - --batch-size: Velikost dávky pro zpracování (výchozí: 100)

Poznámka:
    - Pro projekty je dočasně potlačen signál (suppress_signal=True) aby nedošlo k nežádoucím vedlejším efektům během hromadné aktualizace

Příklady použití::

    python manage.py update_pristupnost_snapshot
    python manage.py update_pristupnost_snapshot --batch-size 200
    python manage.py update_pristupnost_snapshot --batch-size 50

.. automodule:: core.management.commands.update_pristupnost_snapshot
   :members: Command
   :undoc-members:
   :show-inheritance:

**Parametry:**

.. list-table::
   :header-rows: 1
   :widths: 30 20 20 30

   * - Název
     - Typ
     - Výchozí hodnota
     - Popis
   * - ``--batch-size``
     - ``int``
     - ``100``
     - core.management.commands.update_pristupnost_snapshot.Command.add_arguments.batch_size_help


``update_snapshot_fields``
--------------------------

Django management příkaz pro spuštění aktualizace snapshot fields.

Tento příkaz spustí sdílený cron task ``update_snapshot_fields``, který
provede potřebné přepočty a uložení snapshot hodnot do databáze.

Poznámka:
    - Příkaz nespouští aktualizaci synchronně, ale předává úlohu do asynchronního cron systému
    - Snapshot fields zahrnují předpočítané hodnoty pro optimalizaci výkonu

Příklady použití::

    python manage.py update_snapshot_fields

.. automodule:: core.management.commands.update_snapshot_fields
   :members: Command
   :undoc-members:
   :show-inheritance:


``write_value_to_redis``
------------------------

Django management příkaz pro zápis hodnoty do Redis.

Tento příkaz předá klíč a hodnotu do sdíleného cron tasku, který
provede zápis do Redis (asynchronně s nízkou prioritou).

Parametry:
    - key: Redis klíč
    - value: Hodnota, která se pod klíčem uloží

Příklady použití::

    python manage.py write_value_to_redis foo bar

.. automodule:: core.management.commands.write_value_to_redis
   :members: Command
   :undoc-members:
   :show-inheritance:

**Parametry:**

.. list-table::
   :header-rows: 1
   :widths: 30 20 20 30

   * - Název
     - Typ
     - Výchozí hodnota
     - Popis
   * - ``key``
     - ``str``
     - 
     - core.management.commands.write_value_to_redis.Command.add_arguments.key_help
   * - ``value``
     - ``str``
     - 
     - core.management.commands.write_value_to_redis.Command.add_arguments.value_help
