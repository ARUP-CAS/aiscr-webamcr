Konfigurace Fedora repository
==============================

Tato stránka popisuje spojení aplikace s Fedorou a provozní postup, kterým se Fedora repozitář vygeneruje od začátku
(od zformátování disku po spuštění ``generate_metadata_fast``). Datový model a struktura metadat jsou popsané jinde
(viz :doc:`/05_integrace/fedora_repository`).

Spojení aplikace s Fedorou
--------------------------

Aplikace se k Fedoře připojuje podle klíčů ``FEDORA_*`` v ``db_conf`` (viz :doc:`secrets`).
Fedora běží ve stejné interní síti jako aplikace a není vystavená ven; na produkci se volá
přímo kontejner přes HTTP (``FEDORA_PROTOCOL`` ``http``, ``FEDORA_SERVER_HOSTNAME`` ``fcrepo``,
``FEDORA_PORT_NUMBER`` ``8080``). Přihlašuje se HTTP Basic autentizací (``FEDORA_USER``,
``FEDORA_ADMIN_USER``).

Všechny požadavky do Fedory (``core/repository_connector.py``) se posílají s ``verify=False``,
tedy bez ověření TLS certifikátu. Jde o záměrné rozhodnutí, ne o chybu: provoz do Fedory neopouští
interní síť a při ``http`` se TLS vůbec nepoužije. Kdyby se Fedora volala přes ``https``
se self-signed certifikátem, distribuce vlastní CA do kontejnerů by k bezpečnosti interní sítě
nic nepřidala. Pokud by se Fedora někdy zpřístupnila mimo interní síť, je potřeba ověřování
certifikátu zapnout.

Timeouty požadavků do Fedory nastavují klíče ``FEDORA_CONNECT_TIMEOUT``, ``FEDORA_READ_TIMEOUT``
a ``FEDORA_CONTENT_READ_TIMEOUT`` (viz :doc:`secrets`).


Postup generování Fedora repozitáře
-----------------------------------

Postup vznikl při testovacím generování na vývojovém serveru (běh trval zhruba 28 hodin). Cesty
(``/mnt/fcrepo``, ``/opt/bin``, ``/opt/bin/init-fcrepo/``) jsou cesty testovacího serveru a na jiném stroji se mohou
lišit. Názvy kontejnerů (``fcrepo``, ``fcrepo-postgres``) a služby ve Swarmu (``swarm_webamcr_web``) jsou stejné
všude.

Před zahájením:

* importovat produkční databázi (pro testovací server je nutná anonymizace, viz níže),
* nastavit odstávku,
* odpojit aktualizaci Digiarchivu.

Formátování disku
~~~~~~~~~~~~~~~~~

Disk s daty Fedory se formátuje, místo aby se mazal jeho obsah: smazání adresáře Fedory s desítkami milionů souborů
trvá hodiny, zatímco ``mkfs.xfs`` jen několik sekund.

.. warning::

   Formátování je **nevratné**. Zařízení v příkazu ``mkfs.xfs`` (``<ZARIZENI>``) se nikdy nekopíruje z jiného stroje.
   Před formátováním vždy ověřte, že ``<ZARIZENI>`` je skutečně disk Fedory a že je odpojený:

   .. code-block:: bash

      lsblk -f
      findmnt /mnt/fcrepo      # po odpojení nesmí nic vypsat

   Zařízení musí odpovídat tomu, co je v ``/etc/fstab`` u ``/mnt/fcrepo`` a co ukazuje ``lsblk`` u UUID zjištěného
   v kroku 1.

1. Záloha parametrů
^^^^^^^^^^^^^^^^^^^

Uložit UUID filesystému a aktuální parametry XFS:

.. code-block:: bash

   findmnt -n -o UUID /mnt/fcrepo
   grep -E 'fcrepo' /etc/fstab
   xfs_info /mnt/fcrepo > ~/fcrepo_xfs_info.before

2. Zastavení Fedory a odpojení disku
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   sudo docker stop fcrepo
   sudo docker stop fcrepo-postgres
   sudo fuser -vm /mnt/fcrepo
   sudo umount /mnt/fcrepo

Výstup ``fuser`` nesmí obsahovat nic kromě řádku ``/mnt/fcrepo: root kernel mount /mnt/fcrepo``. Jinak disk někdo
používá a nelze ho odpojit.

3. Formátování se zachovaným UUID
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Zachované UUID zajistí, že záznam v ``/etc/fstab`` zůstane platný.

.. code-block:: bash

   sudo mkfs.xfs -f -m uuid=<UUID> -i maxpct=50 <ZARIZENI>

``<UUID>`` je hodnota získaná v kroku 1, ``<ZARIZENI>`` je blokové zařízení ověřené podle výstrahy výše.

4. Připojení disku a základní struktura
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   sudo mount /mnt/fcrepo        # podle fstab
   sudo mkdir -p /mnt/fcrepo/fcrepo-home/data /mnt/fcrepo/fcrepo-home/db

5. Kontrola
^^^^^^^^^^^

Parametry nového filesystému se musí shodovat s původními. Rozdíl smí být nanejvýš v řádcích, které se mění
formátováním (např. čas vytvoření), nikoli v geometrii ani ``maxpct``:

.. code-block:: bash

   xfs_info /mnt/fcrepo | diff ~/fcrepo_xfs_info.before -

Spuštění Fedory
~~~~~~~~~~~~~~~

