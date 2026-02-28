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


.. py:class:: KatastrFilterMixin

   Třída pro filtrování záznamu podle katastru, kraje, okresu a popisních údajů.

   Třída je prepoužita v dalších filtrech.

   **Metody:**

   .. py:method:: filtr_katastr()

      Metoda pro filtrování podle názvu hlavního a dalších katastrů.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: filtr_katastr_kraj()

      Metoda pro filtrování podle názvu okresu hlavního a dalších katastrů.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: filtr_katastr_okres()

      Metoda pro filtrování podle názvu kraje hlavního a dalších katastrů.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: filter_popisne_udaje()

      Metoda pro filtrování podle popisních údajů.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.


.. py:class:: ProjektFilter

   Třída pro filtrování projektů.

   **Metody:**

   .. py:method:: filter_queryset()

      Filtruje queryset. v aplikaci.

      :param queryset: Vstupní hodnota ``queryset`` pro danou operaci.

   .. py:method:: filter_planovane_zahajeni()

      Metoda pro filtrování podle plánovaného zahájení.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: filter_popisne_udaje_akce()

      Metoda pro filtrování podle popisních údajů akce.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: filter_has_positive_find()

      Metoda pro filtrování podle pozitivního nálezu akce.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: filter_by_oblast()

      Metoda pro filtrování podle oblasti projektu.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: filter_announced_after()

      Metoda pro filtrování podle datumu oznámení od.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: filter_announced_before()

      Metoda pro filtrování podle datumu oznámení do.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: filter_approved_after()

      Metoda pro filtrování podle datumu schválení od.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: filter_approved_before()

      Metoda pro filtrování podle datumu schválení do.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: filter_akce_typ()

      Metoda pro filtrování podle typu akce.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: filtr_akce_katastr()

      Metoda pro filtrování podle katastru akce.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: filtr_akce_katastr_kraj()

      Metoda pro filtrování podle kraje katastru akce.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: filtr_akce_katastr_okres()

      Metoda pro filtrování podle okresu katastru akce.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: filtr_akce_vedouci()

      Metoda pro filtrování podle vedoucího akce.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: filtr_akce_organizace()

      Metoda pro filtrování podle organizace akce.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: filtr_dokumenty_ident()

      Metoda pro filtrování podle identu dokumentu.

      :param queryset: Popis parametru ``queryset``.
      :param name: Popis parametru ``name``.
      :param value: Popis parametru ``value``.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: ProjektFilterFormHelper

   Třída pro správně zobrazení filtru.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param form: Vstupní hodnota ``form`` pro danou operaci.

