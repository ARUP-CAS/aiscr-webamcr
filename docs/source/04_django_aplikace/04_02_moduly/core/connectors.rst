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

      :return: Nově vytvořená hodnota připravená touto funkcí.

   .. py:method:: _create_connection_decode()

      Vytvoří connection decode.

      :return: Nově vytvořená hodnota připravená touto funkcí.

   .. py:method:: get_connection()

      Vrací connection. v aplikaci.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: get_connection_decode()

      Vrací connection decode.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: prepare_model_for_redis()

      Převede řádek Django-tables2 tabulky do slovníku pro uložení do Redis cache.

      :param table: Tabulka (django-tables2) obsahující jeden řádek s daty záznamu.

      :return: Vrací proměnná ``data``.


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

      :param buff: Binární stream (``BytesIO``) se souborem určeným ke kontrole.
      :return: Slovník ve formátu ``{filename: (status, reason)}`` pro odpověď clamd.
      :raises ClamdBufferTooLongError: Pokud je stream větší než povolený limit clamd.
      :raises ClamdConnectionError: Při chybě komunikace se službou clamd.

   .. py:method:: _basic_command()

      Odešle jednoduchý příkaz do clamd a vrátí jeho odpověď.

      :param command: Název příkazu zasílaného do clamd démona (např. 'PING', 'VERSION').

      :return: Výstup funkce odpovídající implementované logice.

      :raises ClamdResponseError: Vyvolá se při splnění podmínky ``len(response) > 1``.

   .. py:method:: _init_socket()

      Inicializuje socketové připojení k clamd.

      Pouze pro interní použití.
      :raises ClamdConnectionError: Pokud se nelze připojit ke clamd.

   .. py:method:: _error_message()

      Formátuje chybovou zprávu pro selhání socketového připojení.
      :param exception: Zachycená síťová výjimka při navazování spojení.
      :return: Formátovaná chybová zpráva pro logování.

   .. py:method:: _send_command()

      Odešle command.

      Používá prefix 'n' a ukončovač nového řádku podle doporučení `man clamd`.

      :param cmd: Textový název, klíč nebo zpráva ``cmd`` používaná v rámci operace.
      :param args: Parametr ``args`` se předává do volání ``join()``, ovlivňuje větvení podmínek.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _recv_response()

      Přijme jednořádkovou odpověď od clamd.
      :return: Dekódovaný řádek odpovědi od clamd.
      :raises ClamdConnectionError: Při chybě čtení ze socketu.

   .. py:method:: _parse_response()

      Parsuje odpovědi pro příkazy SCAN, CONTSCAN, MULTISCAN a STREAM.
      :param msg: Textová odpověď vrácená službou clamd.
      :return: N-tice ``(path, virus, status)`` extrahovaná z odpovědi.
      :raises ClamdResponseError: Pokud odpověď nelze naparsovat.

   .. py:method:: _close_socket()

      Uzavře socketové připojení k clamd.

