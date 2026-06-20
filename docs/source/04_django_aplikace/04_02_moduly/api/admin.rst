API admin
=========

Konfigurace Django admin.

Třídy
------

.. py:class:: ApiRequestLogAdmin

   Třída admin panelu pro zobrazení logů API požadavků.

   **Metody:**

   .. py:method:: _format_datetime()

      Naformátuje datetime jako ``RRRR-MM-DD HH:MM:SS.xx`` (setiny sekundy).

   .. py:method:: received_at_display()

      Vrátí ``received_at`` ve formátu ``RRRR-MM-DD HH:MM:SS.xx``.

      :param obj: Záznam ``ApiRequestLog``, jehož ``received_at`` se formátuje.

      :return: Naformátovaný řetězec datumu a času, nebo prázdný řetězec při ``None``.

   .. py:method:: finished_at_display()

      Vrátí ``finished_at`` ve formátu ``RRRR-MM-DD HH:MM:SS.xx``.

      :param obj: Záznam ``ApiRequestLog``, jehož ``finished_at`` se formátuje.

      :return: Naformátovaný řetězec datumu a času, nebo prázdný řetězec při ``None``.

   .. py:method:: has_add_permission()

      Zakáže ruční vytváření záznamů — logy se vytvářejí pouze automaticky.

      :param request: HTTP požadavek od klienta.

      :return: Vždy ``False``.

   .. py:method:: has_change_permission()

      Zakáže editaci záznamů — logy jsou pouze pro čtení.

      :param request: HTTP požadavek od klienta.
      :param obj: Volitelný objekt záznamu.

      :return: Vždy ``False``.

   .. py:method:: has_delete_permission()

      Zakáže mazání záznamů — logy jsou auditní záznamy určené k archivaci.

      :param request: HTTP požadavek od klienta.
      :param obj: Volitelný objekt záznamu.

      :return: Vždy ``False``.

