HESLAR views
============

Definice views.

Třídy
------

.. py:class:: RuianKatastrAutocomplete

   Třída pohledu pro autocomplete ruian katastru.

   **Metody:**

   .. py:method:: get_queryset()

      Vrací queryset.

      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: DokumentTypAutocomplete

   Třída pohledu pro autocomplete dokument typu.

   **Metody:**

   .. py:method:: get_queryset()

      Vrací queryset.

      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: DokumentFormatAutocomplete

   Třída pohledu pro autocomplete dokument formatu.

   **Metody:**

   .. py:method:: get_queryset()

      Vrací queryset.

      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: PristupnostAutocomplete

   Třída pohledu pro autocomplete pristupnosti.

   **Metody:**

   .. py:method:: get_queryset()

      Vrací queryset.

      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: HeslarAutocompleteView

   Třída pohledu pro autocomplete pristupnosti.

   **Metody:**

   .. py:method:: get_queryset()

      Vrací queryset.

      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: HeslarNazevAutocompleteView

   Třída pohledu pro autocomplete pristupnosti.

   **Metody:**

   .. py:method:: get_queryset()

      Vrací queryset.

      :return: Vrací načtená data odpovídající vstupním parametrům.


Funkce
------

.. py:function:: merge_heslare(first, second)

   Pomocní funkce pro vytvoření dvoustupňového selectu.

.. py:function:: heslar_12(druha, prvni_kat, id)

   Funkce pro vytvoření dvoustupňového selectu.

.. py:function:: zjisti_katastr_souradnic(request)

   Funkce pohledu pro vrácení katastru podle souradnic.

.. py:function:: zjisti_vychozi_hodnotu(request)

   Funkce pohledu pro zjištení výchozí hodnoty z heslaře.

.. py:function:: zjisti_nadrazenou_hodnotu(request)

   Funkce pohledu pro zjištení nadřazené hodnoty z heslaře.

.. py:function:: heslar_list(heslo_nazev, filter, use_exclude)

   Provádí operaci heslar list.

   :param heslo_nazev: Vstupní hodnota ``heslo_nazev`` pro danou operaci.
   :param filter: Vstupní hodnota ``filter`` pro danou operaci.
   :param use_exclude: Vstupní hodnota ``use_exclude`` pro danou operaci.
   :return: Vrací výsledek provedené operace.
