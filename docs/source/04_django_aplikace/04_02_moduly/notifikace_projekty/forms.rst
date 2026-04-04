NOTIFIKACE_PROJEKTY formuláře
=============================

Definice formulářů.

Třídy
------

.. py:class:: PesFormSetHelper

   Implementuje komponentu ``PesFormSetHelper`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.



.. py:class:: PesNotificationsForm

   Formulář pro správu typu notifikací.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``pes_object_count``: Parametr ``pes_object_count`` slouží jako vstup pro logiku funkce ``__init__``.
      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.


   .. py:method:: clean()

      Provádí operaci clean.

      **Návratová hodnota:**

      Vrací proměnná ``cleaned_data``.



.. py:class:: PesInlineFormSet

   Implementuje komponentu ``PesInlineFormSet`` v rámci aplikace.

   **Metody:**

   .. py:method:: count_non_empty_forms()

      Provádí operaci count non empty forms.

      **Návratová hodnota:**

      Vrací proměnná ``non_empty_count``.



Funkce
------

.. py:function:: create_pes_form(not_readonly, model_typ)

   Funkce která vrací formulář hlídacího psa pro formset.

   **Parametry:**

   - ``not_readonly``: Číselná hodnota ``not_readonly`` použitá při výpočtu nebo transformaci.
   - ``model_typ``: Parametr ``model_typ`` slouží jako vstup pro logiku funkce ``create_pes_form``.

   **Návratová hodnota:**

   Vrací proměnná ``PesForm``.

