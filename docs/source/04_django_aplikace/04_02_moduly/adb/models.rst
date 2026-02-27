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

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_permission_object()

      Vrací permission object.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: create_transaction()

      Vytvoří transaction.

      :param transaction_user: Vstupní hodnota ``transaction_user`` pro danou operaci.
      :param success_message: Vstupní hodnota ``success_message`` pro danou operaci.
      :param error_message: Vstupní hodnota ``error_message`` pro danou operaci.
      :param main_record: Vstupní hodnota ``main_record`` pro danou operaci.
      :return: Vrací nově vytvořený výsledek operace.


.. py:class:: VyskovyBod

   Databázový model výškového bodu.
   Obsahuje vazbu na ADB.

   **Metody:**

   .. py:method:: set_geom()

      Metoda na nastavení geomu (souřadnic).

   .. py:method:: save()

      Override save metody na nastavení ident celý pokud je prázdny.

   .. py:method:: __init__()

      Override init metody pro úpravu souřadnic.

   .. py:method:: get_absolute_url()

      Vrací absolute url.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_permission_object()

      Vrací permission object.

      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: AdbSekvence

   Class pro sekvenci ADB pole db modelu kladysm5.


Funkce
------

.. py:function:: get_vyskovy_bod(adb, offset)

   Funkce pro výpočet ident celý pro VB.
   Obsahuje test na přetečení hodnot.


   **Argumenty:**

   - ``adb`` (*adb*): adb objekt pro získaní základu identu.
   - ``offset`` (*int*): offset k připočtení k poslednímu VB

   **Návratová hodnota:**

   *string*: nový ident celý
