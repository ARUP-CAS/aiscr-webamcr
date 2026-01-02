ARCH_Z formuláře
================

Definice formulářů.

Třídy
------

.. py:class:: AkceVedouciFormSetHelper

   Form helper pro správné vykreslení formuláře vedoucích.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: CreateArchZForm

   Hlavní formulář pro vytvoření, editaci a zobrazení Archeologického záznamu.

   **Metody:**

   .. py:method:: __init__()

      Prepis init metody pro vyplnení init hodnot, nastanvení readonly.


.. py:class:: CustomDateInput

   Custom class pro zadávaní počátečního a konečního datumu v roce zadaním jen roku.

   **Metody:**

   .. py:method:: year_only()

   .. py:method:: get_date_based_on_year()

   .. py:method:: to_python()

      Prepis kvůli jinému objektu CustomDateInput.


.. py:class:: StartDateInput

   Class pro input prvního dne v roce.


.. py:class:: EndDateInput

   Class pro input posledního dne v roce.


.. py:class:: CreateAkceForm

   Hlavní formulář pro vytvoření, editaci a zobrazení akce.

   **Metody:**

   .. py:method:: clean()

      Přepis clean metody s custom oveřením datumu ukončení a zahájení.

   .. py:method:: __init__()

   .. py:method:: clean_odlozena_nz()

      Custom clean metoda pro ověření že je_nz a odlozena_nz nejsou oba True.

   .. py:method:: clean_datum_zahajeni()

      Custom clean metoda pro ověření:
      
          ak je specifikace_data=přesně tak datum_zahájení nesmí být prázdne
      
          datum zahájení není dále něž mesíc v budoucnu

   .. py:method:: clean_datum_ukonceni()

      Custom clean metoda pro ověření:
      
          ak je specifikace_data=přesně tak datum_ukončení nesmí být prázdne
      
          datum ukončení není dále něž mesíc v budoucnu


.. py:class:: ArchzFilterForm

   Popis není k dispozici.


Funkce
------

.. py:function:: create_akce_vedouci_objekt_form(readonly)

   Funkce která vrací formulář VB pro formset.
   
   Args:
       readonly (boolean): nastavuje formulář na readonly.
   
   Returns:
       CreateAkceVedouciObjektForm: django model formulář AkceVedouci
