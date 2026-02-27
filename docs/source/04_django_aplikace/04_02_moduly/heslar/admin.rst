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
      :param obj: Vstupní hodnota ``obj`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: HeslarWithMetadataAdmin

   Implementuje komponentu ``HeslarWithMetadataAdmin`` v rámci aplikace.


.. py:class:: HeslarNazevAdmin

   Admin část pro prohlížení modelu heslař název.
   Práva na změnu jsou zakázaná.

   **Metody:**

   .. py:method:: has_add_permission()

      Určí, zda add permission.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Vstupní hodnota ``obj`` pro danou operaci.
      :return: Vrací výsledek ověření nebo validačního pravidla.

   .. py:method:: has_delete_permission()

      Určí, zda delete permission.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Vstupní hodnota ``obj`` pro danou operaci.
      :return: Vrací výsledek ověření nebo validačního pravidla.

   .. py:method:: has_change_permission()

      Určí, zda change permission.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Vstupní hodnota ``obj`` pro danou operaci.
      :return: Vrací výsledek ověření nebo validačního pravidla.


.. py:class:: HeslarAdmin

   Admin část pro správu modelu heslař.

   **Metody:**

   .. py:method:: render_change_form()

      Vyrenderuje change form.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param context: Vstupní hodnota ``context`` pro danou operaci.
      :param add: Vstupní hodnota ``add`` pro danou operaci.
      :param change: Vstupní hodnota ``change`` pro danou operaci.
      :param form_url: Vstupní hodnota ``form_url`` pro danou operaci.
      :param obj: Vstupní hodnota ``obj`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: has_change_permission()

      Určí, zda change permission.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Vstupní hodnota ``obj`` pro danou operaci.
      :return: Vrací výsledek ověření nebo validačního pravidla.

   .. py:method:: get_readonly_fields()

      Vrací readonly fields.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Vstupní hodnota ``obj`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: has_delete_permission()

      Určí, zda delete permission.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Vstupní hodnota ``obj`` pro danou operaci.
      :return: Vrací výsledek ověření nebo validačního pravidla.


.. py:class:: HeslarDataceAdmin

   Admin část pro správu modelu heslař datace.

   **Metody:**

   .. py:method:: get_readonly_fields()

      Vrací readonly fields.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Vstupní hodnota ``obj`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: obdobi_ident_cely()

      Provádí operaci obdobi ident cely.

      :param obj: Vstupní hodnota ``obj`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: HeslarDokumentTypMaterialRadaAdmin

   Admin část pro prohlížení modelu heslař dokument typ material.
   Práva na změnu jsou zakázaná.

   **Metody:**

   .. py:method:: has_add_permission()

      Určí, zda add permission.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Vstupní hodnota ``obj`` pro danou operaci.
      :return: Vrací výsledek ověření nebo validačního pravidla.

   .. py:method:: has_delete_permission()

      Určí, zda delete permission.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Vstupní hodnota ``obj`` pro danou operaci.
      :return: Vrací výsledek ověření nebo validačního pravidla.

   .. py:method:: has_change_permission()

      Určí, zda change permission.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Vstupní hodnota ``obj`` pro danou operaci.
      :return: Vrací výsledek ověření nebo validačního pravidla.


.. py:class:: HeslarOdkazAdmin

   Admin část pro správu modelu heslař odkaz.

   **Metody:**

   .. py:method:: heslo_ident_cely()

      Provádí operaci heslo ident cely.

      :param obj: Vstupní hodnota ``obj`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: HeslarHierarchieAdmin

   Admin část pro správu modelu heslař hierarchie.

   **Metody:**

   .. py:method:: heslo_podrazene_ident_cely()

      Provádí operaci heslo podrazene ident cely.

      :param obj: Vstupní hodnota ``obj`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: OsobaAdmin

   Admin část pro správu modelu osob.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: has_delete_permission()

      Určí, zda delete permission.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Vstupní hodnota ``obj`` pro danou operaci.
      :return: Vrací výsledek ověření nebo validačního pravidla.

   .. py:method:: get_fields()

      Vrací fields.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Vstupní hodnota ``obj`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: OrganizaceAdmin

   Admin část pro správu modelu organizace.

   **Metody:**

   .. py:method:: has_delete_permission()

      Určí, zda delete permission.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Vstupní hodnota ``obj`` pro danou operaci.
      :return: Vrací výsledek ověření nebo validačního pravidla.


.. py:class:: HeslarRuianAdmin

   Implementuje komponentu ``HeslarRuianAdmin`` v rámci aplikace.

   **Metody:**

   .. py:method:: has_add_permission()

      Určí, zda add permission.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Vstupní hodnota ``obj`` pro danou operaci.
      :return: Vrací výsledek ověření nebo validačního pravidla.

   .. py:method:: has_delete_permission()

      Určí, zda delete permission.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Vstupní hodnota ``obj`` pro danou operaci.
      :return: Vrací výsledek ověření nebo validačního pravidla.

   .. py:method:: has_change_permission()

      Určí, zda change permission.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Vstupní hodnota ``obj`` pro danou operaci.
      :return: Vrací výsledek ověření nebo validačního pravidla.


.. py:class:: HeslarRuianKrajAdmin

   Admin část pro správu modelu ruian kraj.


.. py:class:: HeslarRuianOkresAdmin

   Admin část pro správu modelu ruian okres.


.. py:class:: HeslarRuianKatastrAdmin

   Admin část pro správu modelu ruian katastr.

