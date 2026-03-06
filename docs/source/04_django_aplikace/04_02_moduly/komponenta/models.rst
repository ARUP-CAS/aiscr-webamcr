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

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.

   .. py:method:: navazany_objekt()

      Provádí operaci navazany objekt.

      :return: Vrací atribut objektu.


.. py:class:: Komponenta

   Databázový model komponenty.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.

   .. py:method:: ident_cely_safe()

      Provádí operaci ident cely safe.

      :return: Vrací výsledek volání ``replace()``.

   .. py:method:: pocet_nalezu()

      Provádí operaci pocet nalezu.

      :return: Vrací hodnotu podle větve zpracování.

   .. py:method:: get_absolute_url()

      Vrací absolute url.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``reverse()``, výsledek volání ``get_absolute_url()``.

   .. py:method:: get_permission_object()

      Vrací permission object.

      :return: Vrací výsledek volání ``get_permission_object()``.

   .. py:method:: create_transaction()

      Vytvoří transaction. v aplikaci.

      :param transaction_user: Uživatel nebo osoba ``transaction_user``, v jejímž kontextu se operace provádí.

      :return: Vrací atribut objektu.

   .. py:method:: set_transaction_main_record()

      Nastaví transaction main record.


.. py:class:: KomponentaAktivita

   Databázový model aktivit komponenty.

