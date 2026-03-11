ARCH_Z filtry
=============

Definice filtrů.

Třídy
------

.. py:class:: NumberRangeWidget

   Implementuje komponentu ``NumberRangeWidget`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param attrs: Kolekce ``attrs`` zpracovávaná touto funkcí.

   .. py:method:: decompress()

      Provádí operaci decompress.

      :param value: Parametr ``value`` pracuje se s atributy ``start``, ``stop``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

      :return: Vrací seznam.


.. py:class:: NumberRangeField

   Implementuje komponentu ``NumberRangeField`` v rámci aplikace.


.. py:class:: NumberRangeFilter

   Implementuje komponentu ``NumberRangeFilter`` v rámci aplikace.


.. py:class:: ArchZaznamFilter

   Třída pro základní filtrování archeologických záznamů a jejich potomků.

   **Metody:**

   .. py:method:: filtr_katastr()

      Metoda pro filtrování podle hlavního i vedlejšího katastru.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filtr_katastr``.
      :param value: Parametr ``value`` předává se do volání ``filter()``, ``Q()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``distinct()``, proměnná ``queryset``.

   .. py:method:: filtr_katastr_kraj()

      Metoda pro filtrování podle hlavního i vedlejšího kraje.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filtr_katastr_kraj``.
      :param value: Parametr ``value`` předává se do volání ``filter()``, ``Q()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``distinct()``.

   .. py:method:: filtr_katastr_okres()

      Metoda pro filtrování podle hlavního i vedlejšího okresu.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filtr_katastr_okres``.
      :param value: Parametr ``value`` předává se do volání ``filter()``, ``Q()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``distinct()``.

   .. py:method:: filter_dj_zjisteni()

      Metoda pro filtrování podle dj_zjisteni.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_dj_zjisteni``.
      :param value: Parametr ``value`` ovlivňuje větvení podmínek.

      :return: Vrací výsledek volání ``distinct()``.

   .. py:method:: filter_predmet_pozn_pocet()

      Metoda pro filtrování podle poznámky a počtu předmětů.

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

   .. py:method:: filter_ident_cely()

      Metoda pro filtrování podle identu akce, ale i dočasného.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` nepoužito.
      :param value: Parametr ``value`` ovlivňuje větvení podmínek, předává se do volání ``filter()``.

      :return: Vrací filtrovaný ``queryset`` podle ``ident_cely`` nebo poznámky z historie.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``, pracuje se s atributy ``get``.


.. py:class:: AkceFilter

   Class pro filtrování akce.

   **Metody:**

   .. py:method:: filter_akce_typ()

      Metoda pro filtrování podle typu akce.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_akce_typ``.
      :param value: Parametr ``value`` předává se do volání ``filter()``, ``Q()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``distinct()``.

   .. py:method:: filtr_vedouci()

      Metoda pro filtrování podle hlavního a vedlejšího vedoucího akce.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filtr_vedouci``.
      :param value: Parametr ``value`` předává se do volání ``filter()``, ``Q()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

      :return: Vrací hodnotu podle větve zpracování, typicky: proměnná ``queryset``, výsledek volání ``distinct()``.

   .. py:method:: filter_popisne_udaje()

      Metoda pro filtrování podle lokalizace, upřesnění, uložení, označení akce.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_popisne_udaje``.
      :param value: Parametr ``value`` předává se do volání ``filter()``, ``Q()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``distinct()``.

   .. py:method:: filtr_zahrnout_projektove()

      Metoda pro filtrování mezi projektovými a samostatnými akcemi.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filtr_zahrnout_projektove``.
      :param value: Parametr ``value`` ovlivňuje větvení podmínek.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``filter()``, proměnná ``queryset``.

   .. py:method:: filter_has_positive_find()

      Metoda pro filtrování podle toho či akce má pozitivní DJ.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_has_positive_find``.
      :param value: Parametr ``value`` ovlivňuje větvení podmínek.

      :return: Vrací hodnotu podle větve zpracování, typicky: proměnná ``queryset``, výsledek volání ``distinct()``.

   .. py:method:: filter_adb_popisne_udaje()

      Metoda pro filtrování podle popisných údajů ADB.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_adb_popisne_udaje``.
      :param value: Parametr ``value`` předává se do volání ``filter()``, ``Q()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``distinct()``.

   .. py:method:: filtr_adb_autori()

      Metoda pro filtrování podle autorů revize a popisu ADB.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filtr_adb_autori``.
      :param value: Parametr ``value`` předává se do volání ``filter()``, ``Q()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

      :return: Vrací hodnotu podle větve zpracování, typicky: proměnná ``queryset``, výsledek volání ``distinct()``.

   .. py:method:: filter_adb_roky()

      Metoda pro filtrování podle roku revize a popisu ADB.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` slouží jako vstup pro logiku funkce ``filter_adb_roky``.
      :param value: Parametr ``value`` předává se do volání ``filter()``, ``Q()``, pracuje se s atributy ``start``, ``stop``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``distinct()``.

   .. py:method:: filter_by_z_range()

      Filtruje by z range.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``extra``, vstupuje do návratové hodnoty.
      :param name: Parametr ``name`` ovlivňuje větvení podmínek.
      :param value: Parametr ``value`` předává se do volání ``extra()``, ovlivňuje větvení podmínek.

      :return: Vrací proměnná ``queryset``.

   .. py:method:: filter_queryset()

      Filtruje queryset. v aplikaci.

      :param queryset: Parametr ``queryset`` předává se do volání ``filter_queryset()``, pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.

      :return: Vrací proměnná ``queryset``.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.


.. py:class:: AkceFilterFormHelper

   Class pro form helper pro zobrazení formuláře.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param form: Parametr ``form`` se předává do volání ``__init__()``.

