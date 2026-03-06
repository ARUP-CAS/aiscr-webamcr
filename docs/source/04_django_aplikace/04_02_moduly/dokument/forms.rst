DOKUMENT formuláře
==================

Definice formulářů.

Třídy
------

.. py:class:: AutoriField

   Třída pro správně zaobcházení s autormi, tak aby jejich uložení pořadí bylo stejné jako zadané uživatelem.

   **Metody:**

   .. py:method:: clean()

      Provádí operaci clean.

      :param value: Parametr ``value`` předává se do volání ``clean()``, ``debug()``, ovlivňuje větvení podmínek.

      :return: Vrací proměnná ``qs``.


.. py:class:: CoordinatesDokumentForm

   Hlavní formulář pro editaci souřadnic v modelu 3D a PAS.


.. py:class:: EditDokumentExtraDataForm

   Hlavní formulář pro vytvoření, editaci a zobrazení Extra dat u dokumentu a modelu 3D.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param readonly: Parametr ``readonly`` ovlivňuje větvení podmínek.
      :param required: Parametr ``required`` ovlivňuje větvení podmínek.
      :param required_next: Parametr ``required_next`` slouží jako vstup pro logiku funkce ``__init__``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``, pracuje se s atributy ``pop``.


.. py:class:: EditDokumentForm

   Hlavní formulář pro vytvoření, editaci a zobrazení Dokumentu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param readonly: Parametr ``readonly`` ovlivňuje větvení podmínek.
      :param required: Parametr ``required`` ovlivňuje větvení podmínek.
      :param required_next: Parametr ``required_next`` slouží jako vstup pro logiku funkce ``__init__``.
      :param can_edit_datum_zverejneni: Parametr ``can_edit_datum_zverejneni`` ovlivňuje větvení podmínek.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``, pracuje se s atributy ``pop``.


.. py:class:: CreateModelDokumentForm

   Hlavní formulář pro vytvoření, editaci a zobrazení modelu 3D.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param readonly: Parametr ``readonly`` slouží jako vstup pro logiku funkce ``__init__``.
      :param required: Parametr ``required`` ovlivňuje větvení podmínek.
      :param required_next: Parametr ``required_next`` slouží jako vstup pro logiku funkce ``__init__``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.


.. py:class:: CreateModelExtraDataForm

   Hlavní formulář pro vytvoření, editaci a zobrazení extra dat modelu 3D.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param readonly: Parametr ``readonly`` slouží jako vstup pro logiku funkce ``__init__``.
      :param required: Parametr ``required`` ovlivňuje větvení podmínek.
      :param required_next: Parametr ``required_next`` slouží jako vstup pro logiku funkce ``__init__``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.


.. py:class:: PripojitDokumentForm

   Hlavní formulář připojení dokumentu do projektu nebo arch záznamu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param ident_zaznam: Identifikátor ``ident_zaznam`` používaný pro dohledání cílového záznamu.
      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.


.. py:class:: DokumentCastForm

   Hlavní formulář pro zobrazení Dokument části.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param readonly: Parametr ``readonly`` slouží jako vstup pro logiku funkce ``__init__``.
      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.


.. py:class:: DokumentCastCreateForm

   Hlavní formulář pro vytvoření, editaci Dokument části.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.


.. py:class:: TvarFormSetHelper

   Form helper pro správné vykreslení formuláře tvarů.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.


.. py:class:: DokumentFilterForm

   Implementuje komponentu ``DokumentFilterForm`` v rámci aplikace.


Funkce
------

.. py:function:: create_tvar_form(not_readonly)

   Funkce která vrací formulář Tvar pro formset.

   Pomocí ní je možné předat výběr formuláři.

   :param not_readonly: Číselná hodnota ``not_readonly`` použitá při výpočtu nebo transformaci.

   :return: Vrací proměnná ``TvarForm``.
