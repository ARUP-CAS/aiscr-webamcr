UZIVATEL admin
==============

Konfigurace Django admin.

Třídy
------

.. py:class:: UserNotificationTypeInlineForm

   Inline form pro nastavení notifikací uživatele.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.



.. py:class:: UserNotificationTypeInlineFormset

   Implementuje komponentu ``UserNotificationTypeInlineFormset`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.



.. py:class:: UserNotificationTypeInline

   Inline panel pro nastavení notifikací uživatele.

   **Metody:**

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``get_queryset()``.

      **Návratová hodnota:**

      Vrací proměnná ``queryset``.


   .. py:method:: get_extra()

      Vrací extra. v aplikaci.

      **Parametry:**

      - ``request``: Parametr ``request`` slouží jako vstup pro logiku funkce ``get_extra``.
      - ``obj``: Parametr ``obj`` ovlivňuje větvení podmínek.
      - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get_extra``.

      **Návratová hodnota:**

      Vrací proměnná ``extra``.


   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``parent_model``: Parametr ``parent_model`` předává se do volání ``__init__()``.
      - ``admin_site``: Instance administrace předaná při registraci modelu.



.. py:class:: PesNotificationTypeInline

   Inline panel pro nastavení hlídacích psů uživatele.

   **Metody:**

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``get_queryset()``.

      **Návratová hodnota:**

      Vrací proměnná ``queryset``.



.. py:class:: PesKrajNotificationTypeInline

   Inline panel pro nastavení hlídacích psů uživatele pro kraj.


.. py:class:: PesOkresNotificationTypeInline

   Inline panel pro nastavení hlídacích psů uživatele pro okres.


.. py:class:: PesKatastrNotificationTypeInline

   Inline panel pro nastavení hlídacích psů uživatele pro katastr.


.. py:class:: PesUserNotificationTypeInlineForm

   Inline form pro nastavení notifikací uživatele.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.



.. py:class:: PesUserNotificationTypeInlineFormset

   Implementuje komponentu ``PesUserNotificationTypeInlineFormset`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.



.. py:class:: PesUserNotificationTypeInline

   Inline panel pro nastavení notifikací uživatele.

   **Metody:**

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``get_queryset()``.

      **Návratová hodnota:**

      Vrací proměnná ``queryset``.


   .. py:method:: get_extra()

      Vrací extra. v aplikaci.

      **Parametry:**

      - ``request``: Parametr ``request`` slouží jako vstup pro logiku funkce ``get_extra``.
      - ``obj``: Parametr ``obj`` ovlivňuje větvení podmínek.
      - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get_extra``.

      **Návratová hodnota:**

      Vrací proměnná ``extra``.



.. py:class:: CustomUserAdmin

   Admin panel pro správu uživatele.

   **Metody:**

   .. py:method:: has_delete_permission()

      Určí, zda delete permission.

      **Parametry:**

      - ``request``: Parametr ``request`` slouží jako vstup pro logiku funkce ``has_delete_permission``.
      - ``obj``: Parametr ``obj`` předává se do volání ``filter()``, ovlivňuje větvení podmínek.

      **Návratová hodnota:**

      Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.


   .. py:method:: save_model()

      Uloží model. v aplikaci.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``save_model()``, pracuje se s atributy ``user``.
      - ``obj``: Parametr ``obj`` předává se do volání ``debug()``, ``get()``, pracuje se s atributy ``created_from_admin_panel``, ``active_transaction``, ovlivňuje větvení podmínek.
      - ``form``: Parametr ``form`` se předává do volání ``save_model()``, ``len()``, pracuje se s atributy ``cleaned_data``, ``changed_data``, ovlivňuje větvení podmínek.
      - ``change``: Parametr ``change`` se předává do volání ``debug()``, ``save_model()``.


   .. py:method:: user_change_password()

      Provádí operaci user change password.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``get_object()``, ``change_password_form()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      - ``id``: Identifikátor zpracovávaného záznamu.
      - ``form_url``: Parametr ``form_url`` se předává do volání ``user_change_password()``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací výsledek volání ``user_change_password()``.


   .. py:method:: get_readonly_fields()

      Vrací readonly fields.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``get_readonly_fields()``, pracuje se s atributy ``user``, ovlivňuje větvení podmínek.
      - ``obj``: Parametr ``obj`` předává se do volání ``get_readonly_fields()``, pracuje se s atributy ``ident_cely``, ovlivňuje větvení podmínek.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: hodnotu podle větve zpracování, proměnná ``fields``.


   .. py:method:: render_change_form()

      Vyrenderuje change form.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``render_change_form()``, pracuje se s atributy ``resolver_match``, vstupuje do návratové hodnoty.
      - ``context``: Parametr ``context`` se předává do volání ``render_change_form()``, pracuje se s atributy ``update``, vstupuje do návratové hodnoty.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``render_change_form()``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací výsledek volání ``render_change_form()``.


   .. py:method:: get_urls()

      Vrací urls. v aplikaci.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování.


   .. py:method:: get_histore_related_records()

      Vrací histore related records.

      **Parametry:**

      - ``object_id``: Identifikátor objektu ``object``.

      **Návratová hodnota:**

      Vrací n-tici.


   .. py:method:: delete_history_records()

      Odstraní history records.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``get_object()``, ``each_context()``, pracuje se s atributy ``method``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      - ``object_id``: Identifikátor objektu ``object``.
      - ``args``: Parametr ``args`` slouží jako vstup pro logiku funkce ``delete_history_records``.
      - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``delete_history_records``.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``TemplateResponse()``, výsledek volání ``HttpResponseRedirect()``.


   .. py:method:: delete_model()

      Odstraní model. v aplikaci.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``delete_model()``.
      - ``obj``: Parametr ``obj`` předává se do volání ``delete_model()``, pracuje se s atributy ``pes_set``.



