PROJEKT filtry
==============

Definice filtrů.

Třídy
------

.. py:class:: Users

   Implementuje komponentu ``Users`` v rámci aplikace.

   **Metody:**

   .. py:method:: active_processes()

      Provádí operaci active processes.

      :return: Vrací výsledek volání ``select_related()``.


.. py:class:: KatastrFilterMixin

   Třída pro filtrování záznamu podle katastru, kraje, okresu a popisných údajů.

   Třída je použita v dalších filtrech.

   **Metody:**

   .. py:method:: filtr_katastr()

      Metoda pro filtrování podle názvu hlavního a dalších katastrů.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filtr_katastr``.
      :param value: Parametr ``value`` předává se do volání ``filter()``, ``Q()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

          :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``distinct()``, proměnná ``queryset``.

   .. py:method:: filtr_katastr_kraj()

      Metoda pro filtrování podle názvu okresu hlavního a dalších katastrů.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filtr_katastr_kraj``.
      :param value: Parametr ``value`` předává se do volání ``filter()``, ``Q()``, vstupuje do návratové hodnoty.

          :return: Vrací výsledek volání ``distinct()``.

   .. py:method:: filtr_katastr_okres()

      Metoda pro filtrování podle názvu kraje hlavního a dalších katastrů.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filtr_katastr_okres``.
      :param value: Parametr ``value`` předává se do volání ``filter()``, ``Q()``, vstupuje do návratové hodnoty.

          :return: Vrací výsledek volání ``distinct()``.

   .. py:method:: filter_popisne_udaje()

      Metoda pro filtrování podle popisných údajů.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_popisne_udaje``.
      :param value: Parametr ``value`` předává se do volání ``filter()``, ``Q()``, vstupuje do návratové hodnoty.

          :return: Vrací výsledek volání ``distinct()``.


.. py:class:: ProjektFilter

   Třída pro filtrování projektů.

   **Metody:**

   .. py:method:: filter_queryset()

      Filtruje queryset. v aplikaci.

      :param queryset: Parametr ``queryset`` předává se do volání ``filter_queryset()``, pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.

          :return: Vrací proměnná ``queryset``.

   .. py:method:: filter_planovane_zahajeni()

      Metoda pro filtrování podle plánovaného zahájení.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_planovane_zahajeni``.
      :param value: Parametr ``value`` předává se do volání ``DateRange()``, pracuje se s atributy ``start``, ``stop``, ovlivňuje větvení podmínek.

          :return: Vrací výsledek volání ``filter()``.

   .. py:method:: filter_popisne_udaje_akce()

      Metoda pro filtrování podle popisných údajů akce.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_popisne_udaje_akce``.
      :param value: Parametr ``value`` předává se do volání ``filter()``, ``Q()``, vstupuje do návratové hodnoty.

          :return: Vrací výsledek volání ``distinct()``.

   .. py:method:: filter_has_positive_find()

      Metoda pro filtrování podle pozitivního nálezu akce.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, ``exclude``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_has_positive_find``.
      :param value: Parametr ``value`` ovlivňuje větvení podmínek.

          :return: Vrací výsledek volání ``distinct()``.

   .. py:method:: filter_by_oblast()

      Metoda pro filtrování podle oblasti projektu.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_by_oblast``.
      :param value: Parametr ``value`` ovlivňuje větvení podmínek.

          :return: Vrací hodnotu podle větve zpracování, typicky: proměnná ``queryset``, výsledek volání ``filter()``.

   .. py:method:: filter_announced_after()

      Metoda pro filtrování podle data oznámení od.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_announced_after``.
      :param value: Parametr ``value`` předává se do volání ``filter()``, vstupuje do návratové hodnoty.

          :return: Vrací výsledek volání ``filter()``.

   .. py:method:: filter_announced_before()

      Metoda pro filtrování podle data oznámení do.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_announced_before``.
      :param value: Parametr ``value`` předává se do volání ``filter()``, vstupuje do návratové hodnoty.

          :return: Vrací výsledek volání ``filter()``.

   .. py:method:: filter_approved_after()

      Metoda pro filtrování podle data schválení od.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_approved_after``.
      :param value: Parametr ``value`` předává se do volání ``filter()``, vstupuje do návratové hodnoty.

          :return: Vrací výsledek volání ``filter()``.

   .. py:method:: filter_approved_before()

      Metoda pro filtrování podle data schválení do.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_approved_before``.
      :param value: Parametr ``value`` předává se do volání ``filter()``, vstupuje do návratové hodnoty.

          :return: Vrací výsledek volání ``filter()``.

   .. py:method:: filter_akce_typ()

      Metoda pro filtrování podle typu akce.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_akce_typ``.
      :param value: Parametr ``value`` předává se do volání ``filter()``, ``Q()``, vstupuje do návratové hodnoty.

          :return: Vrací výsledek volání ``distinct()``.

   .. py:method:: filtr_akce_katastr()

      Metoda pro filtrování podle katastru akce.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filtr_akce_katastr``.
      :param value: Parametr ``value`` předává se do volání ``filter()``, ``Q()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

          :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``distinct()``, proměnná ``queryset``.

   .. py:method:: filtr_akce_katastr_kraj()

      Metoda pro filtrování podle kraje katastru akce.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filtr_akce_katastr_kraj``.
      :param value: Parametr ``value`` předává se do volání ``filter()``, ``Q()``, vstupuje do návratové hodnoty.

          :return: Vrací výsledek volání ``distinct()``.

   .. py:method:: filtr_akce_katastr_okres()

      Metoda pro filtrování podle okresu katastru akce.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filtr_akce_katastr_okres``.
      :param value: Parametr ``value`` předává se do volání ``filter()``, ``Q()``, vstupuje do návratové hodnoty.

          :return: Vrací výsledek volání ``distinct()``.

   .. py:method:: filtr_akce_vedouci()

      Metoda pro filtrování podle vedoucího akce.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filtr_akce_vedouci``.
      :param value: Parametr ``value`` předává se do volání ``filter()``, ``Q()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

          :return: Vrací hodnotu podle větve zpracování, typicky: proměnná ``queryset``, výsledek volání ``distinct()``.

   .. py:method:: filtr_akce_organizace()

      Metoda pro filtrování podle organizace akce.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filtr_akce_organizace``.
      :param value: Parametr ``value`` předává se do volání ``filter()``, ``Q()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

          :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``distinct()``, proměnná ``queryset``.

   .. py:method:: filtr_dokumenty_ident()

      Metoda pro filtrování podle identu dokumentu.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filtr_dokumenty_ident``.
      :param value: Parametr ``value`` předává se do volání ``filter()``, ``Q()``, vstupuje do návratové hodnoty.

          :return: Vrací výsledek volání ``distinct()``.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``, pracuje se s atributy ``get``.


.. py:class:: ProjektFilterFormHelper

   Třída pro správně zobrazení filtru.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param form: Parametr ``form`` se předává do volání ``__init__()``.

