UZIVATEL views
==============

Definice views.

Třídy
------

.. py:class:: OsobaAutocomplete

   Třída pohledu pro získaní osob pro autocomplete.

   **Metody:**

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.


.. py:class:: UzivatelAutocomplete

   Třída pohledu pro získaní uživatelů pro autocomplete.

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

   .. py:method:: add_ownership_lookup()

      Provádí operaci add ownership lookup.

      :param ownership: Uživatel nebo osoba ``ownership``, v jejímž kontextu se operace provádí.
      :param qs: Vstupní queryset, který má být dále zpracován.


.. py:class:: UzivatelAutocompletePublic

   Třída pohledu pro získaní uživatelů pro autocomplete - verze pouze s ident_cely uživatele, beze jména.

   **Metody:**

   .. py:method:: get_result_label()

      Vrací result label.

      :param result: Textový název, klíč nebo zpráva ``result`` používaná v rámci operace.

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.


.. py:class:: UserRegistrationView

   Třída pohledu pro registraci uživatele.

   **Metody:**

   .. py:method:: send_activation_email()

      Odešle activation email.

      :param user: Uživatel, v jehož kontextu se operace provádí.


.. py:class:: UserLoginView

   Třída pohledu pro prihlášení uživatele.


.. py:class:: UserLogoutView

   Třída pohledu pro odhlášení uživatele, kvůli zobrazení info o logoutu

   **Metody:**

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: UserAccountUpdateView

   Třída pohledu pro editaci uživatele.

   **Metody:**

   .. py:method:: get_object()

      Vrací object. v aplikaci.

      :param queryset: Vstupní queryset, který má být dále zpracován.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: _change_password()

      Provádí operaci change password.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param request_data: Kolekce ``request_data`` zpracovávaná touto funkcí.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: invalid_form_context()

      Provádí operaci invalid form context.

      :param form: Formulářová instance zpracovávaná funkcí.
      :param form_tag: Záznam/objekt ``form_tag``, který funkce čte, validuje nebo upravuje.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: UserActivationView

   Třída pohledu pro aktivaci uživatele.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: activate()

      Provádí operaci activate.

      :param form: Formulářová instance zpracovávaná funkcí.


.. py:class:: UserPasswordResetView

   Třída pohledu pro resetování hesla.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Výstup funkce odpovídající implementované logice.


.. py:class:: TokenAuthenticationBearer

   Override třídy pro nastavení názvu tokenu na Bearer.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: authenticate_credentials()

      Provádí operaci authenticate credentials.

      :param key: Textový název nebo klíč ``key`` používaný v rámci operace.


.. py:class:: MyXMLRenderer

   Override třídy pro nastavení správnych tagů.

   **Metody:**

   .. py:method:: render()

      Renders `data` into serialized XML.

      :param data: Kolekce ``data`` zpracovávaná touto funkcí.
      :param accepted_media_type: Název nebo typ ``accepted_media_type`` používaný pro volbu cílové logiky.
      :param renderer_context: Kolekce ``renderer_context`` zpracovávaná touto funkcí.


.. py:class:: GetUserInfo

   Třída podlehu pro získaní základních info o uživately.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param format: Záznam/objekt ``format``, který funkce čte, validuje nebo upravuje.

   .. py:method:: handle_exception()

      Zpracuje exception. v aplikaci.

      :param exc: Číselná hodnota ``exc`` použitá při výpočtu nebo transformaci.

   .. py:method:: perform_content_negotiation()

      Provádí operaci perform content negotiation.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param force: Číselná nebo geometrická hodnota `force` použitá při výpočtu nebo transformaci.

   .. py:method:: finalize_response()

      Provádí operaci finalize response.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param response: Textový nebo strukturální vstup `response` používaný při sestavení nebo zpracování obsahu.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: ObtainAuthTokenWithUpdate

   Třída pohledu pro získaní tokenu pro API.

   **Metody:**

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: UserDeleteRequest

   Třída pohledu pro požádání o smazání účtu

   **Metody:**

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


Funkce
------

.. py:function:: create_osoba(request)

   Funkce pohledu pro vytvoření osoby.

   :param request: Aktuální HTTP request předaný view/funkci.

.. py:function:: update_notifications(request)

   Funkce pohledu pro editaci notifikací.

   :param request: Aktuální HTTP request předaný view/funkci.
