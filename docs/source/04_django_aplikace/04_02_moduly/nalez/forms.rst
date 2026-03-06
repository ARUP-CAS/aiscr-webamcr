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

      :param typ: Název nebo typ ``typ`` používaný pro volbu cílové logiky.
      :param typ_vazby: Název nebo typ ``typ_vazby`` používaný pro volbu cílové logiky.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


Funkce
------

.. py:function:: create_nalez_objekt_form(druh_obj_choices, spec_obj_choices, not_readonly)

   Funkce která vrací formulář nálezu objekty pro formset.

   :param druh_obj_choices: Záznam/objekt ``druh_obj_choices``, který funkce čte, validuje nebo upravuje.
   :param spec_obj_choices: Záznam/objekt ``spec_obj_choices``, který funkce čte, validuje nebo upravuje.
   :param not_readonly: Číselná hodnota ``not_readonly`` použitá při výpočtu nebo transformaci.

.. py:function:: create_nalez_predmet_form(druh_projekt_choices, specifikce_predmetu_choices, not_readonly)

   Funkce která vrací formulář nálezu předměty pro formset.

   :param druh_projekt_choices: Doménový objekt `druh_projekt_choices`, se kterým funkce pracuje.
   :param specifikce_predmetu_choices: Číselná nebo geometrická hodnota `specifikce_predmetu_choices` použitá při výpočtu nebo transformaci.
   :param not_readonly: Číselná hodnota ``not_readonly`` použitá při výpočtu nebo transformaci.
