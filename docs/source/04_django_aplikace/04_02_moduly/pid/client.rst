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

      Ověří úspěšnost HTTP odpovědi a při chybě vyvolá doménovou výjimku.

   .. py:method:: get_record_url()

      Vrátí URL detailu záznamu v DataCite.

   .. py:method:: check_record_exists()

      Zjistí, zda záznam v DataCite existuje.

   .. py:method:: delete_record()

      Skryje/smaže záznam v DataCite podle serializovaného payloadu.

   .. py:method:: hide_record()

      Nastaví záznam v DataCite do neveřejného režimu.

   .. py:method:: publish_record()

      Publikuje záznam v DataCite, případně jej nejdříve vytvoří.

   .. py:method:: update_record()

      Aktualizuje existující záznam v DataCite.

