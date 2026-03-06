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

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: UserNotificationTypeInlineFormset

   Implementuje komponentu ``UserNotificationTypeInlineFormset`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: UserNotificationTypeInline

   Inline panel pro nastavení notifikací uživatele.

   **Metody:**

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      :param request: Django HTTP požadavek použitý při zpracování.

   .. py:method:: get_extra()

      Vrací extra. v aplikaci.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Vstupní hodnota ``obj`` pro danou operaci.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param parent_model: Vstupní hodnota ``parent_model`` pro danou operaci.
      :param admin_site: Vstupní hodnota ``admin_site`` pro danou operaci.


.. py:class:: PesNotificationTypeInline

   Inline panel pro nastavení hlídacích psů uživatele.

   **Metody:**

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      :param request: Django HTTP požadavek použitý při zpracování.


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

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: PesUserNotificationTypeInlineFormset

   Implementuje komponentu ``PesUserNotificationTypeInlineFormset`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: PesUserNotificationTypeInline

   Inline panel pro nastavení notifikací uživatele.

   **Metody:**

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      :param request: Django HTTP požadavek použitý při zpracování.

   .. py:method:: get_extra()

      Vrací extra. v aplikaci.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Vstupní hodnota ``obj`` pro danou operaci.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: CustomUserAdmin

   Admin panel pro správu uživatele.

   **Metody:**

   .. py:method:: has_delete_permission()

      Určí, zda delete permission.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Vstupní hodnota ``obj`` pro danou operaci.

   .. py:method:: save_model()

      Uloží model. v aplikaci.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Vstupní hodnota ``obj`` pro danou operaci.
      :param form: Vstupní hodnota ``form`` pro danou operaci.
      :param change: Vstupní hodnota ``change`` pro danou operaci.

   .. py:method:: user_change_password()

      Provádí operaci user change password.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param id: Identifikátor zpracovávaného záznamu.
      :param form_url: Vstupní hodnota ``form_url`` pro danou operaci.

   .. py:method:: get_readonly_fields()

      Vrací readonly fields.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Vstupní hodnota ``obj`` pro danou operaci.

   .. py:method:: render_change_form()

      Vyrenderuje change form.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param context: Vstupní hodnota ``context`` pro danou operaci.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: get_urls()

      Vrací urls. v aplikaci.

   .. py:method:: get_histore_related_records()

      Vrací histore related records.

      :param object_id: Identifikátor objektu ``object``.

   .. py:method:: delete_history_records()

      Odstraní history records.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param object_id: Identifikátor objektu ``object``.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: delete_model()

      Odstraní model. v aplikaci.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Vstupní hodnota ``obj`` pro danou operaci.


.. py:class:: CustomGroupAdmin

   Admin panel pro správu uživatelskych skupin.

   **Metody:**

   .. py:method:: has_delete_permission()

      Určí, zda delete permission.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param obj: Vstupní hodnota ``obj`` pro danou operaci.


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

      :param request: Django HTTP požadavek.
      :param obj: Upravovaný záznam logu notifikace.
      :return: Seznam názvů polí určených pouze ke čtení.

   .. py:method:: has_add_permission()

      Zakáže ruční vytváření záznamů v administraci.

      :param request: Django HTTP požadavek.
      :return: Vždy ``False``.

   .. py:method:: has_delete_permission()

      Zakáže mazání záznamů logu notifikací.

      :param request: Django HTTP požadavek.
      :param obj: Vybraný záznam logu notifikace.
      :return: Vždy ``False``.

   .. py:method:: get_urls()

      Přidá vlastní URL pro odeslání testovacího emailu z administrace.

      :return: Seznam URL vzorů pro tento admin.

   .. py:method:: test_email_view()

      Zobrazí a zpracuje formulář pro odeslání testovacího emailu.

      :param request: Django HTTP požadavek.
      :return: Odpověď s formulářem a výsledkem odeslání.

