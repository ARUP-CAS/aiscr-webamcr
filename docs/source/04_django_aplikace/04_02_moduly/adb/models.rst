ADB modely
==========

Definice modelů.

Třídy
------

.. py:class:: Kladysm5

   Databázový model kladu SM5.


.. py:class:: Adb

   Databázový model ADB.

   Obsahuje vazbu na dokumentační jednotku.

   **Metody:**

   .. py:method:: get_absolute_url()

      Vrací absolute url.

      :return: Vrací výsledek volání ``get_absolute_url()``.

   .. py:method:: get_permission_object()

      Vrací permission object.

      :return: Vrací výsledek volání ``get_permission_object()``.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.

   .. py:method:: create_transaction()

      Vytvoří Fedora transakci pro ADB záznam a vrátí ji volajícímu.

      :param transaction_user: Uživatel nebo osoba ``transaction_user``, v jejímž kontextu se operace provádí.
      :param success_message: Parametr ``success_message`` předává se do volání ``FedoraTransaction()``.
      :param error_message: Parametr ``error_message`` předává se do volání ``FedoraTransaction()``.
      :param main_record: Parametr ``main_record`` předává se do volání ``FedoraTransaction()``.

          :return: Vrací atribut objektu.


.. py:class:: VyskovyBod

   Databázový model výškového bodu.

   Obsahuje vazbu na ADB.

   **Metody:**

   .. py:method:: set_geom()

      Metoda na nastavení geomu (souřadnic).

      :param northing: Číselná hodnota ``northing`` použitá při výpočtu nebo transformaci.
      :param easting: Číselná hodnota ``easting`` použitá při výpočtu nebo transformaci.
      :param niveleta: Výšková hodnota (Z) ukládaná do geometrie bodu.

   .. py:method:: save()

      Override save metody na nastavení ident celý pokud je prázdny.

      :param args: Parametr ``args`` se předává do volání ``save()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``save()``.

   .. py:method:: __init__()

      Override init metody pro úpravu souřadnic.

      :param args: Parametr ``args`` předává se do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` předává se do volání ``__init__()``.

   .. py:method:: get_absolute_url()

      Vrací absolute url.

      :return: Vrací výsledek volání ``get_absolute_url()``.

   .. py:method:: get_permission_object()

      Vrací permission object.

      :return: Vrací výsledek volání ``get_permission_object()``.


.. py:class:: AdbSekvence

   Class pro sekvenci ADB pole db modelu kladysm5.


Funkce
------

.. py:function:: get_vyskovy_bod(adb, offset)

   Funkce pro výpočet ident celý pro VB.

   Obsahuje test na přetečení hodnot.

   :param adb: Parametr ``adb`` předává se do volání ``filter()``, pracuje se s atributy ``ident_cely``, vstupuje do návratové hodnoty.
   :param offset: Posun přičtený k poslednímu pořadí výškového bodu.
   :return: Vrací vypočtený identifikátor výškového bodu.

       :raises MaximalIdentNumberError: Vyvolá se při splnění podmínky ``vyskove_body.count() <= MAXIMAL_VYSKOVY_BOD + offset``.
