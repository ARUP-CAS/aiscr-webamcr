ADB formuláře
=============

Definice formulářů.

Třídy
------

.. py:class:: AdbReadOnlyTextInput

   Popis není k dispozici.

   **Metody:**

   .. py:method:: format_value()


.. py:class:: CreateADBForm

   Hlavní formulář pro vytvoření, editaci a zobrazení ADB.

   **Metody:**

   .. py:method:: __init__()

      Init metoda pro vytvoření formuláře.
      Args:
          readonly (boolean): nastavuje formulář na readonly.


.. py:class:: VyskovyBodFormSetHelper

   Form helper pro správné vykreslení formuláře výškovího bodu.

   **Metody:**

   .. py:method:: __init__()


Funkce
------

.. py:function:: create_vyskovy_bod_form(pian, niveleta, not_readonly)

   Funkce která vrací formulář VB pro formset.
   
   Args:
       pian (pian): pian objeckt.
   
       niveleta (niveleta): niveleta objekt.
   
       not_readonly (boolean): nastavuje formulář na readonly.
   
   Returns:
       CreateVysovyBodForm: django model formulář VB
