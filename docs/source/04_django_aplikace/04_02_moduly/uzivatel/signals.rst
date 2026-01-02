UZIVATEL signály
================

Definice signálů.

Funkce
------

.. py:function:: orgnaizace_save_metadata(sender, instance)

   Popis není k dispozici.

.. py:function:: osoba_save_metadata(sender, instance)

   Popis není k dispozici.

.. py:function:: create_ident_cely(sender, instance)

   Přidelení identu celý pro usera.

.. py:function:: user_post_save_method(sender, instance, created)

   Popis není k dispozici.

.. py:function:: send_deactivation_email(sender, instance)

   Signál pro poslání deaktivačního emailu uživately.

.. py:function:: send_account_confirmed_email(sender, instance, created)

   signál pro zaslání emailu uživately o jeho konfirmaci.

.. py:function:: delete_user_connections(sender, instance)

   Popis není k dispozici.

.. py:function:: delete_profile(sender, instance)

   Signál pro zaslání emailu uživately o jeho smazání.

.. py:function:: osoba_delete_repository_container(sender, instance)

   Popis není k dispozici.

.. py:function:: organizace_delete_repository_container(sender, instance)

   Popis není k dispozici.

.. py:function:: log_user_signin(sender, user, request)

   Popis není k dispozici.
