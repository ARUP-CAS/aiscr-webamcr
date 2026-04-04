DOKUMENT filtry
===============

Definice filtrů.

Třídy
------

.. py:class:: SouborTypFilter

   Implementuje komponentu ``SouborTypFilter`` v rámci aplikace.

   **Metody:**

   .. py:method:: field()

      Vrací dynamicky generované pole s volbami typů souborů z aktuální databáze.

      **Návratová hodnota:**

      FormField s volbami z databáze.



.. py:class:: HistorieFilter

   Třída pro základní filtrování historie. Třída je děděná v jednotlivých filtracích záznamů.

   **Metody:**

   .. py:method:: set_filter_fields()

      Nastaví filter fields.

      **Parametry:**

      - ``user``: Parametr ``user`` pracuje se s atributy ``hlavni_role``, ovlivňuje větvení podmínek.


   .. py:method:: _get_history_subquery()

      Vrací history subquery.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: filter_ident_cely()

      Metoda pro filtrování podle identu dokumentu/projektu/EZ, ale i dočasného.

      **Parametry:**

      - ``queryset``: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      - ``name``: Parametr ``name`` nepoužito.
      - ``value``: Parametr ``value`` ovlivňuje větvení podmínek, předává se do volání ``filter()``.

      **Návratová hodnota:**

      Vrací filtrovaný ``queryset`` podle ``ident_cely`` nebo poznámky z historie.



.. py:class:: Model3DFilter

   Třída pro základní filtrování modelu 3D a jejich potomků.

   **Metody:**

   .. py:method:: filter_queryset()

      Filtruje queryset. v aplikaci.

      **Parametry:**

      - ``queryset``: Parametr ``queryset`` předává se do volání ``filter_queryset()``, pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací proměnná ``queryset``.


   .. py:method:: filter_popisne_udaje()

      Filtruje modely 3D podle popisu, poznámky, odkazu a textů v komponentách.

      **Parametry:**

      - ``queryset``: QuerySet modelů 3D k filtrování.
      - ``name``: Jméno pole pro filtrování.
      - ``value``: Hodnota pro vyhledávání.

      **Návratová hodnota:**

      Filtrovaný QuerySet.


   .. py:method:: filter_roky()

      Filtruje modely podle roku vzniku.

      **Parametry:**

      - ``queryset``: QuerySet modelů k filtrování.
      - ``name``: Jméno pole pro filtrování.
      - ``value``: RangeField s start/stop roky.

      **Návratová hodnota:**

      Filtrovaný QuerySet.


   .. py:method:: filter_roky_range()

      Filtruje modely podle rozsahu let.

      **Parametry:**

      - ``queryset``: QuerySet modelů k filtrování.
      - ``name``: Jméno pole pro filtrování (tuple name).
      - ``value``: RangeField s start/stop roky.

      **Návratová hodnota:**

      Filtrovaný QuerySet.


   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``, pracuje se s atributy ``get``.



.. py:class:: Model3DFilterFormHelper

   Třída pro správně zobrazení filtru.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``form``: Parametr ``form`` se předává do volání ``__init__()``.



