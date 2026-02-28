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

      :param status_code: Vstupní hodnota ``status_code`` pro danou operaci.
      :param response_text: Vstupní hodnota ``response_text`` pro danou operaci.
      :param request_url: Vstupní hodnota ``request_url`` pro danou operaci.


.. py:class:: DoiConnectionError

   Implementuje komponentu ``DoiConnectionError`` v rámci aplikace.

