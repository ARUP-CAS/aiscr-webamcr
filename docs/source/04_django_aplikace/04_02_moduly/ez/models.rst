EZ modely
=========

Definice modelů.

Třídy
------

.. py:class:: ExterniZdroj

   Databázový model externího zdroje.

   **Metody:**

   .. py:method:: get_absolute_url()

      Metoda pro získaní absolut url záznamu podle identu.

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      :return: Vrací výsledek provedené operace.

   .. py:method:: set_odeslany()

      Metoda pro nastavení stavu odeslaný a uložení změny do historie pro externí zdroj.

      :param user: Popis parametru ``user``.

   .. py:method:: set_vraceny()

      Metoda pro vrácení o jeden stav méně a uložení změny do historie pro externí zdroj.

      :param user: Popis parametru ``user``.
      :param new_state: Popis parametru ``new_state``.
      :param poznamka: Popis parametru ``poznamka``.

   .. py:method:: set_potvrzeny()

      Metoda pro nastavení stavu potvrzená a uložení změny do historie pro externí zdroj.

      Pokud je ident dočasný nahrazení identem stálým.

      :param user: Popis parametru ``user``.

   .. py:method:: set_zapsany()

      Metoda pro nastavení stavu zapsaný a uložení změny do historie pro externí zdroj.

      :param user: Popis parametru ``user``.

   .. py:method:: get_permission_object()

      Vrací permission object.

   .. py:method:: get_create_user()

      Vrací create user.

   .. py:method:: get_create_org()

      Vrací create org.

   .. py:method:: set_snapshots()

      Nastaví snapshots. v aplikaci.

   .. py:method:: redis_snapshot_id()

      Provádí operaci redis snapshot id.

   .. py:method:: generate_redis_snapshot()

      Vygeneruje redis snapshot.

   .. py:method:: check_set_permanent_ident()

      Ověří set permanent ident.


.. py:class:: ExterniZdrojAutor

   Databázový model autora externího zdroje se zohledněním pořadí zadání.

   **Metody:**

   .. py:method:: get_osoba()

      Vrací osoba. v aplikaci.


.. py:class:: ExterniZdrojEditor

   Databázový model editora externího zdroje se zohledněním pořadí zadání.

   **Metody:**

   .. py:method:: get_osoba()

      Vrací osoba. v aplikaci.


.. py:class:: ExterniZdrojSekvence

   Model pro tabulku se sekvencemi externích zdrojů.


Funkce
------

.. py:function:: get_perm_ez_ident()

   Funkce pro výpočet ident celý pro externí zdroj.

   Funkce vrátí pro permanentní ident ID podle sekvence externího zdroje.
