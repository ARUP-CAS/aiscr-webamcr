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

      :return: Vrací proměnná ``qs``.


.. py:class:: UzivatelAutocomplete

   Třída pohledu pro získaní uživatelů pro autocomplete.

   **Metody:**

   .. py:method:: get_result_label()

      Vrací result label.

      :param result: Textový název, klíč nebo zpráva ``result`` používaná v rámci operace.

      :return: Vrací výsledek volání ``display_name()``.

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      :return: Vrací výsledek volání ``check_filter_permission()``.

   .. py:method:: add_accessibility_lookup()

      Provádí operaci add accessibility lookup.

      :param permission: Parametr ``permission`` slouží jako vstup pro logiku funkce ``add_accessibility_lookup``.
      :param qs: Parametr ``qs`` vstupuje do návratové hodnoty.

      :return: Vrací proměnná ``qs``.

   .. py:method:: add_ownership_lookup()

      Provádí operaci add ownership lookup.

      :param ownership: Uživatel nebo osoba ``ownership``, v jejímž kontextu se operace provádí.
      :param qs: Parametr ``qs`` slouží jako vstup pro logiku funkce ``add_ownership_lookup``.

      :return: Vrací výsledek volání ``Q()``.


.. py:class:: UzivatelAutocompletePublic

   Třída pohledu pro získaní uživatelů pro autocomplete - verze pouze s ident_cely uživatele, beze jména.

   **Metody:**

   .. py:method:: get_result_label()

      Vrací result label.

      :param result: Textový název, klíč nebo zpráva ``result`` používaná v rámci operace.

      :return: Vrací výsledek volání ``display_name()``.

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      :return: Vrací proměnná ``qs``.


.. py:class:: UserRegistrationView

   Třída pohledu pro registraci uživatele.

   **Metody:**

   .. py:method:: send_activation_email()

      Odešle activation email.

      :param user: Parametr ``user`` se předává do volání ``send_activation_email()``, ``_log_notification()``, pracuje se s atributy ``email``.


.. py:class:: UserLoginView

   Třída pohledu pro prihlášení uživatele.


.. py:class:: UserLogoutView

   Třída pohledu pro odhlášení uživatele, kvůli zobrazení info o logoutu

   **Metody:**

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Parametr ``request`` předává se do volání ``post()``, pracuje se s atributy ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` se předává do volání ``post()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``post()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``post()``.


.. py:class:: UserAccountUpdateView

   Třída pohledu pro editaci uživatele.

   **Metody:**

   .. py:method:: get_object()

      Vrací object. v aplikaci.

      :param queryset: Parametr ``queryset`` slouží jako vstup pro logiku funkce ``get_object``.

      :return: Vrací výsledek volání ``get()``.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.

   .. py:method:: _change_password()

             Provádí operaci change password.

      :param request: Parametr ``request`` předává se do volání ``Historie()``, ``add_message()``, pracuje se s atributy ``user``.
      :param request_data: Kolekce ``request_data`` zpracovávaná touto funkcí.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: invalid_form_context()

      Provádí operaci invalid form context.

      :param form: Parametr ``form`` slouží jako vstup pro logiku funkce ``invalid_form_context``.
      :param form_tag: Parametr ``form_tag`` slouží jako vstup pro logiku funkce ``invalid_form_context``.

      :return: Vrací proměnná ``context``.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Parametr ``request`` předává se do volání ``dict()``, ``form_class()``, pracuje se s atributy ``POST``, ``user``, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``render()``, výsledek volání ``redirect()``.


.. py:class:: UserActivationView

   Třída pohledu pro aktivaci uživatele.

   **Metody:**

   .. py:method:: dispatch()

             Provádí operaci dispatch.

      :param request: Parametr ``request`` předává se do volání ``dispatch()``, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: activate()

      Provádí operaci activate.

      :param form: Parametr ``form`` pracuje se s atributy ``cleaned_data``.

      :return: Vrací proměnná ``user``.


.. py:class:: UserPasswordResetView

   Třída pohledu pro resetování hesla.

   **Metody:**

   .. py:method:: dispatch()

             Provádí operaci dispatch.

      :param request: Parametr ``request`` předává se do volání ``dispatch()``, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
      :return: Výstup funkce odpovídající implementované logice.


.. py:class:: TokenAuthenticationBearer

   Override třídy pro nastavení názvu tokenu na Bearer.

   **Metody:**

   .. py:method:: dispatch()

             Provádí operaci dispatch.

      :param request: Parametr ``request`` předává se do volání ``dispatch()``, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: authenticate_credentials()

      Provádí operaci authenticate credentials.

      :param key: Textový název nebo klíč ``key`` používaný v rámci operace.

      :return: Vrací n-tici.
      :raises exceptions.AuthenticationFailed: Vyvolá se při zpracování zachycené výjimky typu ``model.DoesNotExist``; nebo při splnění podmínky ``not token.user.is_active``.


.. py:class:: UserDeleteRequest

   Třída pohledu pro požádání o smazání účtu

   **Metody:**

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Parametr ``request`` předává se do volání ``send_eu07()``, ``add_message()``, pracuje se s atributy ``user``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

      :return: Vrací výsledek volání ``JsonResponse()``.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` předává se do volání ``render()``, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get``.

      :return: Vrací výsledek volání ``render()``.


Funkce
------

.. py:function:: create_osoba(request)

   Funkce pohledu pro vytvoření osoby.

   :param request: Parametr ``request`` se předává do volání ``OsobaForm()``, ``add_message()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``render()``, výsledek volání ``JsonResponse()``.

.. py:function:: update_notifications(request)

   Funkce pohledu pro editaci notifikací.

   :param request: Parametr ``request`` se předává do volání ``NotificationsForm()``, ``FedoraTransaction()``, pracuje se s atributy ``POST``, ``user``.

   :return: Vrací výsledek volání ``redirect()``.
