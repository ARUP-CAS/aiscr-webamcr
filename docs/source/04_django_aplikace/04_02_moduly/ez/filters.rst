EZ filtry
=========

Definice filtrů.

Třídy
------

.. py:class:: ExterniZdrojFilter

   Třída pro zakladní filtrování externího zdroju a jejich potomků.

   **Metody:**

   .. py:method:: filter_queryset()

      Filtruje queryset.

      :param queryset: Vstupní hodnota ``queryset`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: filter_popisne_udaje()

      Metoda pro filtrování podle názvu, edice, sborníku, časopisu, isbn, issn, roku vydání a poznámek.

   .. py:method:: filter_akce_ident()

      Metoda pro filtrování podle identu celý akce.

   .. py:method:: filter_lokalita_ident()

      Metoda pro filtrování podle identu celý lokality.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).


.. py:class:: ExterniZdrojFilterFormHelper

   Třída pro správně zobrazení filtru.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param form: Vstupní hodnota ``form`` pro danou operaci.
      :return: Funkce nevrací hodnotu (``None``).

