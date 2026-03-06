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

      :return: Vrací výsledek volání ``reverse()``.

   .. py:method:: __str__()

      Vrací textovou reprezentaci objektu.

      Textová reprezentace objektu.

      :return: Vrací hodnotu podle větve zpracování, typicky: atribut objektu, str.

   .. py:method:: set_odeslany()

      Metoda pro nastavení stavu odeslaný a uložení změny do historie pro externí zdroj.

      :param user: Parametr ``user`` se předává do volání ``Historie()``.

   .. py:method:: set_vraceny()

      Metoda pro vrácení o jeden stav méně a uložení změny do historie pro externí zdroj.

      :param user: Parametr ``user`` se předává do volání ``Historie()``.
      :param new_state: Stavová nebo časová hodnota `new_state` používaná při rozhodování logiky.
      :param poznamka: Parametr ``poznamka`` se předává do volání ``Historie()``.

   .. py:method:: set_potvrzeny()

      Metoda pro nastavení stavu potvrzená a uložení změny do historie pro externí zdroj.

      Pokud je ident dočasný nahrazení identem stálým.

      :param user: Parametr ``user`` se předává do volání ``Historie()``.

   .. py:method:: set_zapsany()

      Metoda pro nastavení stavu zapsaný a uložení změny do historie pro externí zdroj.

      :param user: Parametr ``user`` se předává do volání ``Historie()``.

   .. py:method:: get_permission_object()

      Vrací permission object.

      :return: Vrací proměnná ``self``.

   .. py:method:: get_create_user()

      Vrací create user.

      :return: Vrací n-tici.

   .. py:method:: get_create_org()

      Vrací create org.

      :return: Vrací n-tici.

   .. py:method:: set_snapshots()

      Nastaví snapshots. v aplikaci.

   .. py:method:: redis_snapshot_id()

      Provádí operaci redis snapshot id.

      :return: Vrací hodnotu podle větve zpracování.

   .. py:method:: generate_redis_snapshot()

      Vygeneruje redis snapshot.

      :return: Vrací n-tici.

   .. py:method:: check_set_permanent_ident()

      Ověří set permanent ident.

      :return: Vrací proměnná ``historie_poznamka``.


.. py:class:: ExterniZdrojAutor

   Databázový model autora externího zdroje se zohledněním pořadí zadání.

   **Metody:**

   .. py:method:: get_osoba()

      Vrací osoba. v aplikaci.

      :return: Vrací atribut objektu.


.. py:class:: ExterniZdrojEditor

   Databázový model editora externího zdroje se zohledněním pořadí zadání.

   **Metody:**

   .. py:method:: get_osoba()

      Vrací osoba. v aplikaci.

      :return: Vrací atribut objektu.


.. py:class:: ExterniZdrojSekvence

   Model pro tabulku se sekvencemi externích zdrojů.


Funkce
------

.. py:function:: get_perm_ez_ident()

   Funkce pro výpočet ident celý pro externí zdroj.

   Funkce vrátí pro permanentní ident ID podle sekvence externího zdroje.

   :return: Vrací hodnotu podle větve zpracování.
   :raises MaximalIdentNumberError: Vyvolá se při splnění podmínky ``sequence.sekvence >= MAXIMUM``; nebo při splnění podmínky ``missing[0] >= MAXIMUM``.
