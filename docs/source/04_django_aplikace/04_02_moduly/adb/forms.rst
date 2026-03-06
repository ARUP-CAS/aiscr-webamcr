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

      :param value: Parametr ``value`` předává se do volání ``filter()``, ovlivňuje větvení podmínek.

      :return: Vrací hodnotu podle větve zpracování, typicky: atribut objektu, str.


.. py:class:: CreateADBForm

   Hlavní formulář pro vytvoření, editaci a zobrazení ADB.

   **Metody:**

   .. py:method:: __init__()

      Init metoda pro vytvoření formuláře.

      :param args: Dodatečné poziční argumenty předané konstruktoru formuláře.
      :param readonly: Pokud ``True``, formulář se vykreslí jen pro čtení.
      :param kwargs: Dodatečné pojmenované argumenty předané konstruktoru formuláře.


.. py:class:: VyskovyBodFormSetHelper

   Form helper pro správné vykreslení formuláře výškovího bodu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.


Funkce
------

.. py:function:: create_vyskovy_bod_form(pian, niveleta, not_readonly)

   Funkce která vrací formulář VB pro formset.

   :param pian: objekt PIAN.
   :param niveleta: niveleta objekt.
   :param not_readonly: nastavuje formulář na readonly.

   :return: django model formulář VB.
