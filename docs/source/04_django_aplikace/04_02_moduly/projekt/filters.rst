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

      :param queryset: Vstupní queryset, který má být dále zpracován.
      :param name: Název nebo identifikátor používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: filtr_katastr_kraj()

      Metoda pro filtrování podle názvu okresu hlavního a dalších katastrů.

      :param queryset: Vstupní queryset, který má být dále zpracován.
      :param name: Název nebo identifikátor používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: filtr_katastr_okres()

      Metoda pro filtrování podle názvu kraje hlavního a dalších katastrů.

      :param queryset: Vstupní queryset, který má být dále zpracován.
      :param name: Název nebo identifikátor používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: filter_popisne_udaje()

      Metoda pro filtrování podle popisních údajů.

      :param queryset: Vstupní queryset, který má být dále zpracován.
      :param name: Název nebo identifikátor používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.


.. py:class:: ProjektFilter

   Třída pro filtrování projektů.

   **Metody:**

   .. py:method:: filter_queryset()

      Filtruje queryset. v aplikaci.

      :param queryset: Vstupní queryset, který má být dále zpracován.

   .. py:method:: filter_planovane_zahajeni()

      Metoda pro filtrování podle plánovaného zahájení.

      :param queryset: Vstupní queryset, který má být dále zpracován.
      :param name: Název nebo identifikátor používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: filter_popisne_udaje_akce()

      Metoda pro filtrování podle popisních údajů akce.

      :param queryset: Vstupní queryset, který má být dále zpracován.
      :param name: Název nebo identifikátor používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: filter_has_positive_find()

      Metoda pro filtrování podle pozitivního nálezu akce.

      :param queryset: Vstupní queryset, který má být dále zpracován.
      :param name: Název nebo identifikátor používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: filter_by_oblast()

      Metoda pro filtrování podle oblasti projektu.

      :param queryset: Vstupní queryset, který má být dále zpracován.
      :param name: Název nebo identifikátor používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: filter_announced_after()

      Metoda pro filtrování podle datumu oznámení od.

      :param queryset: Vstupní queryset, který má být dále zpracován.
      :param name: Název nebo identifikátor používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: filter_announced_before()

      Metoda pro filtrování podle datumu oznámení do.

      :param queryset: Vstupní queryset, který má být dále zpracován.
      :param name: Název nebo identifikátor používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: filter_approved_after()

      Metoda pro filtrování podle datumu schválení od.

      :param queryset: Vstupní queryset, který má být dále zpracován.
      :param name: Název nebo identifikátor používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: filter_approved_before()

      Metoda pro filtrování podle datumu schválení do.

      :param queryset: Vstupní queryset, který má být dále zpracován.
      :param name: Název nebo identifikátor používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: filter_akce_typ()

      Metoda pro filtrování podle typu akce.

      :param queryset: Vstupní queryset, který má být dále zpracován.
      :param name: Název nebo identifikátor používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: filtr_akce_katastr()

      Metoda pro filtrování podle katastru akce.

      :param queryset: Vstupní queryset, který má být dále zpracován.
      :param name: Název nebo identifikátor používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: filtr_akce_katastr_kraj()

      Metoda pro filtrování podle kraje katastru akce.

      :param queryset: Vstupní queryset, který má být dále zpracován.
      :param name: Název nebo identifikátor používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: filtr_akce_katastr_okres()

      Metoda pro filtrování podle okresu katastru akce.

      :param queryset: Vstupní queryset, který má být dále zpracován.
      :param name: Název nebo identifikátor používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: filtr_akce_vedouci()

      Metoda pro filtrování podle vedoucího akce.

      :param queryset: Vstupní queryset, který má být dále zpracován.
      :param name: Název nebo identifikátor používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: filtr_akce_organizace()

      Metoda pro filtrování podle organizace akce.

      :param queryset: Vstupní queryset, který má být dále zpracován.
      :param name: Název nebo identifikátor používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: filtr_dokumenty_ident()

      Metoda pro filtrování podle identu dokumentu.

      :param queryset: Vstupní queryset, který má být dále zpracován.
      :param name: Název nebo identifikátor používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: ProjektFilterFormHelper

   Třída pro správně zobrazení filtru.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param form: Formulářová instance zpracovávaná funkcí.

