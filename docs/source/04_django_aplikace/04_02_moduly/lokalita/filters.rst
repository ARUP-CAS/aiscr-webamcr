LOKALITA filtry
===============

Definice filtrů.

Třídy
------

.. py:class:: LokalitaFilter

   Třída pro zakladní filtrování lokality a jejich potomků.

   **Metody:**

   .. py:method:: filter_queryset()

      Filtruje queryset. v aplikaci.

      :param queryset: Vstupní queryset, který má být dále zpracován.

   .. py:method:: filter_popisne_udaje()

      Metoda pro filtrování podle názvu, popisu, uživatelského označení a poznámek.

      :param queryset: Vstupní queryset, který má být dále zpracován.
      :param name: Název nebo identifikátor používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: LokalitaFilterFormHelper

   Třída pro správně zobrazení filtru.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param form: Formulářová instance zpracovávaná funkcí.

