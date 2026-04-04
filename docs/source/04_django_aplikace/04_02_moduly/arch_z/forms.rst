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

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.



.. py:class:: CreateArchZForm

   Hlavní formulář pro vytvoření, editaci a zobrazení Archeologického záznamu.

   **Metody:**

   .. py:method:: __init__()

      Prepis init metody pro vyplnení init hodnot, nastanvení readonly.

      **Parametry:**

      - ``required``: Parametr ``required`` ovlivňuje větvení podmínek.
      - ``required_next``: Parametr ``required_next`` ovlivňuje větvení podmínek.
      - ``readonly``: Parametr ``readonly`` ovlivňuje větvení podmínek.
      - ``args``: Parametr ``args`` předává se do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` předává se do volání ``__init__()``, pracuje se s atributy ``pop``.



.. py:class:: CustomDateInput

   Custom class pro zadávaní počátečního a konečního datumu v roce zadaním jen roku.

   **Metody:**

   .. py:method:: year_only()

      Ověří, zda zadaná hodnota odpovídá formátu čtyřciferného roku.

      **Parametry:**

      - ``value``: Parametr ``value`` předává se do volání ``fullmatch()``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací výsledek volání ``fullmatch()``.


   .. py:method:: get_date_based_on_year()

      Vrací date based on year.

      **Parametry:**

      - ``year``: Časový údaj ``year`` použitý při filtrování nebo výpočtu.

      **Návratová hodnota:**

      Vrací výsledek volání ``date()``.


   .. py:method:: to_python()

      Prepis kvůli jinému objektu CustomDateInput.

      **Parametry:**

      - ``value``: Parametr ``value`` předává se do volání ``isinstance()``, ``year_only()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``get_date_based_on_year()``, výsledek volání ``to_python()``.



.. py:class:: StartDateInput

   Class pro input prvního dne v roce.


.. py:class:: EndDateInput

   Class pro input posledního dne v roce.


.. py:class:: CreateAkceForm

   Hlavní formulář pro vytvoření, editaci a zobrazení akce.

   **Metody:**

   .. py:method:: clean()

      Přepis clean metody s custom oveřením datumu ukončení a zahájení.

      **Návratová hodnota:**

      Vrací atribut objektu.

      **Výjimky:**

      - ``forms.ValidationError``: Vyvolá se při splnění podmínky ``cleaned_data.get('datum_ukonceni') is not None and cleaned_data.get('datum_zahajeni') is None``; nebo při splnění podmínky ``cleaned_data.get('datum_zahajeni') > cleaned_data.get('datum_ukonceni')``.


   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``required``: Parametr ``required`` ovlivňuje větvení podmínek.
      - ``required_next``: Parametr ``required_next`` ovlivňuje větvení podmínek.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``, pracuje se s atributy ``pop``.


   .. py:method:: clean_odlozena_nz()

      Custom clean metoda pro ověření že je_nz a odlozena_nz nejsou oba True.

      **Návratová hodnota:**

      Vrací proměnná ``odlozena_nz``.

      **Výjimky:**

      - ``ValidationError``: Vyvolá se při splnění podmínky ``odlozena_nz and je_nz``.


   .. py:method:: clean_datum_zahajeni()

      Custom clean metoda pro ověření:

      ak je specifikace_data=přesně tak datum_zahájení nesmí být prázdne

      datum zahájení není dále něž mesíc v budoucnu

      **Návratová hodnota:**

      Vrací vybranou hodnotu z kolekce.


   .. py:method:: clean_datum_ukonceni()

      Custom clean metoda pro ověření:

      ak je specifikace_data=přesně tak datum_ukončení nesmí být prázdne

      datum ukončení není dále něž mesíc v budoucnu

      **Návratová hodnota:**

      Vrací vybranou hodnotu z kolekce.



.. py:class:: ArchzFilterForm

   Implementuje komponentu ``ArchzFilterForm`` v rámci aplikace.


Funkce
------

.. py:function:: create_akce_vedouci_objekt_form(readonly)

   Funkce která vrací formulář VB pro formset.

   **Parametry:**

   - ``readonly``: Pokud ``True``, pole formuláře jsou pouze pro čtení.

   **Návratová hodnota:**

   Vnitřní ``ModelForm`` pro evidenci vedoucího akce.