.. py:class:: DokumentFilter

   Třída pro základní filtrování dokumentu a jejich potomků.

   **Metody:**

   .. py:method:: filter_uzemni_prislusnost()

      Filtruje dokumenty podle územní příslušnosti.

      **Parametry:**

      - ``queryset``: QuerySet dokumentů k filtrování.
      - ``name``: Jméno pole pro filtrování.
      - ``value``: Hodnota pro filtrování.

      **Návratová hodnota:**

      Filtrovaný QuerySet.


   .. py:method:: filter_popisne_udaje()

      Filtruje dokumenty podle popisu, poznámky, odkazu a textů v komponentách.

      **Parametry:**

      - ``queryset``: QuerySet dokumentů k filtrování.
      - ``name``: Jméno pole pro filtrování.
      - ``value``: Hodnota pro filtrování.

      **Návratová hodnota:**

      Filtrovaný QuerySet.


   .. py:method:: filter_predmet_pozn_pocet()

      Filtruje dokumenty podle počtu poznámek v předmětech.

      **Parametry:**

      - ``queryset``: QuerySet dokumentů k filtrování.
      - ``name``: Jméno pole pro filtrování.
      - ``value``: Hodnota pro filtrování.

      **Návratová hodnota:**

      Filtrovaný QuerySet.


   .. py:method:: filter_objekt_pozn_pocet()

      Filtruje dokumenty podle počtu poznámek v objektech.

      **Parametry:**

      - ``queryset``: QuerySet dokumentů k filtrování.
      - ``name``: Jméno pole pro filtrování.
      - ``value``: Hodnota pro filtrování.

      **Návratová hodnota:**

      Filtrovaný QuerySet.


   .. py:method:: filter_jistota()

      Filtruje dokumenty podle míry jistoty.

      **Parametry:**

      - ``queryset``: QuerySet dokumentů k filtrování.
      - ``name``: Jméno pole pro filtrování.
      - ``value``: Hodnota pro filtrování.

      **Návratová hodnota:**

      Filtrovaný QuerySet.


   .. py:method:: filter_neident_poznamka()

      Filtruje dokumenty podle poznámky v neidentifikované akci.

      **Parametry:**

      - ``queryset``: QuerySet dokumentů k filtrování.
      - ``name``: Jméno pole pro filtrování.
      - ``value``: Hodnota pro filtrování.

      **Návratová hodnota:**

      Filtrovaný QuerySet.


   .. py:method:: filter_let_poznamka()

      Filtruje dokumenty podle poznámky v letecké akci.

      **Parametry:**

      - ``queryset``: QuerySet dokumentů k filtrování.
      - ``name``: Jméno pole pro filtrování.
      - ``value``: Hodnota pro filtrování.

      **Návratová hodnota:**

      Filtrovaný QuerySet.


   .. py:method:: filter_id_AZ()

      Filtruje dokumenty podle identifikátoru archeologické akce.

      **Parametry:**

      - ``queryset``: QuerySet dokumentů k filtrování.
      - ``name``: Jméno pole pro filtrování.
      - ``value``: Hodnota pro filtrování.

      **Návratová hodnota:**

      Filtrovaný QuerySet.


   .. py:method:: filter_id_projekt()

      Filtruje dokumenty podle identifikátoru projektu.

      **Parametry:**

      - ``queryset``: QuerySet dokumentů k filtrování.
      - ``name``: Jméno pole pro filtrování.
      - ``value``: Hodnota pro filtrování.

      **Návratová hodnota:**

      Filtrovaný QuerySet.


   .. py:method:: filter_exist_neident_akce()

      Filtruje dokumenty s neidentifikovanou akcí.

      **Parametry:**

      - ``queryset``: QuerySet dokumentů k filtrování.
      - ``name``: Jméno pole pro filtrování.
      - ``value``: Hodnota pro filtrování.

      **Návratová hodnota:**

      Filtrovaný QuerySet.


   .. py:method:: filter_exist_komponenty()

      Filtruje dokumenty s komponentami.

      **Parametry:**

      - ``queryset``: QuerySet dokumentů k filtrování.
      - ``name``: Jméno pole pro filtrování.
      - ``value``: Hodnota pro filtrování.

      **Návratová hodnota:**

      Filtrovaný QuerySet.


   .. py:method:: filter_exist_nalezy()

      Filtruje dokumenty s nálezy.

      **Parametry:**

      - ``queryset``: QuerySet dokumentů k filtrování.
      - ``name``: Jméno pole pro filtrování.
      - ``value``: Hodnota pro filtrování.

      **Návratová hodnota:**

      Filtrovaný QuerySet.


   .. py:method:: filter_exist_tvary()

      Filtruje dokumenty s tvary.

      **Parametry:**

      - ``queryset``: QuerySet dokumentů k filtrování.
      - ``name``: Jméno pole pro filtrování.
      - ``value``: Hodnota pro filtrování.

      **Návratová hodnota:**

      Filtrovaný QuerySet.


   .. py:method:: filter_exist_soubory()

      Filtruje dokumenty se soubory.

      **Parametry:**

      - ``queryset``: QuerySet dokumentů k filtrování.
      - ``name``: Jméno pole pro filtrování.
      - ``value``: Hodnota pro filtrování.

      **Návratová hodnota:**

      Filtrovaný QuerySet.


   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.



.. py:class:: DokumentFilterFormHelper

   Třída pro správně zobrazení filtru.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``form``: Parametr ``form`` se předává do volání ``__init__()``.


