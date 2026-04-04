UZIVATEL signály
================

Definice signálů.

Funkce
------

.. py:function:: orgnaizace_save_metadata(sender, instance)

   Provádí operaci orgnaizace save metadata.

   **Parametry:**

   - ``sender``: Parametr ``sender`` slouží jako vstup pro logiku funkce ``orgnaizace_save_metadata``.
   - ``instance``: Parametr ``instance`` předává se do volání ``debug()``, ``get_or_create_transaction()``, pracuje se s atributy ``ident_cely``, ``suppress_signal``, ovlivňuje větvení podmínek.
   - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``orgnaizace_save_metadata``.


.. py:function:: osoba_save_metadata(sender, instance)

   Provádí operaci osoba save metadata.

   **Parametry:**

   - ``sender``: Parametr ``sender`` slouží jako vstup pro logiku funkce ``osoba_save_metadata``.
   - ``instance``: Parametr ``instance`` předává se do volání ``debug()``, ``get_or_create_transaction()``, pracuje se s atributy ``ident_cely``, ``suppress_signal``, ovlivňuje větvení podmínek.
   - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``osoba_save_metadata``.


.. py:function:: create_ident_cely(sender, instance)

   Přidelení identu celý pro usera.

   **Parametry:**

   - ``sender``: Parametr ``sender`` slouží jako vstup pro logiku funkce ``create_ident_cely``.
   - ``instance``: Parametr ``instance`` předává se do volání ``filter()``, ``check_container_deleted_or_not_exists()``, pracuje se s atributy ``id``, ``old``, ovlivňuje větvení podmínek.
   - ``kwargs``: Parametr ``kwargs`` se předává do volání ``len()``, ovlivňuje větvení podmínek.

   **Výjimky:**

   - ``ValidationError``: Vyvolá se při splnění podmínky ``not FedoraRepositoryConnector.check_container_deleted_or_not_exists(instance.ident_cely, 'uzivatel')``.


.. py:function:: user_post_save_method(sender, instance, created)

   Provádí operaci user post save method.

   **Parametry:**

   - ``sender``: Parametr ``sender`` se předává do volání ``send_deactivation_email()``, ``send_account_confirmed_email()``.
   - ``instance``: Parametr ``instance`` předává se do volání ``debug()``, ``send_deactivation_email()``, pracuje se s atributy ``active_transaction``, ``ident_cely``, ovlivňuje větvení podmínek.
   - ``created``: Parametr ``created`` předává se do volání ``send_account_confirmed_email()``.
   - ``kwargs``: Parametr ``kwargs`` se předává do volání ``send_deactivation_email()``.


.. py:function:: send_deactivation_email(sender, instance)

   Signál pro poslání deaktivačního emailu uživately.

   **Parametry:**

   - ``sender``: Parametr ``sender`` slouží jako vstup pro logiku funkce ``send_deactivation_email``.
   - ``instance``: Parametr ``instance`` předává se do volání ``debug()``, ``hasattr()``, pracuje se s atributy ``ident_cely``, ``old``, ovlivňuje větvení podmínek.
   - ``kwargs``: Parametr ``kwargs`` pracuje se s atributy ``get``, ovlivňuje větvení podmínek.


.. py:function:: send_account_confirmed_email(sender, instance, created)

   signál pro zaslání emailu uživately o jeho konfirmaci.

   **Parametry:**

   - ``sender``: Parametr ``sender`` slouží jako vstup pro logiku funkce ``send_account_confirmed_email``.
   - ``instance``: Parametr ``instance`` předává se do volání ``debug()``, ``send_eu02()``, pracuje se s atributy ``ident_cely``, ``created_from_admin_panel``, ovlivňuje větvení podmínek.
   - ``created``: Parametr ``created`` předává se do volání ``debug()``, ovlivňuje větvení podmínek.


.. py:function:: delete_user_connections(sender, instance)

   Odstraní user connections.

   **Parametry:**

   - ``sender``: Parametr ``sender`` slouží jako vstup pro logiku funkce ``delete_user_connections``.
   - ``instance``: Parametr ``instance`` předává se do volání ``debug()``, ``save_record_deletion_record()``, pracuje se s atributy ``ident_cely``, ``deleted_by_user``, ovlivňuje větvení podmínek.
   - ``args``: Parametr ``args`` slouží jako vstup pro logiku funkce ``delete_user_connections``.
   - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``delete_user_connections``.


.. py:function:: delete_profile(sender, instance)

   Signál pro zaslání emailu uživately o jeho smazání.

   **Parametry:**

   - ``sender``: Parametr ``sender`` slouží jako vstup pro logiku funkce ``delete_profile``.
   - ``instance``: Parametr ``instance`` předává se do volání ``debug()``, ``send_eu03()``, pracuje se s atributy ``ident_cely``, ``active_transaction``, ovlivňuje větvení podmínek.
   - ``args``: Parametr ``args`` slouží jako vstup pro logiku funkce ``delete_profile``.
   - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``delete_profile``.


.. py:function:: osoba_delete_repository_container(sender, instance)

   Provádí operaci osoba delete repository container.

   **Parametry:**

   - ``sender``: Parametr ``sender`` slouží jako vstup pro logiku funkce ``osoba_delete_repository_container``.
   - ``instance``: Parametr ``instance`` předává se do volání ``debug()``, ``get_or_create_transaction()``, pracuje se s atributy ``ident_cely``, ``record_deletion``.
   - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``osoba_delete_repository_container``.


.. py:function:: organizace_delete_repository_container(sender, instance)

   Provádí operaci organizace delete repository container.

   **Parametry:**

   - ``sender``: Parametr ``sender`` slouží jako vstup pro logiku funkce ``organizace_delete_repository_container``.
   - ``instance``: Parametr ``instance`` předává se do volání ``debug()``, ``get_or_create_transaction()``, pracuje se s atributy ``ident_cely``, ``record_deletion``.
   - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``organizace_delete_repository_container``.


.. py:function:: log_user_signin(sender, user, request)

   Provádí operaci log user signin.

   **Parametry:**

   - ``sender``: Parametr ``sender`` slouží jako vstup pro logiku funkce ``log_user_signin``.
   - ``user``: Parametr ``user`` se předává do volání ``create()``.
   - ``request``: Parametr ``request`` pracuje se s atributy ``META``.
   - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``log_user_signin``.

