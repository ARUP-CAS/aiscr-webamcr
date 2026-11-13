NOTIFIKACE_PROJEKTY tests
=========================

Modul tests.

Přehled modulu
--------------

Explicitní testy notifikační úlohy s vlastními referenčními daty.

Třídy
------

.. py:class:: ProjectNotificationTaskTest

   Ověřuje skutečný výběr příjemců a dispatch; pouze doručení emailu je mockováno.

   **Metody:**

   .. py:method:: setUpTestData()

      Připraví projekt, hlídacího psa a oba typy notifikací nutné pro úlohu.

   .. py:method:: setUp()

      Naváže ID projektu z fixture na skutečné mapování typu notifikace.

   .. py:method:: test_explicit_task_selects_subscribed_watchdog_and_calls_mailer()

      Přímý běh úlohy vybere přihlášeného archeologa pro katastr projektu.

   .. py:method:: test_explicit_task_does_not_send_without_project_type_subscription()

      Úloha bez odběratele konkrétního typu projektu mailer vůbec nevolá.

   .. py:method:: test_new_project_dispatches_task_with_saved_primary_key()

      Signál nového projektu předává do delay primární klíč uloženého záznamu.

