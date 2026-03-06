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

      :param transaction_user: Uživatel nebo osoba ``transaction_user``, v jejímž kontextu se operace provádí.
      :param success_message: Textová zpráva ``success_message`` používaná pro hlášení stavu nebo chyby.
      :param error_message: Textová zpráva ``error_message`` používaná pro hlášení stavu nebo chyby.
      :param main_record: Záznam/objekt ``main_record``, který funkce čte, validuje nebo upravuje.


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

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

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

   :param adb: Záznam/objekt ``adb``, který funkce čte, validuje nebo upravuje.
   :param offset: Posun přičtený k poslednímu pořadí výškového bodu.
   :return: Vrací vypočtený identifikátor výškového bodu.
