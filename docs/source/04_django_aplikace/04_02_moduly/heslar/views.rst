HESLAR views
============

Definice views.

Třídy
------

.. py:class:: RuianKatastrAutocomplete

   Třída pohledu pro autocomplete ruian katastru.

   **Metody:**

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      :return: Vrací proměnná ``qs``.


.. py:class:: DokumentTypAutocomplete

   Třída pohledu pro autocomplete dokument typu.

   **Metody:**

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      :return: Vrací proměnná ``qs``.


.. py:class:: DokumentFormatAutocomplete

   Třída pohledu pro autocomplete dokument formatu.

   **Metody:**

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      :return: Vrací proměnná ``qs``.


.. py:class:: PristupnostAutocomplete

   Třída pohledu pro autocomplete pristupnosti.

   **Metody:**

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      :return: Vrací proměnná ``qs``.


.. py:class:: HeslarAutocompleteView

   Třída pohledu pro autocomplete pristupnosti.

   **Metody:**

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      :return: Vrací proměnná ``qs``.


.. py:class:: HeslarNazevAutocompleteView

   Třída pohledu pro autocomplete pristupnosti.

   **Metody:**

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      :return: Vrací proměnná ``qs``.


Funkce
------

.. py:function:: merge_heslare(first, second)

   Vytvoří dvoustupňový select z dvou sad hesel.

   :param first: První sada hesel s ID a názvy
   :param second: Druhá sada hesel hierarchicky podřazena první sadě

   :return: Seznam dvojic (název, možnosti) pro dvoustupňový select

.. py:function:: heslar_12(druha, prvni_kat, id)

   Funkce pro vytvoření dvoustupňového selectu.

   :param druha: Parametr ``druha`` se předává do volání ``filter()``, ``merge_heslare()``, vstupuje do návratové hodnoty.
   :param prvni_kat: Parametr ``prvni_kat`` se předává do volání ``filter()``.
   :param id: Identifikátor ``id`` používaný pro dohledání cílového záznamu.

       :return: Vrací výsledek volání ``merge_heslare()``.

.. py:function:: zjisti_katastr_souradnic(request)

   Funkce pohledu pro vrácení katastru podle souradnic.

   :param request: Parametr ``request`` se předává do volání ``filter()``, ``Point()``, pracuje se s atributy ``GET``.

       :return: Vrací výsledek volání ``JsonResponse()``.

.. py:function:: zjisti_vychozi_hodnotu(request)

   Funkce pohledu pro zjištení výchozí hodnoty z heslaře.

   :param request: Parametr ``request`` se předává do volání ``int()``, pracuje se s atributy ``GET``.

       :return: Vrací výsledek volání ``JsonResponse()``.

.. py:function:: zjisti_nadrazenou_hodnotu(request)

   Funkce pohledu pro zjištení nadřazené hodnoty z heslaře.

   :param request: Parametr ``request`` se předává do volání ``int()``, pracuje se s atributy ``GET``.

       :return: Vrací výsledek volání ``JsonResponse()``.

.. py:function:: heslar_list(heslo_nazev, filter, use_exclude)

   Vrací seznam hesel z heslaře filtrovaných podle kritérií.

   :param heslo_nazev: Název heslaře, ze kterého se načítají hesla
   :param filter: Slovník kritérií pro filtrování záznamů
   :param use_exclude: Má-li být použita metoda exclude namíste filter

   :return: Seznam dvojic (ID, název hesla) ve zvolném jazyce
