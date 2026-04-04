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

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.


   .. py:method:: navazany_objekt()

      Vrátí navázaný objekt (část dokumentu nebo dokumentační jednotku) podle typu vazby.

      **Návratová hodnota:**

      Vrací atribut objektu.



.. py:class:: Komponenta

   Databázový model komponenty.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.


   .. py:method:: ident_cely_safe()

      Vrátí identifikátor komponenty s pomlčkami nahrazenými podtržítky (vhodný pro použití v HTML atributech).

      **Návratová hodnota:**

      Vrací výsledek volání ``replace()``.


   .. py:method:: pocet_nalezu()

      Vrátí celkový počet nálezů (objektů a předmětů) přiřazených ke komponentě.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování.


   .. py:method:: get_absolute_url()

      Vrací absolute url.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``reverse()``, výsledek volání ``get_absolute_url()``.


   .. py:method:: get_permission_object()

      Vrací permission object.

      **Návratová hodnota:**

      Vrací výsledek volání ``get_permission_object()``.


   .. py:method:: create_transaction()

      Vytvoří transaction. v aplikaci.

      **Parametry:**

      - ``transaction_user``: Uživatel nebo osoba ``transaction_user``, v jejímž kontextu se operace provádí.

      **Návratová hodnota:**

      Vrací atribut objektu.


   .. py:method:: set_transaction_main_record()

      Nastaví transaction main record.


.. py:class:: KomponentaAktivita

   Databázový model aktivit komponenty.

