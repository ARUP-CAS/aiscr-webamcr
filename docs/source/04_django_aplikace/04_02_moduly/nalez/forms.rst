NALEZ formuláře
===============

Definice formulářů.

Třídy
------

.. py:class:: NalezFormSetHelper

   Implementuje komponentu ``NalezFormSetHelper`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param typ: Parametr ``typ`` slouží jako vstup pro logiku funkce ``__init__``.
      :param typ_vazby: Parametr ``typ_vazby`` slouží jako vstup pro logiku funkce ``__init__``.
      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.


Funkce
------

.. py:function:: create_nalez_objekt_form(druh_obj_choices, spec_obj_choices, not_readonly)

   Funkce která vrací formulář nálezu objekty pro formset.

   :param druh_obj_choices: Parametr ``druh_obj_choices`` slouží jako vstup pro logiku funkce ``create_nalez_objekt_form``.
   :param spec_obj_choices: Parametr ``spec_obj_choices`` slouží jako vstup pro logiku funkce ``create_nalez_objekt_form``.
   :param not_readonly: Číselná hodnota ``not_readonly`` použitá při výpočtu nebo transformaci.

   :return: Vrací proměnná ``CreateNalezObjektForm``.

.. py:function:: create_nalez_predmet_form(druh_projekt_choices, specifikce_predmetu_choices, not_readonly)

   Funkce která vrací formulář nálezu předměty pro formset.

   :param druh_projekt_choices: Parametr ``druh_projekt_choices`` slouží jako vstup pro logiku funkce ``create_nalez_predmet_form``.
   :param specifikce_predmetu_choices: Parametr ``specifikce_predmetu_choices`` slouží jako vstup pro logiku funkce ``create_nalez_predmet_form``.
   :param not_readonly: Číselná hodnota ``not_readonly`` použitá při výpočtu nebo transformaci.

   :return: Vrací proměnná ``CreateNalezPredmetForm``.
