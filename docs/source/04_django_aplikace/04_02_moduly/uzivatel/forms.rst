UZIVATEL formuláře
==================

Definice formulářů.

Třídy
------

.. py:class:: AuthUserCreationForm

   Formulář pro vytvoření uživatele.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: AuthUserCreationFormWithRecaptcha

   Implementuje komponentu ``AuthUserCreationFormWithRecaptcha`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: AuthUserChangeForm

   Formulář pro editaci uživatele.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: AuthReadOnlyUserChangeForm

   Formulář pro zobrazení detailu uživatele.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: AuthUserChangeAdminForm

   Implementuje komponentu ``AuthUserChangeAdminForm`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: NotificationsForm

   Formulář pro správu typu notifikací.


.. py:class:: UpdatePasswordSettings

   Formulář pro změnu hesla.

   **Metody:**

   .. py:method:: clean()

      Provádí operaci clean.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: AuthUserLoginForm

   Formulář pro prihlášení uživatele.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: get_invalid_login_error()

      Vrací invalid login error.


.. py:class:: UserPasswordResetForm

   Implementuje komponentu ``UserPasswordResetForm`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: send_mail()

      Send a django.core.mail.EmailMultiAlternatives to `to_email`.

      :param subject_template_name: Popis parametru ``subject_template_name``.
      :param email_template_name: Popis parametru ``email_template_name``.
      :param context: Popis parametru ``context``.
      :param from_email: Popis parametru ``from_email``.
      :param to_email: Popis parametru ``to_email``.
      :param html_email_template_name: Popis parametru ``html_email_template_name``.


.. py:class:: OsobaForm

   Formulář pro vytvoření osoby.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: AuthActivationForm

   Implementuje komponentu ``AuthActivationForm`` v rámci aplikace.

