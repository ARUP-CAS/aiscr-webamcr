HESLAR admin
============

Konfigurace Django admin.

Třídy
------

.. py:class:: ObjectWithMetadataAdmin

   Implementuje komponentu ``ObjectWithMetadataAdmin`` v rámci aplikace.

   **Metody:**

   .. py:method:: metadata()

      Provádí operaci metadata.

      **Parametry:**

      - ``request``: Parametr ``request`` slouží jako vstup pro logiku funkce ``metadata``.
      - ``obj``: Parametr ``obj`` pracuje se s atributy ``metadata``.

      **Návratová hodnota:**

      Vrací proměnná ``response``.



.. py:class:: HeslarWithMetadataAdmin

   Implementuje komponentu ``HeslarWithMetadataAdmin`` v rámci aplikace.


.. py:class:: HeslarNazevAdmin

   Admin část pro prohlížení modelu heslař název.

   Práva na změnu jsou zakázaná.

   **Metody:**

   .. py:method:: has_add_permission()

      Určí, zda add permission.

      **Parametry:**

      - ``request``: Parametr ``request`` slouží jako vstup pro logiku funkce ``has_add_permission``.
      - ``obj``: Parametr ``obj`` slouží jako vstup pro logiku funkce ``has_add_permission``.

      **Návratová hodnota:**

      Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.


   .. py:method:: has_delete_permission()

      Určí, zda delete permission.

      **Parametry:**

      - ``request``: Parametr ``request`` slouží jako vstup pro logiku funkce ``has_delete_permission``.
      - ``obj``: Parametr ``obj`` slouží jako vstup pro logiku funkce ``has_delete_permission``.

      **Návratová hodnota:**

      Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.


   .. py:method:: has_change_permission()

      Určí, zda change permission.

      **Parametry:**

      - ``request``: Parametr ``request`` slouží jako vstup pro logiku funkce ``has_change_permission``.
      - ``obj``: Parametr ``obj`` slouží jako vstup pro logiku funkce ``has_change_permission``.

      **Návratová hodnota:**

      Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.



.. py:class:: HeslarAdmin

   Admin část pro správu modelu heslař.

   **Metody:**

   .. py:method:: render_change_form()

      Vyrenderuje change form.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``render_change_form()``, vstupuje do návratové hodnoty.
      - ``context``: Parametr ``context`` se předává do volání ``render_change_form()``, vstupuje do návratové hodnoty.
      - ``add``: Parametr ``add`` předává se do volání ``render_change_form()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      - ``change``: Parametr ``change`` se předává do volání ``render_change_form()``, vstupuje do návratové hodnoty.
      - ``form_url``: Parametr ``form_url`` se předává do volání ``render_change_form()``, vstupuje do návratové hodnoty.
      - ``obj``: Parametr ``obj`` předává se do volání ``render_change_form()``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací výsledek volání ``render_change_form()``.


   .. py:method:: has_change_permission()

      Určí, zda change permission.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``has_change_permission()``, vstupuje do návratové hodnoty.
      - ``obj``: Parametr ``obj`` předává se do volání ``has_change_permission()``, pracuje se s atributy ``nazev_heslare``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: bool, výsledek volání ``has_change_permission()``.


   .. py:method:: get_readonly_fields()

      Vrací readonly fields.

      **Parametry:**

      - ``request``: Parametr ``request`` slouží jako vstup pro logiku funkce ``get_readonly_fields``.
      - ``obj``: Parametr ``obj`` pracuje se s atributy ``pk``, ovlivňuje větvení podmínek.

      **Návratová hodnota:**

      Vrací n-tici.


   .. py:method:: has_delete_permission()

      Určí, zda delete permission.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``has_delete_permission()``, vstupuje do návratové hodnoty.
      - ``obj``: Parametr ``obj`` pracuje se s atributy ``nazev_heslare``, ``has_connections``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: bool, výsledek volání ``has_delete_permission()``.



.. py:class:: HeslarDataceAdmin

   Admin část pro správu modelu heslař datace.

   **Metody:**

   .. py:method:: get_readonly_fields()

      Vrací readonly fields.

      **Parametry:**

      - ``request``: Parametr ``request`` slouží jako vstup pro logiku funkce ``get_readonly_fields``.
      - ``obj``: Parametr ``obj`` ovlivňuje větvení podmínek.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: n-tici, seznam.


   .. py:method:: obdobi_ident_cely()

      Provádí operaci obdobi ident cely.

      **Parametry:**

      - ``obj``: Parametr ``obj`` pracuje se s atributy ``obdobi``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací atribut objektu.



