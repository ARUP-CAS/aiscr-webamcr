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
      :param required: Vstupní hodnota ``required`` pro danou operaci.
      :param required_next: Vstupní hodnota ``required_next`` pro danou operaci.
      :param readonly: Vstupní hodnota ``readonly`` pro danou operaci.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: ExterniOdkazForm

   Hlavní formulář pro vytvoření, editaci externího odkazu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param type_arch: Vstupní hodnota ``type_arch`` pro danou operaci.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: PripojitArchZaznamForm

   Hlavní formulář pro připojení archeologického záznamu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param type_arch: Vstupní hodnota ``type_arch`` pro danou operaci.
      :param dok: Vstupní hodnota ``dok`` pro danou operaci.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: PripojitExterniOdkazForm

   Hlavní formulář pro připojení externího zdroju.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

