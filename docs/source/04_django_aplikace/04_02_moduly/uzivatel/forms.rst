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
      :return: Funkce nevrací hodnotu (``None``).


.. py:class:: AuthUserCreationFormWithRecaptcha

   Implementuje komponentu ``AuthUserCreationFormWithRecaptcha`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).


.. py:class:: AuthUserChangeForm

   Formulář pro editaci uživatele.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).


.. py:class:: AuthReadOnlyUserChangeForm

   Formulář pro zobrazení detailu uživatele.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).


.. py:class:: AuthUserChangeAdminForm

   Implementuje komponentu ``AuthUserChangeAdminForm`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).


.. py:class:: NotificationsForm

   Formulář pro správu typu notifikací.


.. py:class:: UpdatePasswordSettings

   Formulář pro změnu hesla.

   **Metody:**

   .. py:method:: clean()

      Provádí operaci clean.

      :return: Vrací výsledek provedené operace.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).


.. py:class:: AuthUserLoginForm

   Formulář pro prihlášení uživatele.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: get_invalid_login_error()

      Vrací invalid login error.

      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: UserPasswordResetForm

   Implementuje komponentu ``UserPasswordResetForm`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: send_mail()

      Send a django.core.mail.EmailMultiAlternatives to `to_email`.


.. py:class:: OsobaForm

   Formulář pro vytvoření osoby.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).


.. py:class:: AuthActivationForm

   Implementuje komponentu ``AuthActivationForm`` v rámci aplikace.

