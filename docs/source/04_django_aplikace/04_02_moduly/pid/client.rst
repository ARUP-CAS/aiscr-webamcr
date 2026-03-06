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

      :param response: Textový nebo strukturální vstup `response` používaný při sestavení nebo zpracování obsahu.
      :return: Vrací výsledek ověření nebo validačního pravidla.

   .. py:method:: get_record_url()

      Vrátí URL detailu záznamu v DataCite.

   .. py:method:: check_record_exists()

      Zjistí, zda záznam v DataCite existuje.

      :param check_status: Příznak ``check_status`` určující průběh nebo rozsah zpracování.

   .. py:method:: delete_record()

      Skryje/smaže záznam v DataCite podle serializovaného payloadu.

      :param check_status: Příznak ``check_status`` určující průběh nebo rozsah zpracování.

   .. py:method:: hide_record()

      Provádí operaci hide record.

      :param check_status: Příznak ``check_status`` určující průběh nebo rozsah zpracování.

   .. py:method:: publish_record()

      Publikuje záznam v DataCite, případně jej nejdříve vytvoří.

      :param check_status: Příznak ``check_status`` určující průběh nebo rozsah zpracování.

   .. py:method:: update_record()

      Aktualizuje record. v aplikaci.

      :param check_status: Příznak ``check_status`` určující průběh nebo rozsah zpracování.
      :param reload_record: Záznam/objekt ``reload_record``, který funkce čte, validuje nebo upravuje.

