LOKALITA views
==============

Definice views.

Třídy
------

.. py:class:: LokalitaIndexView

   Třida pohledu pro zobrazení domovské stránky lokalit s navigačními možnostmi.

   **Metody:**

   .. py:method:: get_context_data()

      Metoda pro získaní kontextu podlehu.

      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get_context_data``.

      :return: Vrací proměnná ``context``.


.. py:class:: LokalitaListView

   Třida pohledu pro zobrazení listu/tabulky s lokalitami.

   **Metody:**

   .. py:method:: init_translations()

      Provádí operaci init translations.

   .. py:method:: rename_field_for_ordering()

      Provádí operaci rename field for ordering.

      :param field: Parametr ``field`` předává se do volání ``get()``, pracuje se s atributy ``replace``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``get()``.

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      :return: Vrací výsledek volání ``check_filter_permission()``.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.


.. py:class:: LokalitaDetailView

   Třida pohledu pro zobrazení detailu lokality.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get``.

      :return: Vrací výsledek volání ``render_to_response()``.

   .. py:method:: get_archeologicky_zaznam()

      Metoda pro získaní akce z db.

      :return: Vrací atribut objektu.

   .. py:method:: check_locality_arch_z_conflict()

      Ověří locality arch z conflict.

   .. py:method:: get_context_data()

      Metoda pro získaní contextu akci pro template.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.

   .. py:method:: get_shows()

      Vrací shows. v aplikaci.

      :return: Vrací výsledek volání ``get_detail_template_shows()``.


.. py:class:: LokalitaCreateView

   Třida pohledu pro vytvoření lokality.

   **Metody:**

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.

   .. py:method:: form_valid()

      Validuje data ve formuláři

      :param form: Instance vyplněného formuláře.
      :return: HTTP odpověď.

   .. py:method:: form_invalid()

      Informuje uživatele o nevalidním vyplnění formuláře a zaloguje ho.

      :param form: Instance vyplněného formuláře.
      :return: HTTP odpověď.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` předává se do volání ``get()``, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` se předává do volání ``get()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``get()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``get()``.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Parametr ``request`` předává se do volání ``post()``, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` se předává do volání ``post()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``post()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``post()``.


.. py:class:: LokalitaEditView

   Třida pohledu pro editaci lokality.

   **Metody:**

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.

   .. py:method:: form_valid()

      Informuje uživatele o nevalidním vyplnění formuláře a zaloguje ho.

      :param form: Instance vyplněného formuláře.
      :return: HTTP odpověď.

   .. py:method:: form_invalid()

      Informuje uživatele o nevalidním vyplnění formuláře a zaloguje ho.

      :param form: Instance vyplněného formuláře.
      :return: HTTP odpověď.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` předává se do volání ``get()``, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` se předává do volání ``get()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``get()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``get()``.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Parametr ``request`` předává se do volání ``post()``, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` se předává do volání ``post()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``post()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``post()``.


.. py:class:: LokalitaRelatedView

   Třida pohledu pro získaní relací lokality, která je dedená v dalších pohledech.


.. py:class:: LokalitaDokumentacniJednotkaCreateView

   Třida pohledu pro vytvoření dokumentační jednotky lokality.

   **Metody:**

   .. py:method:: get_context_data()

      Zpracuje dispečing požadavku.

      :param request: HTTP požadavek.
      :param args: Poziční argumenty.
      :param kwargs: Pojmenované argumenty.
      :return: HTTP odpověď.


.. py:class:: LokalitaDokumentacniJednotkaRelatedView

   Třida pohledu pro získaní dokumentačních jednotek lokality, která je dedená v dalších pohledech.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Parametr ``request`` předává se do volání ``add_message()``, ``url_has_allowed_host_and_scheme()``, pracuje se s atributy ``GET``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``dispatch()``.

   .. py:method:: get_dokumentacni_jednotka()

      Vrací dokumentacni jednotka.

      :return: Vrací proměnná ``object``.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.


.. py:class:: LokalitaDokumentacniJednotkaUpdateView

   Třida pohledu pro editaci dokumentační jednotky lokality.

   **Metody:**

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.


.. py:class:: LokalitaKomponentaCreateView

   Třida pohledu pro vytvoření komponenty lokality.

   **Metody:**

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.

   .. py:method:: get()

      Zpracuje dispečing požadavku.

      :param request: HTTP požadavek.
      :param args: Poziční argumenty.
      :param kwargs: Pojmenované argumenty.
      :return: HTTP odpověď.


.. py:class:: LokalitaKomponentaUpdateView

   Třida pohledu pro editaci komponenty lokality.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Parametr ``request`` předává se do volání ``add_message()``, ``url_has_allowed_host_and_scheme()``, pracuje se s atributy ``GET``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``dispatch()``.

   .. py:method:: get_komponenta()

      Vrací komponenta. v aplikaci.

      :return: Vrací proměnná ``object``.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.


.. py:class:: LokalitaPianCreateView

   Třida pohledu pro vytvoření pianu dokumentační jednotky lokality.

   **Metody:**

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` předává se do volání ``get()``, ``str()``, pracuje se s atributy ``user``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``render_to_response()``.
      :raises Exception: Vyvolá se s textem "lokalita.views.LokalitaPianCreateView.get.label_not_found"; nebo s textem "lokalita.views.LokalitaPianCreateView.get.transormation_error".


.. py:class:: LokalitaPianUpdateView

   Třida pohledu pro editaci pianu dokumentační jednotky lokality.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Parametr ``request`` předává se do volání ``add_message()``, ``url_has_allowed_host_and_scheme()``, pracuje se s atributy ``GET``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``dispatch()``.

   .. py:method:: get_pian()

      Vrací pian. v aplikaci.

      :return: Vrací výsledek volání ``get_object_or_404()``.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` předává se do volání ``get()``, ``str()``, pracuje se s atributy ``user``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``render_to_response()``.
      :raises PermissionDenied: Vyvolá se při splnění podmínky ``self.pian == PIAN_POTVRZEN``.
      :raises Exception: Vyvolá se s textem "lokalita.views.LokalitaPianUpdateView.get.label_not_found"; nebo s textem "lokalita.views.LokalitaPianUpdateView.get.transormation_error".


Funkce
------

.. py:function:: get_required_fields(zaznam, next)

   Funkce pro získaní dictionary povinných polí podle stavu lokality.

   :param zaznam: Parametr ``zaznam`` pracuje se s atributy ``stav``, ovlivňuje větvení podmínek.
   :param next: Posun vůči aktuálnímu stavu (pro kontrolu povinných polí v následujícím kroku).
   :return: Seznam názvů polí, která mají být v daném stavu povinná.
