ADB modely
==========

Definice modelů.

Třídy
------

.. py:class:: Kladysm5

   Class pro db model kladysm5.


.. py:class:: Adb

   Class pro db model ADB.
   Obsahuje vazbu na dokumentační jednotku.

   **Metody:**

   .. py:method:: get_absolute_url()

   .. py:method:: get_permission_object()

   .. py:method:: __init__()

   .. py:method:: create_transaction()


.. py:class:: VyskovyBod

   Class pro db model vyškový bod.
   Obsahuje vazbu na ADB.

   **Metody:**

   .. py:method:: set_geom()

      Metoda na nastavení geomu (souřadnic).

   .. py:method:: save()

      Override save metody na nastavení ident celý pokud je prázdny.

   .. py:method:: __init__()

      Override init metody pro úpravu souřadnic.

   .. py:method:: get_absolute_url()

   .. py:method:: get_permission_object()


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
