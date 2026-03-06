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

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: PesNotificationsForm

   Formulář pro správu typu notifikací.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param pes_object_count: Záznam/objekt ``pes_object_count``, který funkce čte, validuje nebo upravuje.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: clean()

      Provádí operaci clean.


.. py:class:: PesInlineFormSet

   Implementuje komponentu ``PesInlineFormSet`` v rámci aplikace.

   **Metody:**

   .. py:method:: count_non_empty_forms()

      Provádí operaci count non empty forms.


Funkce
------

.. py:function:: create_pes_form(not_readonly, model_typ)

   Funkce která vrací formulář hlídacího psa pro formset.

   :param not_readonly: Číselná hodnota ``not_readonly`` použitá při výpočtu nebo transformaci.
   :param model_typ: Název nebo typ ``model_typ`` používaný pro volbu cílové logiky.
