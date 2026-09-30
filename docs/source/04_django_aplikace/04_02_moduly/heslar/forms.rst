HESLAR formuláře
================

Definice formulářů.

Třídy
------

.. py:class:: UpdateKatastryFileForm

   Formulář pro nahrání seznamu identifikátorů (Projekt/AZ/SN) k hromadnému
   přepočtu příslušnosti ke katastrům.

   Vstupní soubor je CSV/XLSX se sloupcem ``ident_cely`` (jeden záznam na řádek);
   zpracování provádí ``heslar.views.ContinueKatastrProcessing`` na pozadí.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.


.. py:class:: HeslarHierarchieForm

   Implementuje komponentu ``HeslarHierarchieForm`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.


.. py:class:: HeslarOdkazForm

   Implementuje komponentu ``HeslarOdkazForm`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.


.. py:class:: OsobaAdminForm

   Implementuje komponentu ``OsobaAdminForm`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``, ``OrcidAutocompleteField()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.


.. py:class:: OrganizaceAdminForm

   Implementuje komponentu ``OrganizaceAdminForm`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.

