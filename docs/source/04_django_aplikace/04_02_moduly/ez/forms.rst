EZ formuláře
============

Definice formulářů.

Třídy
------

.. py:class:: ExterniZdrojForm

   Hlavní formulář pro vytvoření, editaci a zobrazení externího zdroju.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param required: Příznak ``required`` určující průběh nebo rozsah zpracování.
      :param required_next: Příznak ``required_next`` určující průběh nebo rozsah zpracování.
      :param readonly: Příznak ``readonly`` určující průběh nebo rozsah zpracování.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: ExterniOdkazForm

   Hlavní formulář pro vytvoření, editaci externího odkazu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param type_arch: Název nebo typ ``type_arch`` používaný pro volbu cílové logiky.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: PripojitArchZaznamForm

   Hlavní formulář pro připojení archeologického záznamu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param type_arch: Název nebo typ ``type_arch`` používaný pro volbu cílové logiky.
      :param dok: Doménový objekt `dok`, se kterým funkce pracuje.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: PripojitExterniOdkazForm

   Hlavní formulář pro připojení externího zdroju.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

