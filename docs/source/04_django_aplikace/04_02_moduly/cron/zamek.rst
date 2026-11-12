CRON zamek
==========

Modul zamek.

Přehled modulu
--------------

Zámky zabraňující souběhu dlouhých plánovaných úloh.

Vzor je stejný jako u :func:`heslar.ruian_sync.zamek.ruian_sync_lock`: Postgres advisory lock
na úrovni session. Nemá TTL, takže nemůže vypršet uprostřed několikahodinového běhu, a uvolní se
i při tvrdém pádu procesu, protože ho Postgres pustí se zánikem spojení.

Funkce
------

.. py:function:: cron_task_lock(key)

   Zajistí, že úloha se stejným ``key`` neběží ve dvou instancích současně.

   Souběžné běhy by procházely stejný seznam projektů a zapisovaly do stejných záznamů ve Fedoře,
   což vede ke konfliktu transakcí (HTTP 409) a ke ztrátě zbytku práce druhého běhu.

   :param key: Celočíselný klíč Postgres advisory locku, jedinečný pro každou úlohu.
   :return: Generátor vracející ``True``, když byl zámek získán, jinak ``False``; volající
       v druhém případě běh přeskočí.
