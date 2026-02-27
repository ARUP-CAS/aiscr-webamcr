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
      :return: Funkce nevrací hodnotu (``None``).


.. py:class:: PesNotificationsForm

   Formulář pro správu typu notifikací.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param pes_object_count: Vstupní hodnota ``pes_object_count`` pro danou operaci.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: clean()

      Provádí operaci clean.

      :return: Vrací výsledek provedené operace.


.. py:class:: PesInlineFormSet

   Implementuje komponentu ``PesInlineFormSet`` v rámci aplikace.

   **Metody:**

   .. py:method:: count_non_empty_forms()

      Provádí operaci count non empty forms.

      :return: Vrací výsledek provedené operace.


Funkce
------

.. py:function:: create_pes_form(not_readonly, model_typ)

   Funkce která vrací formulář hlídacího psa pro formset.
