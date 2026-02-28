EZ filtry
=========

Definice filtrů.

Třídy
------

.. py:class:: ExterniZdrojFilter

   Třída pro zakladní filtrování externího zdroju a jejich potomků.

   **Metody:**

   .. py:method:: filter_queryset()

      Filtruje queryset. v aplikaci.

      :param queryset: Vstupní hodnota ``queryset`` pro danou operaci.

   .. py:method:: filter_popisne_udaje()

      Metoda pro filtrování podle názvu, edice, sborníku, časopisu, isbn, issn, roku vydání a poznámek.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: filter_akce_ident()

      Metoda pro filtrování podle identu celý akce.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: filter_lokalita_ident()

      Metoda pro filtrování podle identu celý lokality.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: ExterniZdrojFilterFormHelper

   Třída pro správně zobrazení filtru.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param form: Vstupní hodnota ``form`` pro danou operaci.