.. py:class:: CustomGroupAdmin

   Admin panel pro správu uživatelskych skupin.

   **Metody:**

   .. py:method:: has_delete_permission()

      Určí, zda delete permission.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``has_delete_permission()``, vstupuje do návratové hodnoty.
      - ``obj``: Parametr ``obj`` předává se do volání ``filter()``, pracuje se s atributy ``pk``, ovlivňuje větvení podmínek.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: bool, výsledek volání ``has_delete_permission()``.



.. py:class:: NotificationsLogAdmin

   Admin panel pro kontrolu odeslaných mailů s možností poslat testovací mail.

   **Metody:**

   .. py:method:: created()

      Vrátí datum a čas vytvoření záznamu ve formátu pro administraci.

      **Parametry:**

      - ``obj``: Záznam logu notifikace.

      **Návratová hodnota:**

      Formátovaný datum a čas vytvoření.


   .. py:method:: status_colored()

      Vrátí barevně zvýrazněný stav odeslání notifikace.

      **Parametry:**

      - ``obj``: Záznam logu notifikace.

      **Návratová hodnota:**

      HTML reprezentace stavu notifikace.


   .. py:method:: get_readonly_fields()

      Nastaví všechna pole modelu jako read-only v detailu záznamu.

      **Parametry:**

      - ``request``: Parametr ``request`` slouží jako vstup pro logiku funkce ``get_readonly_fields``.
      - ``obj``: Upravovaný záznam logu notifikace.

      **Návratová hodnota:**

      Seznam názvů polí určených pouze ke čtení.


   .. py:method:: has_add_permission()

      Zakáže ruční vytváření záznamů v administraci.

      **Parametry:**

      - ``request``: Parametr ``request`` slouží jako vstup pro logiku funkce ``has_add_permission``.

      **Návratová hodnota:**

      Vždy ```False```.


   .. py:method:: has_delete_permission()

      Zakáže mazání záznamů logu notifikací.

      **Parametry:**

      - ``request``: Parametr ``request`` slouží jako vstup pro logiku funkce ``has_delete_permission``.
      - ``obj``: Vybraný záznam logu notifikace.

      **Návratová hodnota:**

      Vždy ```False```.


   .. py:method:: get_urls()

      Přidá vlastní URL pro odeslání testovacího emailu z administrace.

      **Návratová hodnota:**

      Seznam URL vzorů pro tento admin.


   .. py:method:: test_email_view()

      Zobrazí a zpracuje formulář pro odeslání testovacího emailu.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``TestEmailForm()``, ``success()``, pracuje se s atributy ``user``, ``method``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Odpověď s formulářem a výsledkem odeslání.

      **Výjimky:**

      - ``PermissionDenied``: Vyvolá se při splnění podmínky ``not request.user.has_perm('uzivatel.send_test_email')``.