.. py:class:: HeslarDokumentTypMaterialRadaAdmin

   Admin část pro prohlížení modelu heslař dokument typ material.

   Práva na změnu jsou zakázaná.

   **Metody:**

   .. py:method:: has_add_permission()

      Určí, zda add permission.

      **Parametry:**

      - ``request``: Parametr ``request`` slouží jako vstup pro logiku funkce ``has_add_permission``.
      - ``obj``: Parametr ``obj`` slouží jako vstup pro logiku funkce ``has_add_permission``.

      **Návratová hodnota:**

      Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.


   .. py:method:: has_delete_permission()

      Určí, zda delete permission.

      **Parametry:**

      - ``request``: Parametr ``request`` slouží jako vstup pro logiku funkce ``has_delete_permission``.
      - ``obj``: Parametr ``obj`` slouží jako vstup pro logiku funkce ``has_delete_permission``.

      **Návratová hodnota:**

      Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.


   .. py:method:: has_change_permission()

      Určí, zda change permission.

      **Parametry:**

      - ``request``: Parametr ``request`` slouží jako vstup pro logiku funkce ``has_change_permission``.
      - ``obj``: Parametr ``obj`` slouží jako vstup pro logiku funkce ``has_change_permission``.

      **Návratová hodnota:**

      Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.



.. py:class:: HeslarOdkazAdmin

   Admin část pro správu modelu heslař odkaz.

   **Metody:**

   .. py:method:: heslo_ident_cely()

      Provádí operaci heslo ident cely.

      **Parametry:**

      - ``obj``: Parametr ``obj`` pracuje se s atributy ``heslo``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací atribut objektu.



.. py:class:: HeslarHierarchieAdmin

   Admin část pro správu modelu heslař hierarchie.

   **Metody:**

   .. py:method:: heslo_podrazene_ident_cely()

      Vrací identifikátor podřazeného hesla.

      **Parametry:**

      - ``obj``: Objekt hierarchie.

      **Návratová hodnota:**

      Identifikátor.



.. py:class:: OsobaAdmin

   Admin část pro správu modelu osob.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.


   .. py:method:: has_delete_permission()

      Určí, zda delete permission.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``has_delete_permission()``, vstupuje do návratové hodnoty.
      - ``obj``: Parametr ``obj`` pracuje se s atributy ``has_connections``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: bool, výsledek volání ``has_delete_permission()``.


   .. py:method:: get_fields()

      Vrací fields. v aplikaci.

      **Parametry:**

      - ``request``: Parametr ``request`` slouží jako vstup pro logiku funkce ``get_fields``.
      - ``obj``: Parametr ``obj`` slouží jako vstup pro logiku funkce ``get_fields``.

      **Návratová hodnota:**

      Vrací výsledek volání ``tuple()``.



.. py:class:: OrganizaceAdmin

   Admin část pro správu modelu organizace.

   **Metody:**

   .. py:method:: has_delete_permission()

      Určí, zda delete permission.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``has_delete_permission()``, vstupuje do návratové hodnoty.
      - ``obj``: Parametr ``obj`` pracuje se s atributy ``has_connections``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: bool, výsledek volání ``has_delete_permission()``.



.. py:class:: HeslarRuianAdmin

   Implementuje komponentu ``HeslarRuianAdmin`` v rámci aplikace.

   **Metody:**

   .. py:method:: has_add_permission()

      Určí, zda add permission.

      **Parametry:**

      - ``request``: Parametr ``request`` slouží jako vstup pro logiku funkce ``has_add_permission``.
      - ``obj``: Parametr ``obj`` slouží jako vstup pro logiku funkce ``has_add_permission``.

      **Návratová hodnota:**

      Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.


   .. py:method:: has_delete_permission()

      Určí, zda delete permission.

      **Parametry:**

      - ``request``: Parametr ``request`` slouží jako vstup pro logiku funkce ``has_delete_permission``.
      - ``obj``: Parametr ``obj`` slouží jako vstup pro logiku funkce ``has_delete_permission``.

      **Návratová hodnota:**

      Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.


   .. py:method:: has_change_permission()

      Určí, zda change permission.

      **Parametry:**

      - ``request``: Parametr ``request`` slouží jako vstup pro logiku funkce ``has_change_permission``.
      - ``obj``: Parametr ``obj`` slouží jako vstup pro logiku funkce ``has_change_permission``.

      **Návratová hodnota:**

      Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.



.. py:class:: HeslarRuianKrajAdmin

   Admin část pro správu modelu ruian kraj.


.. py:class:: HeslarRuianOkresAdmin

   Admin část pro správu modelu ruian okres.


.. py:class:: HeslarRuianKatastrAdmin

   Admin část pro správu modelu ruian katastr.

