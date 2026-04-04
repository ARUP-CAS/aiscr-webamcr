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

      **Parametry:**

      - ``value``: Seznam ID autorů.

      **Návratová hodnota:**

      QuerySet autorů seřazený podle zadaného pořadí.



.. py:class:: CoordinatesDokumentForm

   Hlavní formulář pro editaci souřadnic v modelu 3D a PAS.


.. py:class:: EditDokumentExtraDataForm

   Hlavní formulář pro vytvoření, editaci a zobrazení Extra dat u dokumentu a modelu 3D.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje formulář pro editaci metadat dokumentu s kontrolou dostupnosti polí.

      **Parametry:**

      - ``args``: Poziční argumenty pro ModelForm.
      - ``readonly``: Zda jsou pole jen pro čtení.
      - ``required``: Která pole jsou povinná.
      - ``required_next``: Která pole budou povinná v následující relaci.
      - ``kwargs``: Pojmenované argumenty včetně rada, let, dok_osoby a edit.



.. py:class:: EditDokumentForm

   Hlavní formulář pro vytvoření, editaci a zobrazení Dokumentu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje formulář s kontrolou práv a dostupnosti polí.

      **Parametry:**

      - ``args``: Poziční argumenty pro ModelForm.
      - ``readonly``: Zda jsou pole jen pro čtení.
      - ``required``: Která pole jsou povinná.
      - ``required_next``: Která pole budou povinná v následující relaci.
      - ``can_edit_datum_zverejneni``: Zda lze editovat datum zveřejnění.
      - ``kwargs``: Klíčové argumenty včetně create a region_not_required.



.. py:class:: CreateModelDokumentForm

   Hlavní formulář pro vytvoření, editaci a zobrazení modelu 3D.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje formulář pro vytvoření 3D modelu s nastavením dostupných typů.

      **Parametry:**

      - ``args``: Poziční argumenty pro ModelForm.
      - ``readonly``: Zda jsou pole jen pro čtení.
      - ``required``: Která pole jsou povinná.
      - ``required_next``: Která pole budou povinná v následující relaci.
      - ``kwargs``: Pojmenované argumenty pro ModelForm.



.. py:class:: CreateModelExtraDataForm

   Hlavní formulář pro vytvoření, editaci a zobrazení extra dat modelu 3D.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje formulář pro zadání extra dat 3D modelu.

      **Parametry:**

      - ``args``: Poziční argumenty pro ModelForm.
      - ``readonly``: Zda jsou pole jen pro čtení.
      - ``required``: Která pole jsou povinná.
      - ``required_next``: Která pole budou povinná v následující relaci.
      - ``kwargs``: Pojmenované argumenty pro ModelForm.



.. py:class:: PripojitDokumentForm

   Hlavní formulář připojení dokumentu do projektu nebo arch záznamu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``ident_zaznam``: Identifikátor ``ident_zaznam`` používaný pro dohledání cílového záznamu.
      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.



.. py:class:: DokumentCastForm

   Hlavní formulář pro zobrazení Dokument části.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje formulář pro editaci poznámky k součásti dokumentu.

      **Parametry:**

      - ``readonly``: Zda jsou pole jen pro čtení.
      - ``args``: Poziční argumenty pro ModelForm.
      - ``kwargs``: Pojmenované argumenty pro ModelForm.



.. py:class:: DokumentCastCreateForm

   Hlavní formulář pro vytvoření, editaci Dokument části.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.



.. py:class:: TvarFormSetHelper

   Form helper pro správné vykreslení formuláře tvarů.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.



.. py:class:: DokumentFilterForm

   Implementuje komponentu ``DokumentFilterForm`` v rámci aplikace.


Funkce
------

.. py:function:: create_tvar_form(not_readonly)

   Funkce která vrací formulář Tvar pro formset.

   Pomocí ní je možné předat výběr formuláři.

   **Parametry:**

   - ``not_readonly``: Číselná hodnota ``not_readonly`` použitá při výpočtu nebo transformaci.

   **Návratová hodnota:**

   Vrací proměnná ``TvarForm``.

