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

      **Parametry:**

      - ``attrs``: Kolekce ``attrs`` zpracovávaná touto funkcí.


   .. py:method:: decompress()

      Rozloží hodnotu rozsahu na seznam dvou čísel (začátek a konec).

      **Parametry:**

      - ``value``: Objekt rozsahu s atributy ``start`` a ``stop``; pokud je ``None``, vrátí seznam dvou ``None``.

      **Návratová hodnota:**

      Vrací seznam.



.. py:class:: NumberRangeField

   Implementuje komponentu ``NumberRangeField`` v rámci aplikace.


.. py:class:: NumberRangeFilter

   Implementuje komponentu ``NumberRangeFilter`` v rámci aplikace.


.. py:class:: ArchZaznamFilter

   Třída pro základní filtrování archeologických záznamů a jejich potomků.

   **Metody:**

   .. py:method:: filtr_katastr()

      Metoda pro filtrování podle hlavního i vedlejšího katastru.

      **Parametry:**

      - ``queryset``: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      - ``name``: Název pole filtru (není v metodě využit).
      - ``value``: Kolekce vybraných katastrů, podle které se filtruje hlavní i vedlejší katastr záznamu.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``distinct()``, proměnná ``queryset``.


   .. py:method:: filtr_katastr_kraj()

      Metoda pro filtrování podle hlavního i vedlejšího kraje.

      **Parametry:**

      - ``queryset``: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      - ``name``: Název pole filtru (není v metodě využit).
      - ``value``: Kolekce vybraných krajů, podle které se filtruje kraj hlavního i vedlejšího katastru záznamu.

      **Návratová hodnota:**

      Vrací výsledek volání ``distinct()``.


   .. py:method:: filtr_katastr_okres()

      Metoda pro filtrování podle hlavního i vedlejšího okresu.

      **Parametry:**

      - ``queryset``: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      - ``name``: Název pole filtru (není v metodě využit).
      - ``value``: Kolekce vybraných okresů, podle které se filtruje okres hlavního i vedlejšího katastru záznamu.

      **Návratová hodnota:**

      Vrací výsledek volání ``distinct()``.


   .. py:method:: filter_dj_zjisteni()

      Metoda pro filtrování podle dj_zjisteni.

      **Parametry:**

      - ``queryset``: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      - ``name``: Název pole filtru (není v metodě využit).
      - ``value``: Seznam zvolených hodnot (``"True"`` pro pozitivní, ``"False"`` pro negativní zjištění).

      **Návratová hodnota:**

      Vrací výsledek volání ``distinct()``.


   .. py:method:: filter_predmet_pozn_pocet()

      Metoda pro filtrování podle poznámky a počtu předmětů.

      **Parametry:**

      - ``queryset``: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      - ``name``: Název pole filtru (není v metodě využit).
      - ``value``: Hledaný řetězec, který se porovnává s poznámkou a počtem předmětů v komponentách dokumentačních jednotek.

      **Návratová hodnota:**

      Vrací výsledek volání ``distinct()``.


   .. py:method:: filter_objekt_pozn_pocet()

      Metoda pro filtrování podle poznámky a počtu objektu.

      **Parametry:**

      - ``queryset``: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      - ``name``: Název pole filtru (není v metodě využit).
      - ``value``: Hledaný řetězec, který se porovnává s poznámkou a počtem objektů v komponentách dokumentačních jednotek.

      **Návratová hodnota:**

      Vrací výsledek volání ``distinct()``.


   .. py:method:: filter_ident_cely()

      Metoda pro filtrování podle identu akce, ale i dočasného.

      **Parametry:**

      - ``queryset``: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      - ``name``: Parametr ``name`` nepoužito.
      - ``value``: Parametr ``value`` ovlivňuje větvení podmínek, předává se do volání ``filter()``.

      **Návratová hodnota:**

      Vrací filtrovaný ``queryset`` podle ``ident_cely`` nebo poznámky z historie.


   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``, pracuje se s atributy ``get``.



