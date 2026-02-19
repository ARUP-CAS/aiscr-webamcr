EZ modely
=========

Definice modelů.

Třídy
------

.. py:class:: ExterniZdroj

   Class pro db model externí zdroj.

   **Metody:**

   .. py:method:: get_absolute_url()

      Metoda pro získaní absolut url záznamu podle identu.

   .. py:method:: __str__()

   .. py:method:: set_odeslany()

      Metoda pro nastavení stavu odeslaný a uložení změny do historie pro externí zdroj.

   .. py:method:: set_vraceny()

      Metoda pro vrácení o jeden stav méně a uložení změny do historie pro externí zdroj.

   .. py:method:: set_potvrzeny()

      Metoda pro nastavení stavu potvrzená a uložení změny do historie pro externí zdroj.
      Pokud je ident dočasný nahrazení identem stálým.

   .. py:method:: set_zapsany()

      Metoda pro nastavení stavu zapsaný a uložení změny do historie pro externí zdroj.

   .. py:method:: get_permission_object()

   .. py:method:: get_create_user()

   .. py:method:: get_create_org()

   .. py:method:: set_snapshots()

   .. py:method:: redis_snapshot_id()

   .. py:method:: generate_redis_snapshot()

   .. py:method:: check_set_permanent_ident()


.. py:class:: ExterniZdrojAutor

   Class pro db model autora externího zdroje, zohledňuje pořadí zadání.

   **Metody:**

   .. py:method:: get_osoba()


.. py:class:: ExterniZdrojEditor

   Class pro db model editora externího zdroje, zohledňuje pořadí zadání.

   **Metody:**

   .. py:method:: get_osoba()


.. py:class:: ExterniZdrojSekvence

   Model pro tabulku se sekvencemi externích zdrojů.


Funkce
------

.. py:function:: get_perm_ez_ident()

   Funkce pro výpočet ident celý pro externí zdroj.
   Funkce vráti pro permanentní ident id podle sekvence externího zdroje.
