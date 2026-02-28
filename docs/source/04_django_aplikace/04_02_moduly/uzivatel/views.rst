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

      :param result: Vstupní hodnota ``result`` pro danou operaci.

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

   .. py:method:: add_accessibility_lookup()

      Provádí operaci add accessibility lookup.

      :param permission: Vstupní hodnota ``permission`` pro danou operaci.
      :param qs: Vstupní hodnota ``qs`` pro danou operaci.

   .. py:method:: add_ownership_lookup()

      Provádí operaci add ownership lookup.

      :param ownership: Vstupní hodnota ``ownership`` pro danou operaci.
      :param qs: Vstupní hodnota ``qs`` pro danou operaci.


.. py:class:: UzivatelAutocompletePublic

   Třída pohledu pro získaní uživatelů pro autocomplete - verze pouze s ident_cely uživatele, beze jména.

   **Metody:**

   .. py:method:: get_result_label()

      Vrací result label.

      :param result: Vstupní hodnota ``result`` pro danou operaci.

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.


.. py:class:: UserRegistrationView

   Třída pohledu pro registraci uživatele.

   **Metody:**

   .. py:method:: send_activation_email()

      Odešle activation email.

      :param user: Vstupní hodnota ``user`` pro danou operaci.


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

      :param queryset: Vstupní hodnota ``queryset`` pro danou operaci.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: _change_password()

      Provádí operaci change password.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param request_data: Vstupní hodnota ``request_data`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: invalid_form_context()

      Provádí operaci invalid form context.

      :param form: Vstupní hodnota ``form`` pro danou operaci.
      :param form_tag: Vstupní hodnota ``form_tag`` pro danou operaci.

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
      :return: Vrací výsledek provedené operace.

   .. py:method:: activate()

      Provádí operaci activate.

      :param form: Vstupní hodnota ``form`` pro danou operaci.


.. py:class:: UserPasswordResetView

   Třída pohledu pro resetování hesla.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.


.. py:class:: TokenAuthenticationBearer

   Override třídy pro nastavení názvu tokenu na Bearer.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.

   .. py:method:: authenticate_credentials()

      Provádí operaci authenticate credentials.

      :param key: Vstupní hodnota ``key`` pro danou operaci.


.. py:class:: MyXMLRenderer

   Override třídy pro nastavení správnych tagů.

   **Metody:**

   .. py:method:: render()

      Renders `data` into serialized XML.

      :param data: Popis parametru ``data``.
      :param accepted_media_type: Popis parametru ``accepted_media_type``.
      :param renderer_context: Popis parametru ``renderer_context``.


.. py:class:: GetUserInfo

   Třída podlehu pro získaní základních info o uživately.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param format: Vstupní hodnota ``format`` pro danou operaci.

   .. py:method:: handle_exception()

      Zpracuje exception. v aplikaci.

      :param exc: Vstupní hodnota ``exc`` pro danou operaci.

   .. py:method:: perform_content_negotiation()

      Provádí operaci perform content negotiation.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param force: Vstupní hodnota ``force`` pro danou operaci.

   .. py:method:: finalize_response()

      Provádí operaci finalize response.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param response: Vstupní hodnota ``response`` pro danou operaci.
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

   :param request: Popis parametru ``request``.

.. py:function:: update_notifications(request)

   Funkce pohledu pro editaci notifikací.

   :param request: Popis parametru ``request``.
