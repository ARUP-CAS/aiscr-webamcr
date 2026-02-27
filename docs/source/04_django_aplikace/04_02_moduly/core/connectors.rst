CORE connectors
===============

Modul connectors.

Třídy
------

.. py:class:: RedisConnector

   Implementuje komponentu ``RedisConnector`` v rámci aplikace.

   **Metody:**

   .. py:method:: _create_connection()

      Vytvoří connection.

      :return: Vrací nově vytvořený výsledek operace.

   .. py:method:: _create_connection_decode()

      Vytvoří connection decode.

      :return: Vrací nově vytvořený výsledek operace.

   .. py:method:: get_connection()

      Vrací connection.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_connection_decode()

      Vrací connection decode.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: prepare_model_for_redis()

      Provádí operaci prepare model for redis.

      :param table: Vstupní hodnota ``table`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: ClamdError

   Základní třída výjimek pro chyby clamd.


.. py:class:: ClamdResponseError

   Výjimka vyvolaná při neočekávané odpovědi od clamd.


.. py:class:: ClamdBufferTooLongError

   Výjimka vyvolaná při překročení délky bufferu nad StreamMaxLength v clamd.conf.


.. py:class:: ClamdConnectionError

   Výjimka vyvolaná při chybách komunikace s clamd.


.. py:class:: ClamdNetworkSocket

   Třída pro komunikaci s ClamAV démonem přes síťový socket.

   Tato třída poskytuje metody pro skenování souborů na viry
   pomocí ClamAV démona naslouchajícího na TCP portu.

   **Metody:**

   .. py:method:: __init__()

      Inicializace třídy.

      Hodnoty host, port a timeout se načítají z nastavení aplikace.

   .. py:method:: instream()

      Skenuje buffer na přítomnost virů.


      **Argumenty:**

      - ``buff``: instance BytesIO se soubory ke skenování

      **Návratová hodnota:**

      *dict*: {filename: (status, reason)} kde status je 'FOUND' nebo 'OK'

      **Výjimky:**

      *ClamdBufferTooLongError*: pokud velikost bufferu překročí limity clamd
      *ClamdConnectionError*: při problému s komunikací

   .. py:method:: _basic_command()

      Provádí operaci basic command.

      :param command: Vstupní hodnota ``command`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: _init_socket()

      Inicializuje socketové připojení k clamd.

      Pouze pro interní použití.


      **Výjimky:**

      *ClamdConnectionError*: pokud se nelze připojit k clamd

   .. py:method:: _error_message()

      Formátuje chybovou zprávu pro selhání socketového připojení.


      **Argumenty:**

      - ``exception``: výjimka socket.error

      **Návratová hodnota:**

      *str*: formátovaná chybová zpráva

   .. py:method:: _send_command()

      Odešle command.

      :param cmd: Vstupní hodnota ``cmd`` pro danou operaci.
      :param args: Dodatečné poziční argumenty předané voláním.
      :return: Vrací výsledek provedené operace.

   .. py:method:: _recv_response()

      Přijme jednořádkovou odpověď od clamd.


      **Návratová hodnota:**

      *str*: dekódovaný a oříznutý řádek odpovědi

      **Výjimky:**

      *ClamdConnectionError*: při chybě čtení ze socketu

   .. py:method:: _parse_response()

      Parsuje odpovědi pro příkazy SCAN, CONTSCAN, MULTISCAN a STREAM.


      **Argumenty:**

      - ``msg`` (*str*): zpráva odpovědi od clamd

      **Návratová hodnota:**

      *tuple*: (path, virus, status)

      **Výjimky:**

      *ClamdResponseError*: pokud nelze odpověď parsovat

   .. py:method:: _close_socket()

      Uzavře socketové připojení k clamd.

