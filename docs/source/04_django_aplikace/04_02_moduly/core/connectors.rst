CORE connectors
===============

Modul connectors.

Třídy
------

.. py:class:: RedisConnector

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_connection()

   .. py:method:: get_connection_decode()

   .. py:method:: prepare_model_for_redis()


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
      
      Args:
          buff: instance BytesIO se soubory ke skenování
      
      Returns:
          dict: {filename: (status, reason)} kde status je 'FOUND' nebo 'OK'
      
      Raises:
          ClamdBufferTooLongError: pokud velikost bufferu překročí limity clamd
          ClamdConnectionError: při problému s komunikací
