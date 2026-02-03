Management příkazy
==================

Dokumentace všech Django management příkazů v aplikaci.

Spuštění v Docker kontejneru
----------------------------

Pokud aplikace běží v kontejneru, je možné buď nejprve spustit terminál v kontejneru a následně zadat příkaz,
případně spustit příkaz přímo bez otevření interaktivního shellu.

**Bez swarm módu (vývoj):**

Tento postup se využívá pro vývojové prostředí, proto se příkazy spouští s vývojovým nastavením ``--settings=webclient.settings.dev``.

1. Zjistěte ID běžícího kontejneru:

   .. code-block:: bash

      docker ps

2. Spusťte shell v kontejneru (například s ID ``fdd99a0b6c90``):

   .. code-block:: bash

      docker exec -it aiscr-webamcr-web /bin/sh

3. Poté spusťte požadovaný příkaz:

   .. code-block:: bash

      python manage.py <název_příkazu> [parametry] --settings=webclient.settings.dev

Alternativně je možné vše zapsat do jednoho příkazu (bez otevření interaktivního shellu):

.. code-block:: bash

   docker exec -it $(docker ps -q -f name=aiscr-webamcr-web) python manage.py <název_příkazu> [parametry] --settings=webclient.settings.dev

**Se swarm módem (produkce):**

Swarm mód se používá pro produkční nasazení, proto se příkazy spouští s produkčním nastavením ``--settings=webclient.settings.production``.

1. Zjistěte ID běžícího kontejneru:

   .. code-block:: bash

      sudo docker ps

2. Spusťte shell v kontejneru:

   .. code-block:: bash

      sudo docker exec -it <ID_kontejneru> /bin/sh

3. Poté spusťte požadovaný příkaz:

   .. code-block:: bash

      python3 manage.py <název_příkazu> [parametry] --settings=webclient.settings.production

Alternativně je možné vše zapsat do jednoho příkazu (bez otevření interaktivního shellu):

.. code-block:: bash

   docker exec -it $(sudo docker ps -q -f name=swarm_webamcr_web) python3 manage.py <název_příkazu> [parametry] --settings=webclient.settings.production


``check_pian_properties``
-------------------------

.. automodule:: core.management.commands.check_pian_properties
   :members: Command
   :undoc-members:


``generate_metadata``
---------------------

.. automodule:: core.management.commands.generate_metadata
   :members: Command
   :undoc-members:

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

.. automodule:: core.management.commands.generate_thumbs
   :members: Command
   :undoc-members:

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

.. automodule:: core.management.commands.import_permissions
   :members: Command
   :undoc-members:


``remove_gps_data``
-------------------

.. automodule:: core.management.commands.remove_gps_data
   :members: Command
   :undoc-members:

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

.. automodule:: core.management.commands.save_files_from_storage
   :members: Command
   :undoc-members:

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

.. automodule:: core.management.commands.save_single_file_from_storage
   :members: Command
   :undoc-members:

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

.. automodule:: core.management.commands.transform_to_sjtsk
   :members: Command
   :undoc-members:

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

.. automodule:: core.management.commands.update_pristupnost_snapshot
   :members: Command
   :undoc-members:

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

.. automodule:: core.management.commands.update_snapshot_fields
   :members: Command
   :undoc-members:


``write_value_to_redis``
------------------------

.. automodule:: core.management.commands.write_value_to_redis
   :members: Command
   :undoc-members:

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