.. py:class:: AkceFilter

   Class pro filtrování akce.

   **Metody:**

   .. py:method:: filter_akce_typ()

      Metoda pro filtrování podle typu akce.

      **Parametry:**

      - ``queryset``: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      - ``name``: Název pole filtru (není v metodě využit).
      - ``value``: Kolekce vybraných typů akce; filtruje shodu v hlavním i vedlejším typu akce.

      **Návratová hodnota:**

      Vrací výsledek volání ``distinct()``.


   .. py:method:: filtr_vedouci()

      Metoda pro filtrování podle hlavního a vedlejšího vedoucího akce.

      **Parametry:**

      - ``queryset``: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      - ``name``: Název pole filtru (není v metodě využit).
      - ``value``: Kolekce vybraných osob, které jsou vedoucím nebo dalším vedoucím akce.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: proměnná ``queryset``, výsledek volání ``distinct()``.


   .. py:method:: filter_popisne_udaje()

      Metoda pro filtrování podle lokalizace, upřesnění, uložení, označení akce.

      **Parametry:**

      - ``queryset``: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      - ``name``: Název pole filtru (není v metodě využit).
      - ``value``: Hledaný řetězec porovnávaný s lokalizací, souhrnem upřesnění, uložením nálezů, uložením dokumentace a uživatelským označením záznamu.

      **Návratová hodnota:**

      Vrací výsledek volání ``distinct()``.


   .. py:method:: filtr_zahrnout_projektove()

      Metoda pro filtrování mezi projektovými a samostatnými akcemi.

      **Parametry:**

      - ``queryset``: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      - ``name``: Název pole filtru (není v metodě využit).
      - ``value``: Parametr ``value`` ovlivňuje větvení podmínek.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``filter()``, proměnná ``queryset``.


   .. py:method:: filter_has_positive_find()

      Metoda pro filtrování podle toho či akce má pozitivní DJ.

      **Parametry:**

      - ``queryset``: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      - ``name``: Název pole filtru (není v metodě využit).
      - ``value``: Parametr ``value`` ovlivňuje větvení podmínek.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: proměnná ``queryset``, výsledek volání ``distinct()``.


   .. py:method:: filter_adb_popisne_udaje()

      Metoda pro filtrování podle popisných údajů ADB.

      **Parametry:**

      - ``queryset``: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      - ``name``: Název pole filtru (není v metodě využit).
      - ``value``: Parametr ``value`` předává se do volání ``filter()``, ``Q()``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací výsledek volání ``distinct()``.


   .. py:method:: filtr_adb_autori()

      Metoda pro filtrování podle autorů revize a popisu ADB.

      **Parametry:**

      - ``queryset``: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      - ``name``: Název pole filtru (není v metodě využit).
      - ``value``: Parametr ``value`` předává se do volání ``filter()``, ``Q()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: proměnná ``queryset``, výsledek volání ``distinct()``.


   .. py:method:: filter_adb_roky()

      Metoda pro filtrování podle roku revize a popisu ADB.

      **Parametry:**

      - ``queryset``: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      - ``name``: Název pole filtru; hodnota ``vb_niveleta_od`` nebo ``vb_niveleta_do`` určuje směr rozsahu.
      - ``value``: Parametr ``value`` předává se do volání ``filter()``, ``Q()``, pracuje se s atributy ``start``, ``stop``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací výsledek volání ``distinct()``.


   .. py:method:: filter_by_z_range()

      Filtruje by z range.

      **Parametry:**

      - ``queryset``: Parametr ``queryset`` pracuje se s atributy ``extra``, vstupuje do návratové hodnoty.
      - ``name``: Parametr ``name`` ovlivňuje větvení podmínek.
      - ``value``: Parametr ``value`` předává se do volání ``extra()``, ovlivňuje větvení podmínek.

      **Návratová hodnota:**

      Vrací proměnná ``queryset``.


   .. py:method:: filter_queryset()

      Filtruje queryset. v aplikaci.

      **Parametry:**

      - ``queryset``: Parametr ``queryset`` předává se do volání ``filter_queryset()``, pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací proměnná ``queryset``.


   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.



.. py:class:: AkceFilterFormHelper

   Class pro form helper pro zobrazení formuláře.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``form``: Parametr ``form`` se předává do volání ``__init__()``.


