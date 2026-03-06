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

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.


.. py:class:: CoordinatesDokumentForm

   Hlavní formulář pro editaci souřadnic v modelu 3D a PAS.


.. py:class:: EditDokumentExtraDataForm

   Hlavní formulář pro vytvoření, editaci a zobrazení Extra dat u dokumentu a modelu 3D.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param readonly: Příznak ``readonly`` určující průběh nebo rozsah zpracování.
      :param required: Příznak ``required`` určující průběh nebo rozsah zpracování.
      :param required_next: Příznak ``required_next`` určující průběh nebo rozsah zpracování.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: EditDokumentForm

   Hlavní formulář pro vytvoření, editaci a zobrazení Dokumentu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param readonly: Příznak ``readonly`` určující průběh nebo rozsah zpracování.
      :param required: Příznak ``required`` určující průběh nebo rozsah zpracování.
      :param required_next: Příznak ``required_next`` určující průběh nebo rozsah zpracování.
      :param can_edit_datum_zverejneni: Číselná nebo geometrická hodnota `can_edit_datum_zverejneni` použitá při výpočtu nebo transformaci.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: CreateModelDokumentForm

   Hlavní formulář pro vytvoření, editaci a zobrazení modelu 3D.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param readonly: Příznak ``readonly`` určující průběh nebo rozsah zpracování.
      :param required: Příznak ``required`` určující průběh nebo rozsah zpracování.
      :param required_next: Příznak ``required_next`` určující průběh nebo rozsah zpracování.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: CreateModelExtraDataForm

   Hlavní formulář pro vytvoření, editaci a zobrazení extra dat modelu 3D.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param readonly: Příznak ``readonly`` určující průběh nebo rozsah zpracování.
      :param required: Příznak ``required`` určující průběh nebo rozsah zpracování.
      :param required_next: Příznak ``required_next`` určující průběh nebo rozsah zpracování.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: PripojitDokumentForm

   Hlavní formulář připojení dokumentu do projektu nebo arch záznamu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param ident_zaznam: Identifikátor ``ident_zaznam`` používaný pro dohledání cílového záznamu.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: DokumentCastForm

   Hlavní formulář pro zobrazení Dokument části.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param readonly: Příznak ``readonly`` určující průběh nebo rozsah zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: DokumentCastCreateForm

   Hlavní formulář pro vytvoření, editaci Dokument části.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: TvarFormSetHelper

   Form helper pro správné vykreslení formuláře tvarů.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: DokumentFilterForm

   Implementuje komponentu ``DokumentFilterForm`` v rámci aplikace.


Funkce
------

.. py:function:: create_tvar_form(not_readonly)

   Funkce která vrací formulář Tvar pro formset.

   Pomocí ní je možné předat výběr formuláři.

   :param not_readonly: Číselná hodnota ``not_readonly`` použitá při výpočtu nebo transformaci.
