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

   .. py:method:: navazany_objekt()

      Provádí operaci navazany objekt.


.. py:class:: Komponenta

   Databázový model komponenty.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: ident_cely_safe()

      Provádí operaci ident cely safe.

   .. py:method:: pocet_nalezu()

      Provádí operaci pocet nalezu.

   .. py:method:: get_absolute_url()

      Vrací absolute url.

   .. py:method:: get_permission_object()

      Vrací permission object.

   .. py:method:: create_transaction()

      Vytvoří transaction. v aplikaci.

      :param transaction_user: Vstupní hodnota ``transaction_user`` pro danou operaci.

   .. py:method:: set_transaction_main_record()

      Nastaví transaction main record.


.. py:class:: KomponentaAktivita

   Databázový model aktivit komponenty.

