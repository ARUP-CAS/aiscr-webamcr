PAS signály
===========

Definice signálů.

Funkce
------

.. py:function:: create_dokument_vazby(sender, instance)

   Metoda pro vytvoření historických a souborových vazeb samostatnýho náleze.

   Metoda se volá pred uložením záznamu.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``create_dokument_vazby``.
   :param instance: Parametr ``instance`` předává se do volání ``debug()``, pracuje se s atributy ``ident_cely``, ``pk``, ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``create_dokument_vazby``.

.. py:function:: save_metadata_samostatny_nalez(sender, instance, created)

   Uloží metadata samostatny nalez.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``save_metadata_samostatny_nalez``.
   :param instance: Parametr ``instance`` předává se do volání ``debug()``, ``check_if_task_queued()``, pracuje se s atributy ``ident_cely``, ``suppress_signal``, ovlivňuje větvení podmínek.
   :param created: Parametr ``created`` slouží jako vstup pro logiku funkce ``save_metadata_samostatny_nalez``.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``save_metadata_samostatny_nalez``.

.. py:function:: dokument_delete_container_soubor_vazby(sender, instance)

   Před smazáním samostatného nálezu označí záznam ve Fedoře jako smazaný a odstraní jeho soubory a historii v DB.

   Zápis do Fedory probíhá hned (uvnitř DB transakce), aby chyba Fedory (např. 409 při souběžném
   zápisu jiné transakce) vedla k rollbacku smazání v DB. Metadata projektu se zapisují až
   v ``samostatny_nalez_delete_update_projekt`` po smazání řádku, aby už nález neobsahovala.

   :param sender: Model, který signál vyvolal (``SamostatnyNalez``).
   :param instance: Mazaný samostatný nález; používá se jeho ``active_transaction``, ``soubory`` a ``historie``.
   :param kwargs: Dodatečné argumenty předané Django signálem.

.. py:function:: samostatny_nalez_delete_update_projekt(sender, instance)

   Po smazání samostatného nálezu přegeneruje metadata projektu ve Fedoře a případně uzavře transakci.

   Metadata projektu se zapisují ještě uvnitř DB transakce, takže konflikt ve Fedoře (409 při souběžném
   mazání jiného nálezu téhož projektu) se projeví výjimkou ve view a smazání v DB se odroluje.
   Do ``transaction.on_commit`` se odkládá jen commit Fedora transakce (#4437). Selhání samotného
   commitu Fedory po commitu DB tím pokryté není; zaloguje se jako ERROR s ``ident_cely``
   (``core_repository_connector.FedoraTransaction.commit_transaction.failed``).

   :param sender: Model, který signál vyvolal (``SamostatnyNalez``).
   :param instance: Smazaný samostatný nález; používá se jeho ``projekt``, ``active_transaction``
       a ``close_active_transaction_when_finished``.
   :param kwargs: Dodatečné argumenty předané Django signálem.

.. py:function:: save_uzivatel_spoluprce(sender, instance)

   Uloží uzivatel spoluprce.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``save_uzivatel_spoluprce``.
   :param instance: Parametr ``instance`` předává se do volání ``debug()``, pracuje se s atributy ``pk``, ``suppress_signal``, ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``save_uzivatel_spoluprce``.

.. py:function:: delete_uzivatel_spoluprce_connections(sender, instance)

   Odstraní uzivatel spoluprce connections.

   :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``delete_uzivatel_spoluprce_connections``.
   :param instance: Parametr ``instance`` předává se do volání ``debug()``, pracuje se s atributy ``pk``, ``active_transaction``, ovlivňuje větvení podmínek.
   :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``delete_uzivatel_spoluprce_connections``.
