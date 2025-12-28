PAS formuláře
=============

Definice formulářů.

Třídy
------

.. py:class:: ProjectModelChoiceField

   Třída pro správně zobrazení label.

   **Metody:**

   .. py:method:: label_from_instance()


.. py:class:: PotvrditNalezForm

   Hlavní formulář pro potvrzení nálezu lokality.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: CreateSamostatnyNalezForm

   Hlavní formulář pro vytvoření, editaci a zobrazení samostatnýho nálezu.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: CreateZadostForm

   Hlavní formulář pro vytvoření, editaci a zobrazení žádosti o spoluprácu.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: PasFilterForm

   Popis není k dispozici.


.. py:class:: DeaktivovatSpolupraciForm

   Formulář pro deaktivaci záznamu. Obsahuje jen text pole pro zdůvodnění deaktivace.

   **Metody:**

   .. py:method:: __init__()


Funkce
------

.. py:function:: validate_uzivatel_email(email)

   Funkce pro validaci zadaného emailu uživatele.
