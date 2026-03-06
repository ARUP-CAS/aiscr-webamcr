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

      :param status_code: Stavová nebo časová hodnota `status_code` používaná při rozhodování logiky.
      :param response_text: Číselná hodnota ``response_text`` použitá při výpočtu nebo transformaci.
      :param request_url: Parametr ``request_url`` slouží jako vstup pro logiku funkce ``__init__``.


.. py:class:: DoiConnectionError

   Implementuje komponentu ``DoiConnectionError`` v rámci aplikace.

