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

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Objekt, se kterým funkce pracuje.


.. py:class:: HeslarWithMetadataAdmin

   Implementuje komponentu ``HeslarWithMetadataAdmin`` v rámci aplikace.


.. py:class:: HeslarNazevAdmin

   Admin část pro prohlížení modelu heslař název.

   Práva na změnu jsou zakázaná.

   **Metody:**

   .. py:method:: has_add_permission()

      Určí, zda add permission.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Objekt, se kterým funkce pracuje.

   .. py:method:: has_delete_permission()

      Určí, zda delete permission.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Objekt, se kterým funkce pracuje.

   .. py:method:: has_change_permission()

      Určí, zda change permission.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Objekt, se kterým funkce pracuje.


.. py:class:: HeslarAdmin

   Admin část pro správu modelu heslař.

   **Metody:**

   .. py:method:: render_change_form()

      Vyrenderuje change form.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param context: Kontextová data používaná při serializaci nebo renderování.
      :param add: Příznak, zda se formulář/objekt vytváří v režimu přidání.
      :param change: Číselná nebo geometrická hodnota `change` použitá při výpočtu nebo transformaci.
      :param form_url: Cesta, URL nebo název zdroje ``form_url``, ze kterého funkce čte nebo kam zapisuje.
      :param obj: Objekt, se kterým funkce pracuje.

   .. py:method:: has_change_permission()

      Určí, zda change permission.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Objekt, se kterým funkce pracuje.

   .. py:method:: get_readonly_fields()

      Vrací readonly fields.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Objekt, se kterým funkce pracuje.

   .. py:method:: has_delete_permission()

      Určí, zda delete permission.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Objekt, se kterým funkce pracuje.


.. py:class:: HeslarDataceAdmin

   Admin část pro správu modelu heslař datace.

   **Metody:**

   .. py:method:: get_readonly_fields()

      Vrací readonly fields.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Objekt, se kterým funkce pracuje.

   .. py:method:: obdobi_ident_cely()

      Provádí operaci obdobi ident cely.

      :param obj: Objekt, se kterým funkce pracuje.


.. py:class:: HeslarDokumentTypMaterialRadaAdmin

   Admin část pro prohlížení modelu heslař dokument typ material.

   Práva na změnu jsou zakázaná.

   **Metody:**

   .. py:method:: has_add_permission()

      Určí, zda add permission.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Objekt, se kterým funkce pracuje.

   .. py:method:: has_delete_permission()

      Určí, zda delete permission.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Objekt, se kterým funkce pracuje.

   .. py:method:: has_change_permission()

      Určí, zda change permission.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Objekt, se kterým funkce pracuje.


.. py:class:: HeslarOdkazAdmin

   Admin část pro správu modelu heslař odkaz.

   **Metody:**

   .. py:method:: heslo_ident_cely()

      Provádí operaci heslo ident cely.

      :param obj: Objekt, se kterým funkce pracuje.


.. py:class:: HeslarHierarchieAdmin

   Admin část pro správu modelu heslař hierarchie.

   **Metody:**

   .. py:method:: heslo_podrazene_ident_cely()

      Provádí operaci heslo podrazene ident cely.

      :param obj: Objekt, se kterým funkce pracuje.


.. py:class:: OsobaAdmin

   Admin část pro správu modelu osob.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: has_delete_permission()

      Určí, zda delete permission.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Objekt, se kterým funkce pracuje.

   .. py:method:: get_fields()

      Vrací fields. v aplikaci.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Objekt, se kterým funkce pracuje.


.. py:class:: OrganizaceAdmin

   Admin část pro správu modelu organizace.

   **Metody:**

   .. py:method:: has_delete_permission()

      Určí, zda delete permission.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Objekt, se kterým funkce pracuje.


.. py:class:: HeslarRuianAdmin

   Implementuje komponentu ``HeslarRuianAdmin`` v rámci aplikace.

   **Metody:**

   .. py:method:: has_add_permission()

      Určí, zda add permission.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Objekt, se kterým funkce pracuje.

   .. py:method:: has_delete_permission()

      Určí, zda delete permission.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Objekt, se kterým funkce pracuje.

   .. py:method:: has_change_permission()

      Určí, zda change permission.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Objekt, se kterým funkce pracuje.


.. py:class:: HeslarRuianKrajAdmin

   Admin část pro správu modelu ruian kraj.


.. py:class:: HeslarRuianOkresAdmin

   Admin část pro správu modelu ruian okres.


.. py:class:: HeslarRuianKatastrAdmin

   Admin část pro správu modelu ruian katastr.

