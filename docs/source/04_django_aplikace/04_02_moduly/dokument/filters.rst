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

      :return: FormField s volbami z databáze.


.. py:class:: HistorieFilter

   Třída pro základní filtrování historie. Třída je děděná v jednotlivých filtracích záznamů.

   **Metody:**

   .. py:method:: set_filter_fields()

      Nastaví filter fields.

      :param user: Parametr ``user`` pracuje se s atributy ``hlavni_role``, ovlivňuje větvení podmínek.

   .. py:method:: _get_history_subquery()

      Vrací history subquery.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: filter_ident_cely()

      Metoda pro filtrování podle identu dokumentu/projektu/EZ, ale i dočasného.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` nepoužito.
      :param value: Parametr ``value`` ovlivňuje větvení podmínek, předává se do volání ``filter()``.

      :return: Vrací filtrovaný ``queryset`` podle ``ident_cely`` nebo poznámky z historie.


.. py:class:: Model3DFilter

   Třída pro základní filtrování modelu 3D a jejich potomků.

   **Metody:**

   .. py:method:: filter_queryset()

      Filtruje queryset. v aplikaci.

      :param queryset: Parametr ``queryset`` předává se do volání ``filter_queryset()``, pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.

      :return: Vrací proměnná ``queryset``.

   .. py:method:: filter_popisne_udaje()

      Filtruje modely 3D podle popisu, poznámky, odkazu a textů v komponentách.

      :param queryset: QuerySet modelů 3D k filtrování.
      :param name: Jméno pole pro filtrování.
      :param value: Hodnota pro vyhledávání.
      :return: Filtrovaný QuerySet.

   .. py:method:: filter_roky()

      Filtruje modely podle roku vzniku.

      :param queryset: QuerySet modelů k filtrování.
      :param name: Jméno pole pro filtrování.
      :param value: RangeField s start/stop roky.
      :return: Filtrovaný QuerySet.

   .. py:method:: filter_roky_range()

      Filtruje modely podle rozsahu let.

      :param queryset: QuerySet modelů k filtrování.
      :param name: Jméno pole pro filtrování (tuple name).
      :param value: RangeField s start/stop roky.
      :return: Filtrovaný QuerySet.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``, pracuje se s atributy ``get``.


.. py:class:: Model3DFilterFormHelper

   Třída pro správně zobrazení filtru.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param form: Parametr ``form`` se předává do volání ``__init__()``.


.. py:class:: DokumentFilter

   Třída pro základní filtrování dokumentu a jejich potomků.

   **Metody:**

   .. py:method:: filter_uzemni_prislusnost()

      Filtruje dokumenty podle územní příslušnosti.

      :param queryset: QuerySet dokumentů k filtrování.
      :param name: Jméno pole pro filtrování.
      :param value: Hodnota pro filtrování.
      :return: Filtrovaný QuerySet.

   .. py:method:: filter_popisne_udaje()

      Filtruje dokumenty podle popisu, poznámky, odkazu a textů v komponentách.

      :param queryset: QuerySet dokumentů k filtrování.
      :param name: Jméno pole pro filtrování.
      :param value: Hodnota pro filtrování.
      :return: Filtrovaný QuerySet.

   .. py:method:: filter_predmet_pozn_pocet()

      Filtruje dokumenty podle počtu poznámek v předmětech.

      :param queryset: QuerySet dokumentů k filtrování.
      :param name: Jméno pole pro filtrování.
      :param value: Hodnota pro filtrování.
      :return: Filtrovaný QuerySet.

   .. py:method:: filter_objekt_pozn_pocet()

      Filtruje dokumenty podle počtu poznámek v objektech.

      :param queryset: QuerySet dokumentů k filtrování.
      :param name: Jméno pole pro filtrování.
      :param value: Hodnota pro filtrování.
      :return: Filtrovaný QuerySet.

   .. py:method:: filter_jistota()

      Filtruje dokumenty podle míry jistoty.

      :param queryset: QuerySet dokumentů k filtrování.
      :param name: Jméno pole pro filtrování.
      :param value: Hodnota pro filtrování.
      :return: Filtrovaný QuerySet.

   .. py:method:: filter_neident_poznamka()

      Filtruje dokumenty podle poznámky v neidentifikované akci.

      :param queryset: QuerySet dokumentů k filtrování.
      :param name: Jméno pole pro filtrování.
      :param value: Hodnota pro filtrování.
      :return: Filtrovaný QuerySet.

   .. py:method:: filter_let_poznamka()

      Filtruje dokumenty podle poznámky v letecké akci.

      :param queryset: QuerySet dokumentů k filtrování.
      :param name: Jméno pole pro filtrování.
      :param value: Hodnota pro filtrování.
      :return: Filtrovaný QuerySet.

   .. py:method:: filter_id_AZ()

      Filtruje dokumenty podle identifikátoru archeologické akce.

      :param queryset: QuerySet dokumentů k filtrování.
      :param name: Jméno pole pro filtrování.
      :param value: Hodnota pro filtrování.
      :return: Filtrovaný QuerySet.

   .. py:method:: filter_id_projekt()

      Filtruje dokumenty podle identifikátoru projektu.

      :param queryset: QuerySet dokumentů k filtrování.
      :param name: Jméno pole pro filtrování.
      :param value: Hodnota pro filtrování.
      :return: Filtrovaný QuerySet.

   .. py:method:: filter_exist_neident_akce()

      Filtruje dokumenty s neidentifikovanou akcí.

      :param queryset: QuerySet dokumentů k filtrování.
      :param name: Jméno pole pro filtrování.
      :param value: Hodnota pro filtrování.
      :return: Filtrovaný QuerySet.

   .. py:method:: filter_exist_komponenty()

      Filtruje dokumenty s komponentami.

      :param queryset: QuerySet dokumentů k filtrování.
      :param name: Jméno pole pro filtrování.
      :param value: Hodnota pro filtrování.
      :return: Filtrovaný QuerySet.

   .. py:method:: filter_exist_nalezy()

      Filtruje dokumenty s nálezy.

      :param queryset: QuerySet dokumentů k filtrování.
      :param name: Jméno pole pro filtrování.
      :param value: Hodnota pro filtrování.
      :return: Filtrovaný QuerySet.

   .. py:method:: filter_exist_tvary()

      Filtruje dokumenty s tvary.

      :param queryset: QuerySet dokumentů k filtrování.
      :param name: Jméno pole pro filtrování.
      :param value: Hodnota pro filtrování.
      :return: Filtrovaný QuerySet.

   .. py:method:: filter_exist_soubory()

      Filtruje dokumenty se soubory.

      :param queryset: QuerySet dokumentů k filtrování.
      :param name: Jméno pole pro filtrování.
      :param value: Hodnota pro filtrování.
      :return: Filtrovaný QuerySet.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.


.. py:class:: DokumentFilterFormHelper

   Třída pro správně zobrazení filtru.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param form: Parametr ``form`` se předává do volání ``__init__()``.

