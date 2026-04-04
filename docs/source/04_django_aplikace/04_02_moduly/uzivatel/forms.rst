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

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``, ``OrcidAutocompleteField()``, pracuje se s atributy ``get``.



.. py:class:: AuthUserCreationFormWithRecaptcha

   Implementuje komponentu ``AuthUserCreationFormWithRecaptcha`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.



.. py:class:: AuthUserChangeForm

   Formulář pro editaci uživatele.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``, ``OrcidAutocompleteField()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.



.. py:class:: AuthReadOnlyUserChangeForm

   Formulář pro zobrazení detailu uživatele.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.



.. py:class:: AuthUserChangeAdminForm

   Implementuje komponentu ``AuthUserChangeAdminForm`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``, ``OrcidAutocompleteField()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.



.. py:class:: NotificationsForm

   Formulář pro správu typu notifikací.


.. py:class:: UpdatePasswordSettings

   Formulář pro změnu hesla.

   **Metody:**

   .. py:method:: clean()

      Provádí operaci clean.

      **Výjimky:**

      - ``ValidationError``: Vyvolá se při splnění podmínky ``not old_password and (password1 or password2)``; nebo při splnění podmínky ``old_password and (not (password1 or password2))``.


   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.



.. py:class:: AuthUserLoginForm

   Formulář pro prihlášení uživatele.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.


   .. py:method:: get_invalid_login_error()

      Vrací invalid login error.

      **Návratová hodnota:**

      Vrací výsledek volání ``ValidationError()``.



.. py:class:: UserPasswordResetForm

   Implementuje komponentu ``UserPasswordResetForm`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.


   .. py:method:: send_mail()

      Send a django.core.mail.EmailMultiAlternatives to `to_email`.

      **Parametry:**

      - ``subject_template_name``: Parametr ``subject_template_name`` se předává do volání ``render_to_string()``.
      - ``email_template_name``: Parametr ``email_template_name`` se předává do volání ``render_to_string()``.
      - ``context``: Parametr ``context`` se předává do volání ``render_to_string()``, ``_log_notification()``.
      - ``from_email``: Uživatel nebo osoba ``from_email``, v jejímž kontextu se operace provádí.
      - ``to_email``: Uživatel nebo osoba ``to_email``, v jejímž kontextu se operace provádí.
      - ``html_email_template_name``: Parametr ``html_email_template_name`` se předává do volání ``render_to_string()``, ovlivňuje větvení podmínek.



.. py:class:: OsobaForm

   Formulář pro vytvoření osoby.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``, pracuje se s atributy ``pop``.



.. py:class:: AuthActivationForm

   Implementuje komponentu ``AuthActivationForm`` v rámci aplikace.


.. py:class:: TestEmailForm

   Formulář pro odeslání testovacího mailu v administraci.

