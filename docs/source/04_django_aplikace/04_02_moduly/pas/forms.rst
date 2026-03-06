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

      :param obj: Objekt, se kterým funkce pracuje.


.. py:class:: PotvrditNalezForm

   Hlavní formulář pro potvrzení nálezu lokality.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param readonly: Příznak ``readonly`` určující průběh nebo rozsah zpracování.
      :param predano_required: Číselná nebo geometrická hodnota `predano_required` použitá při výpočtu nebo transformaci.
      :param predano_hidden: Číselná nebo geometrická hodnota `predano_hidden` použitá při výpočtu nebo transformaci.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: CreateSamostatnyNalezForm

   Hlavní formulář pro vytvoření, editaci a zobrazení samostatnýho nálezu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param readonly: Příznak ``readonly`` určující průběh nebo rozsah zpracování.
      :param user: Uživatel, v jehož kontextu se operace provádí.
      :param required: Příznak ``required`` určující průběh nebo rozsah zpracování.
      :param required_next: Příznak ``required_next`` určující průběh nebo rozsah zpracování.
      :param project_ident: Identifikátor ``project_ident`` používaný pro dohledání cílového záznamu.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: CreateZadostForm

   Hlavní formulář pro vytvoření, editaci a zobrazení žádosti o spoluprácu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: PasFilterForm

   Implementuje komponentu ``PasFilterForm`` v rámci aplikace.


.. py:class:: DeaktivovatSpolupraciForm

   Formulář pro deaktivaci záznamu. Obsahuje jen text pole pro zdůvodnění deaktivace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


Funkce
------

.. py:function:: validate_uzivatel_email(email)

   Funkce pro validaci zadaného emailu uživatele.

   :param email: Uživatel nebo osoba ``email``, v jejímž kontextu se operace provádí.
