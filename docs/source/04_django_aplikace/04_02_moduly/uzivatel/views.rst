UZIVATEL views
==============

Definice views.

Třídy
------

.. py:class:: OsobaAutocomplete

   Třída pohledu pro získaní osob pro autocomplete.

   **Metody:**

   .. py:method:: get_queryset()


.. py:class:: UzivatelAutocomplete

   Třída pohledu pro získaní uživatelů pro autocomplete.

   **Metody:**

   .. py:method:: get_result_label()

   .. py:method:: get_queryset()

   .. py:method:: add_accessibility_lookup()

   .. py:method:: add_ownership_lookup()


.. py:class:: UzivatelAutocompletePublic

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_result_label()

   .. py:method:: get_queryset()


.. py:class:: UserRegistrationView

   Třída pohledu pro registraci uživatele.

   **Metody:**

   .. py:method:: send_activation_email()


.. py:class:: UserLoginView

   Třída pohledu pro prihlášení uživatele.


.. py:class:: UserLogoutView

   Třída pohledu pro odhlášení uživatele, kvůli zobrazení info o logoutu

   **Metody:**

   .. py:method:: post()


.. py:class:: UserAccountUpdateView

   Třída pohledu pro editaci uživatele.

   **Metody:**

   .. py:method:: get_object()

   .. py:method:: get_context_data()

   .. py:method:: _change_password()

   .. py:method:: invalid_form_context()

   .. py:method:: post()


.. py:class:: UserActivationView

   Třída pohledu pro aktivaci uživatele.

   **Metody:**

   .. py:method:: dispatch()

   .. py:method:: activate()


.. py:class:: UserPasswordResetView

   Třída pohledu pro resetování hesla.

   **Metody:**

   .. py:method:: dispatch()


.. py:class:: TokenAuthenticationBearer

   Override třídy pro nastavení názvu tokenu na Bearer.

   **Metody:**

   .. py:method:: dispatch()

   .. py:method:: authenticate_credentials()


.. py:class:: MyXMLRenderer

   Override třídy pro nastavení správnych tagů.

   **Metody:**

   .. py:method:: render()

      Renders `data` into serialized XML.


.. py:class:: GetUserInfo

   Třída podlehu pro získaní základních info o uživately.

   **Metody:**

   .. py:method:: get()

   .. py:method:: handle_exception()

   .. py:method:: perform_content_negotiation()

   .. py:method:: finalize_response()


.. py:class:: ObtainAuthTokenWithUpdate

   Třída pohledu pro získaní tokenu pro API.

   **Metody:**

   .. py:method:: post()


.. py:class:: UserDeleteRequest

   Třída pohledu pro požádání o smazání účtu

   **Metody:**

   .. py:method:: post()

   .. py:method:: get()


Funkce
------

.. py:function:: create_osoba(request)

   Funkce pohledu pro vytvoření osoby.

.. py:function:: update_notifications(request)

   Funkce pohledu pro editaci notifikací.
