PID exceptions
==============

Modul exceptions.

Třídy
------

.. py:class:: DoiNoTransactionError

   Implementuje komponentu ``DoiNoTransactionError`` v rámci aplikace.


.. py:class:: DoiWriteError

   Implementuje komponentu ``DoiWriteError`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``status_code``: HTTP stavový kód odpovědi z DataCite API.
      - ``response_text``: Textový obsah chybové odpovědi z DataCite API.
      - ``request_url``: URL adresa požadavku, který skončil chybou.



.. py:class:: DoiConnectionError

   Implementuje komponentu ``DoiConnectionError`` v rámci aplikace.

