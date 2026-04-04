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

      **Parametry:**

      - ``obj``: Parametr ``obj`` pracuje se s atributy ``ident_cely``, ``vedouci_projektu``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování.



.. py:class:: PotvrditNalezForm

   Hlavní formulář pro potvrzení nálezu lokality.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``readonly``: Parametr ``readonly`` slouží jako vstup pro logiku funkce ``__init__``.
      - ``predano_required``: Parametr ``predano_required`` slouží jako vstup pro logiku funkce ``__init__``.
      - ``predano_hidden``: Parametr ``predano_hidden`` ovlivňuje větvení podmínek.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.



.. py:class:: CreateSamostatnyNalezForm

   Hlavní formulář pro vytvoření, editaci a zobrazení samostatnýho nálezu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``readonly``: Parametr ``readonly`` ovlivňuje větvení podmínek.
      - ``user``: Parametr ``user`` se předává do volání ``ProjectModelChoiceField()``, ``filter()``, pracuje se s atributy ``moje_spolupracujici_organizace``, ``moje_stavy_pruzkumnych_projektu``.
      - ``required``: Parametr ``required`` ovlivňuje větvení podmínek.
      - ``required_next``: Parametr ``required_next`` slouží jako vstup pro logiku funkce ``__init__``.
      - ``project_ident``: Identifikátor ``project_ident`` používaný pro dohledání cílového záznamu.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``, pracuje se s atributy ``pop``.



.. py:class:: CreateZadostForm

   Hlavní formulář pro vytvoření, editaci a zobrazení žádosti o spoluprácu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.



.. py:class:: PasFilterForm

   Implementuje komponentu ``PasFilterForm`` v rámci aplikace.


.. py:class:: DeaktivovatSpolupraciForm

   Formulář pro deaktivaci záznamu. Obsahuje jen text pole pro zdůvodnění deaktivace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.



Funkce
------

.. py:function:: validate_uzivatel_email(email)

   Funkce pro validaci zadaného emailu uživatele.

   **Parametry:**

   - ``email``: Uživatel nebo osoba ``email``, v jejímž kontextu se operace provádí.

   **Výjimky:**

   - ``ValidationError``: Vyvolá se při splnění podmínky ``not user.exists()``; nebo při splnění podmínky ``user[0].hlavni_role not in Group.objects.filter(id__in=(ROLE_ARCHEOLOG_ID, ROLE_ADMIN_ID, ROLE_ARCHIVAR_ID))``.

