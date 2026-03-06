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


.. py:class:: DokumentTypAutocomplete

   Třída pohledu pro autocomplete dokument typu.

   **Metody:**

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.


.. py:class:: DokumentFormatAutocomplete

   Třída pohledu pro autocomplete dokument formatu.

   **Metody:**

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.


.. py:class:: PristupnostAutocomplete

   Třída pohledu pro autocomplete pristupnosti.

   **Metody:**

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.


.. py:class:: HeslarAutocompleteView

   Třída pohledu pro autocomplete pristupnosti.

   **Metody:**

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.


.. py:class:: HeslarNazevAutocompleteView

   Třída pohledu pro autocomplete pristupnosti.

   **Metody:**

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.


Funkce
------

.. py:function:: merge_heslare(first, second)

   Pomocní funkce pro vytvoření dvoustupňového selectu.

   :param first: Číselná nebo geometrická hodnota `first` použitá při výpočtu nebo transformaci.
   :param second: Číselná nebo geometrická hodnota `second` použitá při výpočtu nebo transformaci.

.. py:function:: heslar_12(druha, prvni_kat, id)

   Funkce pro vytvoření dvoustupňového selectu.

   :param druha: Číselná nebo geometrická hodnota `druha` použitá při výpočtu nebo transformaci.
   :param prvni_kat: Číselná nebo geometrická hodnota `prvni_kat` použitá při výpočtu nebo transformaci.
   :param id: Identifikátor ``id`` používaný pro dohledání cílového záznamu.

.. py:function:: zjisti_katastr_souradnic(request)

   Funkce pohledu pro vrácení katastru podle souradnic.

   :param request: Aktuální HTTP request předaný view/funkci.

.. py:function:: zjisti_vychozi_hodnotu(request)

   Funkce pohledu pro zjištení výchozí hodnoty z heslaře.

   :param request: Aktuální HTTP request předaný view/funkci.

.. py:function:: zjisti_nadrazenou_hodnotu(request)

   Funkce pohledu pro zjištení nadřazené hodnoty z heslaře.

   :param request: Aktuální HTTP request předaný view/funkci.

.. py:function:: heslar_list(heslo_nazev, filter, use_exclude)

   Provádí operaci heslar list.

   :param heslo_nazev: Heslo ``heslo_nazev`` používané při vytváření nebo aktualizaci účtu.
   :param filter: Queryset/filtr ``filter`` použitý při výběru záznamů.
   :param use_exclude: Příznak ``use_exclude`` určující průběh nebo rozsah zpracování.
