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

      :param typ: Vstupní hodnota ``typ`` pro danou operaci.
      :param typ_vazby: Vstupní hodnota ``typ_vazby`` pro danou operaci.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).


Funkce
------

.. py:function:: create_nalez_objekt_form(druh_obj_choices, spec_obj_choices, not_readonly)

   Funkce která vrací formulář nálezu objekty pro formset.

.. py:function:: create_nalez_predmet_form(druh_projekt_choices, specifikce_predmetu_choices, not_readonly)

   Funkce která vrací formulář nálezu předměty pro formset.
