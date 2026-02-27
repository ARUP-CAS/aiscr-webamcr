UZIVATEL signály
================

Definice signálů.

Funkce
------

.. py:function:: orgnaizace_save_metadata(sender, instance)

   Provádí operaci orgnaizace save metadata.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
   :return: Vrací výsledek provedené operace.

.. py:function:: osoba_save_metadata(sender, instance)

   Provádí operaci osoba save metadata.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
   :return: Vrací výsledek provedené operace.

.. py:function:: create_ident_cely(sender, instance)

   Přidelení identu celý pro usera.

.. py:function:: user_post_save_method(sender, instance, created)

   Provádí operaci user post save method.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param created: Vstupní hodnota ``created`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
   :return: Vrací výsledek provedené operace.

.. py:function:: send_deactivation_email(sender, instance)

   Signál pro poslání deaktivačního emailu uživately.

.. py:function:: send_account_confirmed_email(sender, instance, created)

   signál pro zaslání emailu uživately o jeho konfirmaci.

.. py:function:: delete_user_connections(sender, instance)

   Odstraní user connections.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param args: Dodatečné poziční argumenty předané voláním.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
   :return: Vrací výsledek operace odstranění.

.. py:function:: delete_profile(sender, instance)

   Signál pro zaslání emailu uživately o jeho smazání.

.. py:function:: osoba_delete_repository_container(sender, instance)

   Provádí operaci osoba delete repository container.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
   :return: Vrací výsledek provedené operace.

.. py:function:: organizace_delete_repository_container(sender, instance)

   Provádí operaci organizace delete repository container.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param instance: Vstupní hodnota ``instance`` pro danou operaci.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
   :return: Vrací výsledek provedené operace.

.. py:function:: log_user_signin(sender, user, request)

   Provádí operaci log user signin.

   :param sender: Vstupní hodnota ``sender`` pro danou operaci.
   :param user: Vstupní hodnota ``user`` pro danou operaci.
   :param request: Django HTTP požadavek použitý při zpracování.
   :param kwargs: Dodatečné pojmenované argumenty předané voláním.
   :return: Vrací výsledek provedené operace.
