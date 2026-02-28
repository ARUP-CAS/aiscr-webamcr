ARCH_Z formuláře
================

Definice formulářů.

Třídy
------

.. py:class:: AkceVedouciFormSetHelper

   Form helper pro správné vykreslení formuláře vedoucích.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: CreateArchZForm

   Hlavní formulář pro vytvoření, editaci a zobrazení Archeologického záznamu.

   **Metody:**

   .. py:method:: __init__()

      Prepis init metody pro vyplnení init hodnot, nastanvení readonly.


.. py:class:: CustomDateInput

   Custom class pro zadávaní počátečního a konečního datumu v roce zadaním jen roku.

   **Metody:**

   .. py:method:: year_only()

      Provádí operaci year only.

      :param value: Vstupní hodnota ``value`` pro danou operaci.

   .. py:method:: get_date_based_on_year()

      Vrací date based on year.

      :param year: Vstupní hodnota ``year`` pro danou operaci.

   .. py:method:: to_python()

      Prepis kvůli jinému objektu CustomDateInput.

      :param value: Popis parametru ``value``.


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

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param required: Vstupní hodnota ``required`` pro danou operaci.
      :param required_next: Vstupní hodnota ``required_next`` pro danou operaci.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

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

   Implementuje komponentu ``ArchzFilterForm`` v rámci aplikace.


Funkce
------

.. py:function:: create_akce_vedouci_objekt_form(readonly)

   Funkce která vrací formulář VB pro formset.


   **Argumenty:**

   - ``readonly`` (*boolean*): nastavuje formulář na readonly.

   **Návratová hodnota:**

   *CreateAkceVedouciObjektForm*: django model formulář AkceVedouci
