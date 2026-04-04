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

      **Návratová hodnota:**

      Nově vytvořená hodnota připravená touto funkcí.


   .. py:method:: _create_connection_decode()

      Vytvoří connection decode.

      **Návratová hodnota:**

      Nově vytvořená hodnota připravená touto funkcí.


   .. py:method:: get_connection()

      Vrací connection. v aplikaci.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: get_connection_decode()

      Vrací connection decode.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: prepare_model_for_redis()

      Převede řádek Django-tables2 tabulky do slovníku pro uložení do Redis cache.

      **Parametry:**

      - ``table``: Tabulka (django-tables2) obsahující jeden řádek s daty záznamu.

      **Návratová hodnota:**

      Vrací proměnná ``data``.



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

      **Parametry:**

      - ``buff``: Binární stream (``BytesIO``) se souborem určeným ke kontrole.

      **Návratová hodnota:**

      Slovník ve formátu ``{filename: (status, reason)}`` pro odpověď clamd.

      **Výjimky:**

      - ``ClamdBufferTooLongError``: Pokud je stream větší než povolený limit clamd.
      - ``ClamdConnectionError``: Při chybě komunikace se službou clamd.


   .. py:method:: _basic_command()

      Odešle jednoduchý příkaz do clamd a vrátí jeho odpověď.

      **Parametry:**

      - ``command``: Název příkazu zasílaného do clamd démona (např. 'PING', 'VERSION').

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice.

      **Výjimky:**

      - ``ClamdResponseError``: Vyvolá se při splnění podmínky ``len(response) > 1``.


   .. py:method:: _init_socket()

      Inicializuje socketové připojení k clamd.

      Pouze pro interní použití.

      **Výjimky:**

      - ``ClamdConnectionError``: Pokud se nelze připojit ke clamd.


   .. py:method:: _error_message()

      Formátuje chybovou zprávu pro selhání socketového připojení.

      **Parametry:**

      - ``exception``: Zachycená síťová výjimka při navazování spojení.

      **Návratová hodnota:**

      Formátovaná chybová zpráva pro logování.


   .. py:method:: _send_command()

      Odešle command.

      Používá prefix 'n' a ukončovač nového řádku podle doporučení `man clamd`.

      **Parametry:**

      - ``cmd``: Textový název, klíč nebo zpráva ``cmd`` používaná v rámci operace.
      - ``args``: Parametr ``args`` se předává do volání ``join()``, ovlivňuje větvení podmínek.

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice.


   .. py:method:: _recv_response()

      Přijme jednořádkovou odpověď od clamd.

      **Návratová hodnota:**

      Dekódovaný řádek odpovědi od clamd.

      **Výjimky:**

      - ``ClamdConnectionError``: Při chybě čtení ze socketu.


   .. py:method:: _parse_response()

      Parsuje odpovědi pro příkazy SCAN, CONTSCAN, MULTISCAN a STREAM.

      **Parametry:**

      - ``msg``: Textová odpověď vrácená službou clamd.

      **Návratová hodnota:**

      N-tice ``(path, virus, status)`` extrahovaná z odpovědi.

      **Výjimky:**

      - ``ClamdResponseError``: Pokud odpověď nelze naparsovat.


   .. py:method:: _close_socket()

      Uzavře socketové připojení k clamd.

