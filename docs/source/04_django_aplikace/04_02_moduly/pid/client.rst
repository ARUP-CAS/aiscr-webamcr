PID client
==========

Modul client.

Přehled modulu
--------------

Klient pro komunikaci s DataCite API při správě DOI/IGSN identifikátorů.

Třídy
------

.. py:class:: DigitalObjectIdentifierClient

   Zapouzdřuje CRUD operace nad DOI/IGSN záznamy v DataCite.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje klienta podle typu předaného doménového záznamu.

      :param record: Parametr ``record`` předává se do volání ``type()``.
      :raises ValueError: Vyvolá se při splnění podmínky ``record_type in self.record_serializer_map``.

   .. py:method:: _check_response_status()

      Ověří response status.

      :param response: Textový nebo strukturální vstup `response` používaný při sestavení nebo zpracování obsahu.
      :return: Vrací výsledek ověření nebo validačního pravidla.

      :raises DoiWriteError: Vyvolá se při splnění podmínky ``not str(response.status_code).startswith('2')``.

   .. py:method:: get_record_url()

      Vrátí URL detailu záznamu v DataCite.

      :return: Vrací hodnotu podle větve zpracování.

   .. py:method:: check_record_exists()

      Zjistí, zda záznam v DataCite existuje.

      :param check_status: Parametr ``check_status`` ovlivňuje větvení podmínek.

      :return: Vrací výsledek volání ``startswith()``.
      :raises DoiConnectionError: Vyvolá se při splnění podmínky ``str(response.status_code).startswith('5') and check_status``.

   .. py:method:: delete_record()

      Skryje/smaže záznam v DataCite podle serializovaného payloadu.

      :param check_status: Parametr ``check_status`` předává se do volání ``check_record_exists()``, ovlivňuje větvení podmínek.

      :return: Vrací výsledek volání ``json()``.
      :raises DoiNoTransactionError: Vyvolá se při splnění podmínky ``not isinstance(self.record, Lokalita) and (not hasattr(self.record, 'active_transaction'))``.

   .. py:method:: hide_record()

      Skryje existující záznam v DataCite pomocí serializovaného payloadu pro skrytí.

      :param check_status: Příznak, zda má být ověřena existence záznamu a zkontrolován stavový kód odpovědi.

      :return: Vrací výsledek volání ``json()``.
      :raises DoiNoTransactionError: Vyvolá se při splnění podmínky ``not isinstance(self.record, Lokalita) and (not hasattr(self.record, 'active_transaction'))``.

   .. py:method:: publish_record()

      Publikuje záznam v DataCite, případně jej nejdříve vytvoří.

      :param check_status: Parametr ``check_status`` předává se do volání ``check_record_exists()``, ovlivňuje větvení podmínek.

      :return: Vrací výsledek volání ``json()``.
      :raises DoiNoTransactionError: Vyvolá se při splnění podmínky ``not isinstance(self.record, Lokalita) and (not hasattr(self.record, 'active_transaction'))``.

   .. py:method:: update_record()

      Aktualizuje record. v aplikaci.

      :param check_status: Parametr ``check_status`` předává se do volání ``check_record_exists()``, ovlivňuje větvení podmínek.
      :param reload_record: Parametr ``reload_record`` ovlivňuje větvení podmínek.

      :return: Vrací výsledek volání ``json()``.

