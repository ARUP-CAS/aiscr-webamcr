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

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: ExterniZdrojListView

   Třida pohledu pro zobrazení listu/tabulky s externím zdrojem.

   **Metody:**

   .. py:method:: init_translations()

      Provádí operaci init translations.

   .. py:method:: rename_field_for_ordering()

      Provádí operaci rename field for ordering.

      :param field: Záznam/objekt ``field``, který funkce čte, validuje nebo upravuje.

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

   .. py:method:: add_accessibility_lookup()

      Provádí operaci add accessibility lookup.

      :param permission: Typová nebo konfigurační hodnota `permission` určující cílovou logiku.
      :param qs: Vstupní queryset, který má být dále zpracován.


.. py:class:: ExterniZdrojDetailView

   Třida pohledu pro zobrazení detailu externího zdroju.

   **Metody:**

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: ExterniZdrojCreateView

   Třida pohledu pro vytvoření externího zdroje.

   **Metody:**

   .. py:method:: get_form_kwargs()

      Vrací form kwargs.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: form_valid()

      Provádí operaci form valid.

      :param form: Formulářová instance zpracovávaná funkcí.

   .. py:method:: form_invalid()

      Provádí operaci form invalid.

      :param form: Formulářová instance zpracovávaná funkcí.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: ExterniZdrojEditView

   Třida pohledu pro editaci externího zdroje.

   **Metody:**

   .. py:method:: get_form_kwargs()

      Vrací form kwargs.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: form_valid()

      Provádí operaci form valid.

      :param form: Formulářová instance zpracovávaná funkcí.

   .. py:method:: form_invalid()

      Provádí operaci form invalid.

      :param form: Formulářová instance zpracovávaná funkcí.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: TransakceView

   Třida pohledu pro změnu stavu a práci s externíma zdrojama cez modal, která se dedí pro jednotlivá změny.

   **Metody:**

   .. py:method:: init_translation()

      Provádí operaci init translation.

   .. py:method:: get_zaznam()

      Vrací zaznam. v aplikaci.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: ExterniZdrojOdeslatView

   Třida pohledu pro odeslání externího zdroje pomoci modalu.

   **Metody:**

   .. py:method:: init_translation()

      Provádí operaci init translation.


.. py:class:: ExterniZdrojPotvrditView

   Třida pohledu pro potvrzení externího zdroje pomoci modalu.

   **Metody:**

   .. py:method:: init_translation()

      Provádí operaci init translation.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: ExterniZdrojSmazatView

   Třida pohledu pro smazání externího zdroje pomoci modalu.

   **Metody:**

   .. py:method:: init_translation()

      Provádí operaci init translation.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: ExterniZdrojVratitView

   Třida pohledu pro vrácení externího zdroje pomoci modalu.

   **Metody:**

   .. py:method:: init_translation()

      Provádí operaci init translation.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: ExterniOdkazOdpojitView

   Třida pohledu pro odpojení externího odkazu pomoci modalu.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: init_translation()

      Provádí operaci init translation.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: ExterniOdkazPripojitView

   Třida pohledu pro připojení externího odkazu pomoci modalu.

   **Metody:**

   .. py:method:: init_translation()

      Provádí operaci init translation.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: ExterniOdkazEditView

   Třida pohledu pro editaci externího odkazu pomoci modalu.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: get_success_url()

      Vrací success url.

   .. py:method:: get_object()

      Vrací object. v aplikaci.

      :param queryset: Vstupní queryset, který má být dále zpracován.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: form_valid()

      Provádí operaci form valid.

      :param form: Formulářová instance zpracovávaná funkcí.

   .. py:method:: form_invalid()

      Provádí operaci form invalid.

      :param form: Formulářová instance zpracovávaná funkcí.


.. py:class:: ExterniOdkazOdpojitAZView

   Třida pohledu pro odpojení externího odkazu z archeologického záznamu pomoci modalu.

   **Metody:**

   .. py:method:: init_translation()

      Provádí operaci init translation.

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: get_zaznam()

      Vrací zaznam. v aplikaci.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: ExterniZdrojAutocomplete

   Třída pohledu pro autocomplete externích zdrojů.

   **Metody:**

   .. py:method:: get_result_label()

      Vrací result label.

      :param result: Textový název, klíč nebo zpráva ``result`` používaná v rámci operace.

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

   .. py:method:: add_accessibility_lookup()

      Provádí operaci add accessibility lookup.

      :param permission: Typová nebo konfigurační hodnota `permission` určující cílovou logiku.
      :param qs: Vstupní queryset, který má být dále zpracován.


.. py:class:: ExterniZdrojTableRowView

   Třída pohledu pro získaní řádku tabulky s externím zdrojem.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.


.. py:class:: ExterniOdkazPripojitDoAzView

   Třída pohledu pro připojení externího odkazu do arch záznamu.

   **Metody:**

   .. py:method:: get_zaznam()

      Vrací zaznam. v aplikaci.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: EzOdkazyTableView

   Třída pohledu pro zobrazení řádků tabulky externích odkazů.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.


Funkce
------

.. py:function:: get_history_dates(historie_vazby, request_user)

   Funkce pro získaní historických datumu.

   :param historie_vazby: Kolekce ``historie_vazby`` zpracovávaná touto funkcí.
   :param request_user: Uživatel nebo osoba ``request_user``, v jejímž kontextu se operace provádí.
   :return: Slovník dat jednotlivých změn stavu pro zobrazení v historii.

.. py:function:: get_detail_template_shows(zaznam, user)

   Funkce pro získaní kontextu pro zobrazování možností na stránkách.

   :param zaznam: Záznam/objekt ``zaznam``, který funkce čte, validuje nebo upravuje.
   :param user: Uživatel, v jehož kontextu se operace provádí.
   :return: Slovník příznaků určujících, které akce a sekce detailu se mají zobrazit.

.. py:function:: get_required_fields()

   Funkce pro získaní dictionary povinných polí podle stavu externího zdroje.

.. py:function:: save_autor_editor(zaznam, form)

   Funkce pro uložení autorů a editorů k externímu zdroji podle toho v jakém pořadí byly zadáni.

   :param zaznam: Záznam/objekt ``zaznam``, který funkce čte, validuje nebo upravuje.
   :param form: Formulářová instance zpracovávaná funkcí.
