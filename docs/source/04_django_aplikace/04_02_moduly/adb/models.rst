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

   .. py:method:: get_permission_object()

      Vrací permission object.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: create_transaction()

      Vytvoří Fedora transakci pro ADB záznam a vrátí ji volajícímu.
      :param transaction_user: Vstupní hodnota ``transaction_user`` pro danou operaci.
      :param success_message: Vstupní hodnota ``success_message`` pro danou operaci.
      :param error_message: Vstupní hodnota ``error_message`` pro danou operaci.
      :param main_record: Vstupní hodnota ``main_record`` pro danou operaci.


.. py:class:: VyskovyBod

   Databázový model výškového bodu.

   Obsahuje vazbu na ADB.

   **Metody:**

   .. py:method:: set_geom()

      Metoda na nastavení geomu (souřadnic).
      :param northing: Hodnota parametru ``northing`` použitého touto operací.
      :param easting: Hodnota parametru ``easting`` použitého touto operací.
      :param niveleta: Hodnota parametru ``niveleta`` použitého touto operací.

      :param northing: Hodnota parametru ``northing`` použitého touto operací.
      :param easting: Hodnota parametru ``easting`` použitého touto operací.
      :param niveleta: Hodnota parametru ``niveleta`` použitého touto operací.

   .. py:method:: save()

      Override save metody na nastavení ident celý pokud je prázdny.
      :param args: Hodnota parametru ``args`` použitého touto operací.
      :param kwargs: Hodnota parametru ``kwargs`` použitého touto operací.

      :param args: Hodnota parametru ``args`` použitého touto operací.
      :param kwargs: Hodnota parametru ``kwargs`` použitého touto operací.

   .. py:method:: __init__()

      Override init metody pro úpravu souřadnic.

   .. py:method:: get_absolute_url()

      Vrací absolute url.

   .. py:method:: get_permission_object()

      Vrací permission object.


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
