DOKUMENT filtry
===============

Definice filtrů.

Třídy
------

.. py:class:: SouborTypFilter

   Implementuje komponentu ``SouborTypFilter`` v rámci aplikace.

   **Metody:**

   .. py:method:: field()

      Provádí operaci field.

      :return: Vrací atribut objektu.


.. py:class:: HistorieFilter

   Třída pro zakladní filtrování historie. Třída je dedená v jednotlivých filtracích záznamů.

   **Metody:**

   .. py:method:: set_filter_fields()

      Nastaví filter fields.

      :param user: Parametr ``user`` pracuje se s atributy ``hlavni_role``, ovlivňuje větvení podmínek.

   .. py:method:: _get_history_subquery()

      Vrací history subquery.

      :return: Načtená data odpovídající zadaným vstupům.


.. py:class:: Model3DFilter

   Třída pro zakladní filtrování modelu 3D a jejich potomků.

   **Metody:**

   .. py:method:: filter_queryset()

      Filtruje queryset. v aplikaci.

      :param queryset: Parametr ``queryset`` předává se do volání ``filter_queryset()``, pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.

      :return: Vrací proměnná ``queryset``.

   .. py:method:: filter_popisne_udaje()

      Metoda pro filtrování podle popisu, poznámky, odkazu a poznámek v objektech a předmětech.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_popisne_udaje``.
      :param value: Parametr ``value`` předává se do volání ``filter()``, ``Q()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``filter()``.

   .. py:method:: filter_roky()

      Metoda pro filtrování podle roku revize a popisu ADB.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_roky``.
      :param value: Parametr ``value`` předává se do volání ``filter()``, pracuje se s atributy ``start``, ``stop``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``distinct()``.

   .. py:method:: filter_roky_range()

      Metoda pro filtrování podle roku revize a popisu ADB.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_roky_range``.
      :param value: Parametr ``value`` pracuje se s atributy ``start``, ``stop``, ovlivňuje větvení podmínek.

      :return: Vrací proměnná ``queryset``.

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

   Třída pro zakladní filtrování dokumentu a jejich potomků.

   **Metody:**

   .. py:method:: filter_uzemni_prislusnost()

      Metoda pro filtrování podle územní príslušnosti.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_uzemni_prislusnost``.
      :param value: Parametr ``value`` předává se do volání ``debug()``, ``reduce()``.

      :return: Vrací výsledek volání ``filter()``.

   .. py:method:: filter_popisne_udaje()

      Metoda pro filtrování podle popisu, poznámky, licence, čísla objektu, regiónu a události.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_popisne_udaje``.
      :param value: Parametr ``value`` předává se do volání ``filter()``, ``Q()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``filter()``.

   .. py:method:: filter_predmet_pozn_pocet()

      Metoda pro filtrování podle poznámky a počtu predmětu.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_predmet_pozn_pocet``.
      :param value: Parametr ``value`` předává se do volání ``filter()``, ``Q()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``distinct()``.

   .. py:method:: filter_objekt_pozn_pocet()

      Metoda pro filtrování podle poznámky a počtu objektu.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_objekt_pozn_pocet``.
      :param value: Parametr ``value`` předává se do volání ``filter()``, ``Q()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``distinct()``.

   .. py:method:: filter_jistota()

      Metoda pro filtrování podle jistoty.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``distinct``, ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_jistota``.
      :param value: Parametr ``value`` ovlivňuje větvení podmínek.

      :return: Vrací výsledek volání ``distinct()``.

   .. py:method:: filter_neident_poznamka()

      Metoda pro filtrování podle neident akce.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_neident_poznamka``.
      :param value: Parametr ``value`` předává se do volání ``filter()``, ``Q()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``distinct()``.

   .. py:method:: filter_let_poznamka()

      Metoda pro filtrování podle letu.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_let_poznamka``.
      :param value: Parametr ``value`` předává se do volání ``filter()``, ``Q()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``distinct()``.

   .. py:method:: filter_id_AZ()

      Metoda pro filtrování podle id AZ.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_id_AZ``.
      :param value: Parametr ``value`` předává se do volání ``filter()``, ``Q()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``distinct()``.

   .. py:method:: filter_id_projekt()

      Metoda pro filtrování podle id projektu.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_id_projekt``.
      :param value: Parametr ``value`` předává se do volání ``filter()``, ``Q()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``distinct()``.

   .. py:method:: filter_exist_neident_akce()

      Metoda pro filtrování podle existence neident akce.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, ``exclude``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_exist_neident_akce``.
      :param value: Parametr ``value`` předává se do volání ``len()``, ovlivňuje větvení podmínek.

      :return: Vrací výsledek volání ``distinct()``.

   .. py:method:: filter_exist_komponenty()

      Metoda pro filtrování podle existence komponenty.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, ``exclude``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_exist_komponenty``.
      :param value: Parametr ``value`` předává se do volání ``len()``, ovlivňuje větvení podmínek.

      :return: Vrací výsledek volání ``distinct()``.

   .. py:method:: filter_exist_nalezy()

      Metoda pro filtrování podle existence nálezu.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, ``exclude``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_exist_nalezy``.
      :param value: Parametr ``value`` předává se do volání ``len()``, ovlivňuje větvení podmínek.

      :return: Vrací výsledek volání ``distinct()``.

   .. py:method:: filter_exist_tvary()

      Metoda pro filtrování podle existence tvaru.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, ``distinct``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_exist_tvary``.
      :param value: Parametr ``value`` předává se do volání ``len()``, ovlivňuje větvení podmínek.

      :return: Vrací výsledek volání ``distinct()``.

   .. py:method:: filter_exist_soubory()

      Metoda pro filtrování podle existence souboru.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, ``distinct``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_exist_soubory``.
      :param value: Parametr ``value`` předává se do volání ``len()``, ovlivňuje větvení podmínek.

      :return: Vrací výsledek volání ``distinct()``.

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

