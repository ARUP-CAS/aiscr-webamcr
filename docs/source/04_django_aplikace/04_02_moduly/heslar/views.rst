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

   :param first: Popis parametru ``first``.
   :param second: Popis parametru ``second``.

.. py:function:: heslar_12(druha, prvni_kat, id)

   Funkce pro vytvoření dvoustupňového selectu.

   :param druha: Popis parametru ``druha``.
   :param prvni_kat: Popis parametru ``prvni_kat``.
   :param id: Popis parametru ``id``.

.. py:function:: zjisti_katastr_souradnic(request)

   Funkce pohledu pro vrácení katastru podle souradnic.

   :param request: Popis parametru ``request``.

.. py:function:: zjisti_vychozi_hodnotu(request)

   Funkce pohledu pro zjištení výchozí hodnoty z heslaře.

   :param request: Popis parametru ``request``.

.. py:function:: zjisti_nadrazenou_hodnotu(request)

   Funkce pohledu pro zjištení nadřazené hodnoty z heslaře.

   :param request: Popis parametru ``request``.

.. py:function:: heslar_list(heslo_nazev, filter, use_exclude)

   Provádí operaci heslar list.

   :param heslo_nazev: Vstupní hodnota ``heslo_nazev`` pro danou operaci.
   :param filter: Vstupní hodnota ``filter`` pro danou operaci.
   :param use_exclude: Vstupní hodnota ``use_exclude`` pro danou operaci.
