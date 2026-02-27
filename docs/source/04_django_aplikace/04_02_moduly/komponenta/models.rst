KOMPONENTA modely
=================

Definice modelů.

Třídy
------

.. py:class:: KomponentaVazby

   Databázový model vazeb komponenty.
   Model se používa k napojení na jednotlivé záznamy.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: navazany_objekt()

      Provádí operaci navazany objekt.

      :return: Vrací výsledek provedené operace.


.. py:class:: Komponenta

   Databázový model komponenty.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: ident_cely_safe()

      Provádí operaci ident cely safe.

      :return: Vrací výsledek provedené operace.

   .. py:method:: pocet_nalezu()

      Provádí operaci pocet nalezu.

      :return: Vrací výsledek provedené operace.

   .. py:method:: get_absolute_url()

      Vrací absolute url.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_permission_object()

      Vrací permission object.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: create_transaction()

      Vytvoří transaction.

      :param transaction_user: Vstupní hodnota ``transaction_user`` pro danou operaci.
      :return: Vrací nově vytvořený výsledek operace.

   .. py:method:: set_transaction_main_record()

      Nastaví transaction main record.

      :return: Vrací výsledek provedené operace.


.. py:class:: KomponentaAktivita

   Databázový model aktivit komponenty.

