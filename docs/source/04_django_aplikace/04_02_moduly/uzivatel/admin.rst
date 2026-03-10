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

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.


.. py:class:: UserNotificationTypeInlineFormset

   Implementuje komponentu ``UserNotificationTypeInlineFormset`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.


.. py:class:: UserNotificationTypeInline

   Inline panel pro nastavení notifikací uživatele.

   **Metody:**

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      :param request: Parametr ``request`` předává se do volání ``get_queryset()``.

      :return: Vrací proměnná ``queryset``.

   .. py:method:: get_extra()

      Vrací extra. v aplikaci.

      :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get_extra``.
      :param obj: Parametr ``obj`` ovlivňuje větvení podmínek.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get_extra``.

      :return: Vrací proměnná ``extra``.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param parent_model: Parametr ``parent_model`` předává se do volání ``__init__()``.
      :param admin_site: Instance administrace předaná při registraci modelu.


.. py:class:: PesNotificationTypeInline

   Inline panel pro nastavení hlídacích psů uživatele.

   **Metody:**

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      :param request: Parametr ``request`` předává se do volání ``get_queryset()``.

      :return: Vrací proměnná ``queryset``.


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

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.


.. py:class:: PesUserNotificationTypeInlineFormset

   Implementuje komponentu ``PesUserNotificationTypeInlineFormset`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.


.. py:class:: PesUserNotificationTypeInline

   Inline panel pro nastavení notifikací uživatele.

   **Metody:**

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      :param request: Parametr ``request`` předává se do volání ``get_queryset()``.

      :return: Vrací proměnná ``queryset``.

   .. py:method:: get_extra()

      Vrací extra. v aplikaci.

      :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get_extra``.
      :param obj: Parametr ``obj`` ovlivňuje větvení podmínek.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get_extra``.

      :return: Vrací proměnná ``extra``.


.. py:class:: CustomUserAdmin

   Admin panel pro správu uživatele.

   **Metody:**

   .. py:method:: has_delete_permission()

      Určí, zda delete permission.

      :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``has_delete_permission``.
      :param obj: Parametr ``obj`` předává se do volání ``filter()``, ovlivňuje větvení podmínek.

      :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.

   .. py:method:: save_model()

      Uloží model. v aplikaci.

      :param request: Parametr ``request`` předává se do volání ``save_model()``, pracuje se s atributy ``user``.
      :param obj: Parametr ``obj`` předává se do volání ``debug()``, ``get()``, pracuje se s atributy ``created_from_admin_panel``, ``active_transaction``, ovlivňuje větvení podmínek.
      :param form: Parametr ``form`` se předává do volání ``save_model()``, ``len()``, pracuje se s atributy ``cleaned_data``, ``changed_data``, ovlivňuje větvení podmínek.
      :param change: Parametr ``change`` se předává do volání ``debug()``, ``save_model()``.

   .. py:method:: user_change_password()

      Provádí operaci user change password.

      :param request: Parametr ``request`` předává se do volání ``get_object()``, ``change_password_form()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :param id: Identifikátor zpracovávaného záznamu.
      :param form_url: Parametr ``form_url`` se předává do volání ``user_change_password()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``user_change_password()``.

   .. py:method:: get_readonly_fields()

      Vrací readonly fields.

      :param request: Parametr ``request`` předává se do volání ``get_readonly_fields()``, pracuje se s atributy ``user``, ovlivňuje větvení podmínek.
      :param obj: Parametr ``obj`` předává se do volání ``get_readonly_fields()``, pracuje se s atributy ``ident_cely``, ovlivňuje větvení podmínek.

      :return: Vrací hodnotu podle větve zpracování, typicky: hodnotu podle větve zpracování, proměnná ``fields``.

   .. py:method:: render_change_form()

      Vyrenderuje change form.

      :param request: Parametr ``request`` předává se do volání ``render_change_form()``, pracuje se s atributy ``resolver_match``, vstupuje do návratové hodnoty.
      :param context: Parametr ``context`` se předává do volání ``render_change_form()``, pracuje se s atributy ``update``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``render_change_form()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``render_change_form()``.

   .. py:method:: get_urls()

      Vrací urls. v aplikaci.

      :return: Vrací hodnotu podle větve zpracování.

   .. py:method:: get_histore_related_records()

      Vrací histore related records.

      :param object_id: Identifikátor objektu ``object``.

      :return: Vrací n-tici.

   .. py:method:: delete_history_records()

      Odstraní history records.

      :param request: Parametr ``request`` předává se do volání ``get_object()``, ``each_context()``, pracuje se s atributy ``method``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :param object_id: Identifikátor objektu ``object``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``delete_history_records``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``delete_history_records``.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``TemplateResponse()``, výsledek volání ``HttpResponseRedirect()``.

   .. py:method:: delete_model()

      Odstraní model. v aplikaci.

      :param request: Parametr ``request`` předává se do volání ``delete_model()``.
      :param obj: Parametr ``obj`` předává se do volání ``delete_model()``, pracuje se s atributy ``pes_set``.


.. py:class:: CustomGroupAdmin

   Admin panel pro správu uživatelskych skupin.

   **Metody:**

   .. py:method:: has_delete_permission()

      Určí, zda delete permission.

      :param request: Parametr ``request`` předává se do volání ``has_delete_permission()``, vstupuje do návratové hodnoty.
      :param obj: Parametr ``obj`` předává se do volání ``filter()``, pracuje se s atributy ``pk``, ovlivňuje větvení podmínek.

      :return: Vrací hodnotu podle větve zpracování, typicky: bool, výsledek volání ``has_delete_permission()``.


.. py:class:: NotificationsLogAdmin

   Admin panel pro kontrolu odeslaných mailů s možností poslat testovací mail.

   **Metody:**

   .. py:method:: created()

      Vrátí datum a čas vytvoření záznamu ve formátu pro administraci.

      :param obj: Záznam logu notifikace.
      :return: Formátovaný datum a čas vytvoření.

   .. py:method:: status_colored()

      Vrátí barevně zvýrazněný stav odeslání notifikace.

      :param obj: Záznam logu notifikace.
      :return: HTML reprezentace stavu notifikace.

   .. py:method:: get_readonly_fields()

      Nastaví všechna pole modelu jako read-only v detailu záznamu.

      :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get_readonly_fields``.
      :param obj: Upravovaný záznam logu notifikace.
      :return: Seznam názvů polí určených pouze ke čtení.

   .. py:method:: has_add_permission()

      Zakáže ruční vytváření záznamů v administraci.

      :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``has_add_permission``.
      :return: Vždy ```False```.

   .. py:method:: has_delete_permission()

      Zakáže mazání záznamů logu notifikací.

      :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``has_delete_permission``.
      :param obj: Vybraný záznam logu notifikace.
      :return: Vždy ```False```.

   .. py:method:: get_urls()

      Přidá vlastní URL pro odeslání testovacího emailu z administrace.

      :return: Seznam URL vzorů pro tento admin.

   .. py:method:: test_email_view()

      Zobrazí a zpracuje formulář pro odeslání testovacího emailu.

      :param request: Parametr ``request`` předává se do volání ``TestEmailForm()``, ``success()``, pracuje se s atributy ``user``, ``method``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :return: Odpověď s formulářem a výsledkem odeslání.

      :raises PermissionDenied: Vyvolá se při splnění podmínky ``not request.user.has_perm('uzivatel.send_test_email')``.

