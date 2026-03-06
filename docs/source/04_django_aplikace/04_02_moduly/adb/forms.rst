ADB formuláře
=============

Definice formulářů.

Třídy
------

.. py:class:: AdbReadOnlyTextInput

   Implementuje komponentu ``AdbReadOnlyTextInput`` v rámci aplikace.

   **Metody:**

   .. py:method:: format_value()

      Provádí operaci format value.

      :param value: Vstupní hodnota ``value`` pro danou operaci.


.. py:class:: CreateADBForm

   Hlavní formulář pro vytvoření, editaci a zobrazení ADB.

   **Metody:**

   .. py:method:: __init__()

      Init metoda pro vytvoření formuláře.

      **Argumenty:**

      - ``readonly`` (*boolean*): nastavuje formulář na readonly.


.. py:class:: VyskovyBodFormSetHelper

   Form helper pro správné vykreslení formuláře výškovího bodu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


Funkce
------

.. py:function:: create_vyskovy_bod_form(pian, niveleta, not_readonly)

   Funkce která vrací formulář VB pro formset.

   :param pian: objekt PIAN.
   :param niveleta: niveleta objekt.
   :param not_readonly: nastavuje formulář na readonly.

   :return: django model formulář VB.
