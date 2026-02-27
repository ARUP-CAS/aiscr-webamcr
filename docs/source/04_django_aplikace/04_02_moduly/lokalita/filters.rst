LOKALITA filtry
===============

Definice filtrů.

Třídy
------

.. py:class:: LokalitaFilter

   Třída pro zakladní filtrování lokality a jejich potomků.

   **Metody:**

   .. py:method:: filter_queryset()

      Filtruje queryset.

      :param queryset: Vstupní hodnota ``queryset`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: filter_popisne_udaje()

      Metoda pro filtrování podle názvu, popisu, uživatelského označení a poznámek.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).


.. py:class:: LokalitaFilterFormHelper

   Třída pro správně zobrazení filtru.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param form: Vstupní hodnota ``form`` pro danou operaci.
      :return: Funkce nevrací hodnotu (``None``).

