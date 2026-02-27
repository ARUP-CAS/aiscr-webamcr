EZ views
========

Definice views.

Třídy
------

.. py:class:: ExterniZdrojIndexView

   Třida pohledu pro zobrazení domovské stránky externích zdrojů s navigačními možnostmi.

   **Metody:**

   .. py:method:: get_context_data()

      Metoda pro získaní kontextu podlehu.


.. py:class:: ExterniZdrojListView

   Třida pohledu pro zobrazení listu/tabulky s externím zdrojem.

   **Metody:**

   .. py:method:: init_translations()

      Provádí operaci init translations.

      :return: Vrací výsledek provedené operace.

   .. py:method:: rename_field_for_ordering()

      Provádí operaci rename field for ordering.

      :param field: Vstupní hodnota ``field`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get_queryset()

      Vrací queryset.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: add_accessibility_lookup()

      Provádí operaci add accessibility lookup.

      :param permission: Vstupní hodnota ``permission`` pro danou operaci.
      :param qs: Vstupní hodnota ``qs`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: ExterniZdrojDetailView

   Třida pohledu pro zobrazení detailu externího zdroju.

   **Metody:**

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: ExterniZdrojCreateView

   Třida pohledu pro vytvoření externího zdroje.

   **Metody:**

   .. py:method:: get_form_kwargs()

      Vrací form kwargs.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: form_valid()

      Provádí operaci form valid.

      :param form: Vstupní hodnota ``form`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: form_invalid()

      Provádí operaci form invalid.

      :param form: Vstupní hodnota ``form`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: ExterniZdrojEditView

   Třida pohledu pro editaci externího zdroje.

   **Metody:**

   .. py:method:: get_form_kwargs()

      Vrací form kwargs.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: form_valid()

      Provádí operaci form valid.

      :param form: Vstupní hodnota ``form`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: form_invalid()

      Provádí operaci form invalid.

      :param form: Vstupní hodnota ``form`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.


.. py:class:: TransakceView

   Třida pohledu pro změnu stavu a práci s externíma zdrojama cez modal, která se dedí pro jednotlivá změny.

   **Metody:**

   .. py:method:: init_translation()

      Provádí operaci init translation.

      :return: Vrací výsledek provedené operace.

   .. py:method:: get_zaznam()

      Vrací zaznam.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.


.. py:class:: ExterniZdrojOdeslatView

   Třida pohledu pro odeslání externího zdroje pomoci modalu.

   **Metody:**

   .. py:method:: init_translation()

      Provádí operaci init translation.

      :return: Vrací výsledek provedené operace.


.. py:class:: ExterniZdrojPotvrditView

   Třida pohledu pro potvrzení externího zdroje pomoci modalu.

   **Metody:**

   .. py:method:: init_translation()

      Provádí operaci init translation.

      :return: Vrací výsledek provedené operace.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.


.. py:class:: ExterniZdrojSmazatView

   Třida pohledu pro smazání externího zdroje pomoci modalu.

   **Metody:**

   .. py:method:: init_translation()

      Provádí operaci init translation.

      :return: Vrací výsledek provedené operace.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.


.. py:class:: ExterniZdrojVratitView

   Třida pohledu pro vrácení externího zdroje pomoci modalu.

   **Metody:**

   .. py:method:: init_translation()

      Provádí operaci init translation.

      :return: Vrací výsledek provedené operace.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.


.. py:class:: ExterniOdkazOdpojitView

   Třida pohledu pro odpojení externího odkazu pomoci modalu.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.

   .. py:method:: init_translation()

      Provádí operaci init translation.

      :return: Vrací výsledek provedené operace.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.


.. py:class:: ExterniOdkazPripojitView

   Třida pohledu pro připojení externího odkazu pomoci modalu.

   **Metody:**

   .. py:method:: init_translation()

      Provádí operaci init translation.

      :return: Vrací výsledek provedené operace.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.


.. py:class:: ExterniOdkazEditView

   Třida pohledu pro editaci externího odkazu pomoci modalu.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_success_url()

      Vrací success url.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_object()

      Vrací object.

      :param queryset: Vstupní hodnota ``queryset`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.

   .. py:method:: form_valid()

      Provádí operaci form valid.

      :param form: Vstupní hodnota ``form`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: form_invalid()

      Provádí operaci form invalid.

      :param form: Vstupní hodnota ``form`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: ExterniOdkazOdpojitAZView

   Třida pohledu pro odpojení externího odkazu z archeologického záznamu pomoci modalu.

   **Metody:**

   .. py:method:: init_translation()

      Provádí operaci init translation.

      :return: Vrací výsledek provedené operace.

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get_zaznam()

      Vrací zaznam.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.


.. py:class:: ExterniZdrojAutocomplete

   Třída pohledu pro autocomplete externích zdrojů.

   **Metody:**

   .. py:method:: get_result_label()

      Vrací result label.

      :param result: Vstupní hodnota ``result`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_queryset()

      Vrací queryset.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: add_accessibility_lookup()

      Provádí operaci add accessibility lookup.

      :param permission: Vstupní hodnota ``permission`` pro danou operaci.
      :param qs: Vstupní hodnota ``qs`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: ExterniZdrojTableRowView

   Třída pohledu pro získaní řádku tabulky s externím zdrojem.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: ExterniOdkazPripojitDoAzView

   Třída pohledu pro připojení externího odkazu do arch záznamu.

   **Metody:**

   .. py:method:: get_zaznam()

      Vrací zaznam.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.


.. py:class:: EzOdkazyTableView

   Třída pohledu pro zobrazení řádků tabulky externích odkazů.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param ident_cely: Vstupní hodnota ``ident_cely`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.


Funkce
------

.. py:function:: get_history_dates(historie_vazby, request_user)

   Funkce pro získaní historických datumu.

.. py:function:: get_detail_template_shows(zaznam, user)

   Funkce pro získaní kontextu pro zobrazování možností na stránkách.

.. py:function:: get_required_fields()

   Funkce pro získaní dictionary povinných polí podle stavu externího zdroje.


   **Argumenty:**

   - ``zaznam`` (*Externí zdroj*): model ExterniZdroj pro který se dané pole počítají.
   - ``next`` (*int*): pokud je poskytnuto číslo tak se jedná o povinné pole pro příští stav.

   **Návratová hodnota:**

   *required_fields*: list polí.

.. py:function:: save_autor_editor(zaznam, form)

   Funkce pro uložení autorů a editorů k externímu zdroji podle toho v jakém pořadí byly zadáni.
