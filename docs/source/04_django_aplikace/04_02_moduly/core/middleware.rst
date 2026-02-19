CORE middleware
===============

Modul middleware.

Třídy
------

.. py:class:: PermissionMiddleware

   Middleware třída užívaná pro kontrolu oprávnení.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: __call__()

   .. py:method:: process_view()

      Metoda pro kontrolu oprvávnení pro každý view.


.. py:class:: ErrorMiddleware

   Popis není k dispozici.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: __call__()

   .. py:method:: process_exception()


.. py:class:: StatusMessageMiddleware

   Popis není k dispozici.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: __call__()

   .. py:method:: _show_message()

   .. py:method:: process_view()

