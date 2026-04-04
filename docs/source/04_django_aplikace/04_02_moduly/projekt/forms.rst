PROJEKT formuláře
=================

Definice formulářů.

Třídy
------

.. py:class:: CreateProjektForm

   Hlavní formulář pro vytvoření projektu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``required``: Parametr ``required`` ovlivňuje větvení podmínek.
      - ``required_next``: Parametr ``required_next`` ovlivňuje větvení podmínek.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.


   .. py:method:: clean()

      Provádí operaci clean.

      **Návratová hodnota:**

      Vrací proměnná ``cleaned_data``.

      **Výjimky:**

      - ``forms.ValidationError``: Vyvolá se při splnění podmínky ``not coordinate_x1 or not coordinate_x2``.



.. py:class:: EditProjektForm

   Hlavní formulář pro editaci projektu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``required``: Parametr ``required`` ovlivňuje větvení podmínek.
      - ``required_next``: Parametr ``required_next`` ovlivňuje větvení podmínek.
      - ``edit_fields``: Parametr ``edit_fields`` ovlivňuje větvení podmínek.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.


   .. py:method:: clean()

      Kontrola datumu zahájení a ukončení pri validaci formuláře.

      **Návratová hodnota:**

      Vrací atribut objektu.

      **Výjimky:**

      - ``forms.ValidationError``: Vyvolá se s textem "Datum zahájení nemůže být po datu ukončení".



.. py:class:: NavrhnoutZruseniProjektForm

   Formulář pro navržení zrušení projektu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.


   .. py:method:: clean()

      Metoda na kontrolu obsahu důvodu pro zrušení.

      **Návratová hodnota:**

      Vrací atribut objektu.

      **Výjimky:**

      - ``forms.ValidationError``: Vyvolá se při splnění podmínky ``not cleaned_data.get('projekt_id')``; nebo při splnění podmínky ``not cleaned_data.get('reason_text')``.



.. py:class:: PrihlaseniProjektForm

   Hlavní formulář pro prihlášení projektu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``, pracuje se s atributy ``pop``.



.. py:class:: ZahajitVTerenuForm

   Formulář pro zahájení projektu v terénu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.


   .. py:method:: clean()

      Provádí operaci clean.

      **Návratová hodnota:**

      Vrací proměnná ``cleaned_data``.



.. py:class:: UkoncitVTerenuForm

   Formulář pro ukončení projektu v terénu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.


   .. py:method:: clean()

      Metoda pro kontrolu datumu ukončení.

      **Návratová hodnota:**

      Vrací atribut objektu.

      **Výjimky:**

      - ``forms.ValidationError``: Vyvolá se při splnění podmínky ``self.instance.datum_zahajeni > cleaned_data.get('datum_ukonceni')``.



.. py:class:: ZruseniProjektForm

   Formulář pro zrušení projektu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.



.. py:class:: GenerovatNovePotvrzeniForm

   Formulář pro vygenerování nového potvrzení projektu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.



.. py:class:: GenerovatExpertniListForm

   Formulář pro generování expertního listu projektu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.



.. py:class:: PripojitProjektForm

   Formulář pro pripojení projektu do akce nebo dokumentu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``dok``: Parametr ``dok`` ovlivňuje větvení podmínek.
      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.



.. py:class:: ProjektFilterForm

   Implementuje komponentu ``ProjektFilterForm`` v rámci aplikace.


.. py:class:: ZadostProjektForm

   Implementuje komponentu ``ZadostProjektForm`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``label``: Textový název nebo klíč ``label`` používaný v rámci operace.
      - ``help_text``: Číselná hodnota ``help_text`` použitá při výpočtu nebo transformaci.
      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.



.. py:class:: UpravitDatumOznameniForm

   Implementuje komponentu ``UpravitDatumOznameniForm`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.



.. py:class:: NeodeslatMailForm

   Formulář neodeslání mailu oznamovateli.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.


