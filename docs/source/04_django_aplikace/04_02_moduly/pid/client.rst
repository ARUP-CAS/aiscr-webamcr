PID client
==========

Modul client.

Třídy
------

.. py:class:: DigitalObjectIdentifierClient

   Zapouzdřuje CRUD operace nad DOI/IGSN záznamy v DataCite.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje klienta podle typu předaného doménového záznamu.

   .. py:method:: _check_response_status()

      Ověří response status.

      :param response: Vstupní hodnota ``response`` pro danou operaci.
      :return: Vrací výsledek ověření nebo validačního pravidla.

   .. py:method:: get_record_url()

      Vrátí URL detailu záznamu v DataCite.

   .. py:method:: check_record_exists()

      Zjistí, zda záznam v DataCite existuje.

   .. py:method:: delete_record()

      Skryje/smaže záznam v DataCite podle serializovaného payloadu.

   .. py:method:: hide_record()

      Provádí operaci hide record.

      :param check_status: Vstupní hodnota ``check_status`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: publish_record()

      Publikuje záznam v DataCite, případně jej nejdříve vytvoří.

   .. py:method:: update_record()

      Aktualizuje record.

      :param check_status: Vstupní hodnota ``check_status`` pro danou operaci.
      :param reload_record: Vstupní hodnota ``reload_record`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

