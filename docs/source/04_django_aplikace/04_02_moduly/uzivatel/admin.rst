UZIVATEL admin
==============

Konfigurace Django admin.

Třídy
------

.. py:class:: UserNotificationTypeInlineForm

   Inline form pro nastavení notifikací uživatele.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: UserNotificationTypeInlineFormset

   Popis není k dispozici.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: UserNotificationTypeInline

   Inline panel pro nastavení notifikací uživatele.

   **Metody:**

   .. py:method:: get_queryset()

   .. py:method:: get_extra()

   .. py:method:: __init__()


.. py:class:: PesNotificationTypeInline

   Inline panel pro nastavení hlídacích psů uživatele.

   **Metody:**

   .. py:method:: get_queryset()


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


.. py:class:: PesUserNotificationTypeInlineFormset

   Popis není k dispozici.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: PesUserNotificationTypeInline

   Inline panel pro nastavení notifikací uživatele.

   **Metody:**

   .. py:method:: get_queryset()

   .. py:method:: get_extra()


.. py:class:: CustomUserAdmin

   Admin panel pro správu uživatele.

   **Metody:**

   .. py:method:: has_delete_permission()

   .. py:method:: save_model()

   .. py:method:: user_change_password()

   .. py:method:: log_deletion()

   .. py:method:: get_readonly_fields()

   .. py:method:: render_change_form()

   .. py:method:: get_urls()

   .. py:method:: get_histore_related_records()

   .. py:method:: delete_history_records()

   .. py:method:: delete_model()


.. py:class:: CustomGroupAdmin

   Admin panel pro správu uživatelskych skupin.

   **Metody:**

   .. py:method:: has_delete_permission()


.. py:class:: NotificationsLogAdmin

   Admin panel pro kontrolu odeslaných mailů s možností poslat testovací mail.

   **Metody:**

   .. py:method:: created()

   .. py:method:: status_colored()

   .. py:method:: get_readonly_fields()

   .. py:method:: has_add_permission()

   .. py:method:: has_change_permission()

   .. py:method:: has_delete_permission()

   .. py:method:: has_view_permission()

   .. py:method:: get_urls()

   .. py:method:: test_email_view()