Nejdřív se spustí databáze:

.. code-block:: bash

   sudo docker start fcrepo-postgres

Při generování se do Fedory zapisují miliony požadavků, proto je potřeba snížit úroveň logování na ``WARN``.
Na testovacím serveru to dělá skript ``run-fcrepo_6.5.1_warn.sh`` v ``/opt/bin``. Není součástí repozitáře, jde
o serverový skript, který spouští kontejner ``fcrepo`` se stejnou konfigurací jako běžně, jen s úrovní logování
``WARN``. Na jiném stroji je potřeba vytvořit obdobný skript.

.. code-block:: bash

   sudo docker rm fcrepo
   cd /opt/bin
   sudo ./run-fcrepo_6.5.1_warn.sh

Příprava databáze Fedory
~~~~~~~~~~~~~~~~~~~~~~~~

Pokud se Fedora spouští nad novou (prázdnou) PostgreSQL databází, je potřeba ručně přidat index ``containment_idx5``:

.. code-block:: sql

   CREATE INDEX IF NOT EXISTS containment_idx5 ON containment (fedora_id varchar_pattern_ops);

Jde o obejití chyby ve Fedoře: na PostgreSQL 16 a novější se index při vytváření schématu tiše nevytvoří a bez něj
zápisy do Fedory výrazně zpomalují s tím, jak repozitář roste.

Inicializace struktury Fedory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Skript ``fedora-init.py`` vytvoří základní kontejnery, ACL pravidla a schéma metadat. V repozitáři je jako
``bin/fedora/fedora-init.py``, na testovacím serveru se spouští z ``/opt/bin/init-fcrepo/``, kam se zkopíruje.
Heslo ``fedoraAdmin`` čte ze souboru ``/var/run/secrets/tomcat_users``, takže musí běžet tam, kde je tento secret
dostupný.

.. code-block:: bash

   cd /opt/bin/init-fcrepo/
   python3 fedora-init.py

Vypnutí cron tasků
~~~~~~~~~~~~~~~~~~

U databáze importované z produkce jsou naplánované úlohy, které by se během generování spouštěly zbytečně
a zatěžovaly Fedoru i databázi. Před generováním je proto vypněte a po dokončení zase zapněte
(viz „Obnova nastavení“ níže).

Anonymizace databáze (volitelné)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Na testovacím serveru se importovaná produkční databáze anonymizuje příkazem ``anonymizace_dat`` s přepínačem
``--potvrzuji-testovaci-server`` (popis příkazu viz :doc:`/04_django_aplikace/04_01_core/management_commands`).
Anonymizace funguje až po aktualizaci katastrů, protože se odkazuje na hranice okresů.

.. code-block:: bash

   sudo docker exec -i $(sudo docker ps -q -f name=swarm_webamcr_web) \
       python3 manage.py anonymizace_dat --potvrzuji-testovaci-server --settings=webclient.settings.production

Spuštění generování
~~~~~~~~~~~~~~~~~~~

Generování běží hodiny, proto se spouští na pozadí v ``tmux``:

.. code-block:: bash

   tmux new -s fedora

Počet workerů (``--workers``) upravte podle výkonu serveru. Všechny přepínače příkazu ``generate_metadata_fast`` jsou
popsané v :doc:`/04_django_aplikace/04_01_core/management_commands`. Hlášky úrovně DEBUG, INFO a WARN se ze stderr
odfiltrují, aby zůstaly vidět jen skutečné chyby:

.. code-block:: bash

   sudo docker exec $(sudo docker ps -q -f name=swarm_webamcr_web) \
       python3 manage.py generate_metadata_fast --workers 10 --max-retries 20 --aktualizovat-db \
       --settings=webclient.settings.production 2> >(grep -vE ' (DEBUG|INFO|WARN) ' >&2)

Z ``tmux`` se odpojíte klávesami ``Ctrl+b``, ``d`` a znovu se připojíte příkazem ``tmux attach -t fedora``.

Doba běhu
^^^^^^^^^

Testovací běh trval zhruba 28 hodin. Jde jen o orientační údaj: doba závisí na počtu záznamů, na počtu workerů
(``--workers``) i na výkonu disku a databáze Fedory (viz index ``containment_idx5`` výše).

Jak poznat, že běh dopadl dobře
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Příkaz skončí nulovým exit kódem. Při selhání jakéhokoli záznamu nebo při nesrovnalostech v závěrečné kontrole
  konzistence DB vs. Fedora je exit kód nenulový.
* Na konci proběhne kontrola konzistence (lze ji vypnout ``--bez-kontroly`` nebo spustit samostatně
  ``--jen-kontrola``).
* Pojistka ``--max-selhani-po-sobe`` ukončí běh po sérii selhání v řadě, takže při výpadku Fedory příkaz neběží
  naprázdno, aniž by si toho někdo všiml.

Navázání po pádu
^^^^^^^^^^^^^^^^

Po pádu nebo přerušení se navazuje stejným příkazem rozšířeným o ``--force`` a ``--start-with-pk`` s hodnotou těsně
za posledním úspěšně zpracovaným záznamem.

Obnova nastavení
~~~~~~~~~~~~~~~~

Po dokončení generování:

* vrátit běžné logování Fedory: ``sudo docker rm fcrepo`` a spustit kontejner standardním skriptem (bez ``WARN``),
* zapnout aktualizaci a indexování Digiarchivu,
* vypnout odstávku a znovu zapnout cron tasky.
