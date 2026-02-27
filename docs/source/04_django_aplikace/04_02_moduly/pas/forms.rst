PAS formuláře
=============

Definice formulářů.

Třídy
------

.. py:class:: ProjectModelChoiceField

   Třída pro správně zobrazení label.

   **Metody:**

   .. py:method:: label_from_instance()

      Provádí operaci label from instance.

      :param obj: Vstupní hodnota ``obj`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: PotvrditNalezForm

   Hlavní formulář pro potvrzení nálezu lokality.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param readonly: Vstupní hodnota ``readonly`` pro danou operaci.
      :param predano_required: Vstupní hodnota ``predano_required`` pro danou operaci.
      :param predano_hidden: Vstupní hodnota ``predano_hidden`` pro danou operaci.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).


.. py:class:: CreateSamostatnyNalezForm

   Hlavní formulář pro vytvoření, editaci a zobrazení samostatnýho nálezu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param readonly: Vstupní hodnota ``readonly`` pro danou operaci.
      :param user: Vstupní hodnota ``user`` pro danou operaci.
      :param required: Vstupní hodnota ``required`` pro danou operaci.
      :param required_next: Vstupní hodnota ``required_next`` pro danou operaci.
      :param project_ident: Vstupní hodnota ``project_ident`` pro danou operaci.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).


.. py:class:: CreateZadostForm

   Hlavní formulář pro vytvoření, editaci a zobrazení žádosti o spoluprácu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).


.. py:class:: PasFilterForm

   Implementuje komponentu ``PasFilterForm`` v rámci aplikace.


.. py:class:: DeaktivovatSpolupraciForm

   Formulář pro deaktivaci záznamu. Obsahuje jen text pole pro zdůvodnění deaktivace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).


Funkce
------

.. py:function:: validate_uzivatel_email(email)

   Funkce pro validaci zadaného emailu uživatele.
