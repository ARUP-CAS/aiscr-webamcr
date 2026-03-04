PROJEKT filtry
==============

Definice filtrů.

Třídy
------

.. py:class:: Users

   Popis není k dispozici.

   **Metody:**

   .. py:method:: active_processes()


.. py:class:: KatastrFilterMixin

   Třída pro filtrování záznamu podle katastru, kraje, okresu a popisných údajů.
   Třída je použita v dalších filtrech.

   **Metody:**

   .. py:method:: filtr_katastr()

      Metoda pro filtrování podle názvu hlavního a dalších katastrů.

   .. py:method:: filtr_katastr_kraj()

      Metoda pro filtrování podle názvu okresu hlavního a dalších katastrů.

   .. py:method:: filtr_katastr_okres()

      Metoda pro filtrování podle názvu kraje hlavního a dalších katastrů.

   .. py:method:: filter_popisne_udaje()

      Metoda pro filtrování podle popisných údajů.


.. py:class:: ProjektFilter

   Třída pro filtrování projektů.

   **Metody:**

   .. py:method:: filter_queryset()

   .. py:method:: filter_planovane_zahajeni()

      Metoda pro filtrování podle plánovaného zahájení.

   .. py:method:: filter_popisne_udaje_akce()

      Metoda pro filtrování podle popisných údajů akce.

   .. py:method:: filter_has_positive_find()

      Metoda pro filtrování podle pozitivního nálezu akce.

   .. py:method:: filter_by_oblast()

      Metoda pro filtrování podle oblasti projektu.

   .. py:method:: filter_announced_after()

      Metoda pro filtrování podle data oznámení od.

   .. py:method:: filter_announced_before()

      Metoda pro filtrování podle data oznámení do.

   .. py:method:: filter_approved_after()

      Metoda pro filtrování podle data schválení od.

   .. py:method:: filter_approved_before()

      Metoda pro filtrování podle data schválení do.

   .. py:method:: filter_akce_typ()

      Metoda pro filtrování podle typu akce.

   .. py:method:: filtr_akce_katastr()

      Metoda pro filtrování podle katastru akce.

   .. py:method:: filtr_akce_katastr_kraj()

      Metoda pro filtrování podle kraje katastru akce.

   .. py:method:: filtr_akce_katastr_okres()

      Metoda pro filtrování podle okresu katastru akce.

   .. py:method:: filtr_akce_vedouci()

      Metoda pro filtrování podle vedoucího akce.

   .. py:method:: filtr_akce_organizace()

      Metoda pro filtrování podle organizace akce.

   .. py:method:: filtr_dokumenty_ident()

      Metoda pro filtrování podle identu dokumentu.

   .. py:method:: __init__()


.. py:class:: ProjektFilterFormHelper

   Třída pro správně zobrazení filtru.

   **Metody:**

   .. py:method:: __init__()

