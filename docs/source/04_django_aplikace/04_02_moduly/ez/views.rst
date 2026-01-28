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

   .. py:method:: rename_field_for_ordering()

   .. py:method:: get_queryset()

   .. py:method:: add_accessibility_lookup()


.. py:class:: ExterniZdrojDetailView

   Třida pohledu pro zobrazení detailu externího zdroju.

   **Metody:**

   .. py:method:: get_context_data()


.. py:class:: ExterniZdrojCreateView

   Třida pohledu pro vytvoření externího zdroje.

   **Metody:**

   .. py:method:: get_form_kwargs()

   .. py:method:: get_context_data()

   .. py:method:: form_valid()

   .. py:method:: form_invalid()

   .. py:method:: get()


.. py:class:: ExterniZdrojEditView

   Třida pohledu pro editaci externího zdroje.

   **Metody:**

   .. py:method:: get_form_kwargs()

   .. py:method:: get_context_data()

   .. py:method:: form_valid()

   .. py:method:: form_invalid()

   .. py:method:: get()

   .. py:method:: post()


.. py:class:: TransakceView

   Třida pohledu pro změnu stavu a práci s externíma zdrojama cez modal, která se dedí pro jednotlivá změny.

   **Metody:**

   .. py:method:: init_translation()

   .. py:method:: get_zaznam()

   .. py:method:: get_context_data()

   .. py:method:: dispatch()

   .. py:method:: get()

   .. py:method:: post()


.. py:class:: ExterniZdrojOdeslatView

   Třida pohledu pro odeslání externího zdroje pomoci modalu.

   **Metody:**

   .. py:method:: init_translation()


.. py:class:: ExterniZdrojPotvrditView

   Třida pohledu pro potvrzení externího zdroje pomoci modalu.

   **Metody:**

   .. py:method:: init_translation()

   .. py:method:: post()


.. py:class:: ExterniZdrojSmazatView

   Třida pohledu pro smazání externího zdroje pomoci modalu.

   **Metody:**

   .. py:method:: init_translation()

   .. py:method:: post()


.. py:class:: ExterniZdrojVratitView

   Třida pohledu pro vrácení externího zdroje pomoci modalu.

   **Metody:**

   .. py:method:: init_translation()

   .. py:method:: get()

   .. py:method:: post()


.. py:class:: ExterniOdkazOdpojitView

   Třida pohledu pro odpojení externího odkazu pomoci modalu.

   **Metody:**

   .. py:method:: dispatch()

   .. py:method:: init_translation()

   .. py:method:: get_context_data()

   .. py:method:: post()


.. py:class:: ExterniOdkazPripojitView

   Třida pohledu pro připojení externího odkazu pomoci modalu.

   **Metody:**

   .. py:method:: init_translation()

   .. py:method:: get_context_data()

   .. py:method:: post()


.. py:class:: ExterniOdkazEditView

   Třida pohledu pro editaci externího odkazu pomoci modalu.

   **Metody:**

   .. py:method:: dispatch()

   .. py:method:: get_context_data()

   .. py:method:: get_success_url()

   .. py:method:: get_object()

   .. py:method:: post()

   .. py:method:: form_valid()

   .. py:method:: form_invalid()


.. py:class:: ExterniOdkazOdpojitAZView

   Třida pohledu pro odpojení externího odkazu z archeologického záznamu pomoci modalu.

   **Metody:**

   .. py:method:: init_translation()

   .. py:method:: dispatch()

   .. py:method:: get_zaznam()

   .. py:method:: get_context_data()

   .. py:method:: post()


.. py:class:: ExterniZdrojAutocomplete

   Třída pohledu pro autocomplete externích zdrojů.

   **Metody:**

   .. py:method:: get_result_label()

   .. py:method:: get_queryset()

   .. py:method:: add_accessibility_lookup()


.. py:class:: ExterniZdrojTableRowView

   Třída pohledu pro získaní řádku tabulky s externím zdrojem.

   **Metody:**

   .. py:method:: get()


.. py:class:: ExterniOdkazPripojitDoAzView

   Třída pohledu pro připojení externího odkazu do arch záznamu.

   **Metody:**

   .. py:method:: get_zaznam()

   .. py:method:: get_context_data()

   .. py:method:: post()


.. py:class:: EzOdkazyTableView

   Třída pohledu pro zobrazení řádků tabulky externích odkazů.

   **Metody:**

   .. py:method:: get()


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
