DOKUMENT formuláře
==================

Definice formulářů.

Třídy
------

.. py:class:: AutoriField

   Třída pro správně zaobcházení s autormi, tak aby jejich uložení pořadí bylo stejné jako zadané uživatelem.

   **Metody:**

   .. py:method:: clean()

      Očistí a seřadí seznam autorů podle zadaného pořadí.

      :param value: Seznam ID autorů.
      :return: QuerySet autorů seřazený podle zadaného pořadí.


.. py:class:: CoordinatesDokumentForm

   Hlavní formulář pro editaci souřadnic v modelu 3D a PAS.


.. py:class:: EditDokumentExtraDataForm

   Hlavní formulář pro vytvoření, editaci a zobrazení Extra dat u dokumentu a modelu 3D.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje formulář pro editaci metadat dokumentu s kontrolou dostupnosti polí.

      :param args: Poziční argumenty pro ModelForm.
      :param readonly: Zda jsou pole jen pro čtení.
      :param required: Která pole jsou povinná.
      :param required_next: Která pole budou povinná v následující relaci.
      :param kwargs: Pojmenované argumenty včetně rada, let, dok_osoby a edit.


.. py:class:: EditDokumentForm

   Hlavní formulář pro vytvoření, editaci a zobrazení Dokumentu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje formulář s kontrolou práv a dostupnosti polí.

      :param args: Poziční argumenty pro ModelForm.
      :param readonly: Zda jsou pole jen pro čtení.
      :param required: Která pole jsou povinná.
      :param required_next: Která pole budou povinná v následující relaci.
      :param can_edit_datum_zverejneni: Zda lze editovat datum zveřejnění.
      :param kwargs: Klíčové argumenty včetně create a region_not_required.


.. py:class:: CreateModelDokumentForm

   Hlavní formulář pro vytvoření, editaci a zobrazení modelu 3D.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje formulář pro vytvoření 3D modelu s nastavením dostupných typů.

      :param args: Poziční argumenty pro ModelForm.
      :param readonly: Zda jsou pole jen pro čtení.
      :param required: Která pole jsou povinná.
      :param required_next: Která pole budou povinná v následující relaci.
      :param kwargs: Pojmenované argumenty pro ModelForm.


.. py:class:: CreateModelExtraDataForm

   Hlavní formulář pro vytvoření, editaci a zobrazení extra dat modelu 3D.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje formulář pro zadání extra dat 3D modelu.

      :param args: Poziční argumenty pro ModelForm.
      :param readonly: Zda jsou pole jen pro čtení.
      :param required: Která pole jsou povinná.
      :param required_next: Která pole budou povinná v následující relaci.
      :param kwargs: Pojmenované argumenty pro ModelForm.


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

      Inicializuje formulář pro editaci poznámky k součásti dokumentu.

      :param readonly: Zda jsou pole jen pro čtení.
      :param args: Poziční argumenty pro ModelForm.
      :param kwargs: Pojmenované argumenty pro ModelForm.


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
