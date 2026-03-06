DOKUMENT filtry
===============

Definice filtrů.

Třídy
------

.. py:class:: SouborTypFilter

   Implementuje komponentu ``SouborTypFilter`` v rámci aplikace.

   **Metody:**

   .. py:method:: field()

      Provádí operaci field.


.. py:class:: HistorieFilter

   Třída pro zakladní filtrování historie. Třída je dedená v jednotlivých filtracích záznamů.

   **Metody:**

   .. py:method:: set_filter_fields()

      Nastaví filter fields.

      :param user: Uživatel, v jehož kontextu se operace provádí.

   .. py:method:: _get_history_subquery()

      Vrací history subquery.

      :return: Načtená data odpovídající zadaným vstupům.


.. py:class:: Model3DFilter

   Třída pro zakladní filtrování modelu 3D a jejich potomků.

   **Metody:**

   .. py:method:: filter_queryset()

      Filtruje queryset. v aplikaci.

      :param queryset: Vstupní queryset, který má být dále zpracován.

   .. py:method:: filter_popisne_udaje()

      Metoda pro filtrování podle popisu, poznámky, odkazu a poznámek v objektech a předmětech.

      :param queryset: Vstupní queryset, který má být dále zpracován.
      :param name: Název nebo identifikátor používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: filter_roky()

      Metoda pro filtrování podle roku revize a popisu ADB.

      :param queryset: Vstupní queryset, který má být dále zpracován.
      :param name: Název nebo identifikátor používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: filter_roky_range()

      Metoda pro filtrování podle roku revize a popisu ADB.

      :param queryset: Vstupní queryset, který má být dále zpracován.
      :param name: Název nebo identifikátor používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: Model3DFilterFormHelper

   Třída pro správně zobrazení filtru.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param form: Formulářová instance zpracovávaná funkcí.


.. py:class:: DokumentFilter

   Třída pro zakladní filtrování dokumentu a jejich potomků.

   **Metody:**

   .. py:method:: filter_uzemni_prislusnost()

      Metoda pro filtrování podle územní príslušnosti.

      :param queryset: Vstupní queryset, který má být dále zpracován.
      :param name: Název nebo identifikátor používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: filter_popisne_udaje()

      Metoda pro filtrování podle popisu, poznámky, licence, čísla objektu, regiónu a události.

      :param queryset: Vstupní queryset, který má být dále zpracován.
      :param name: Název nebo identifikátor používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: filter_predmet_pozn_pocet()

      Metoda pro filtrování podle poznámky a počtu predmětu.

      :param queryset: Vstupní queryset, který má být dále zpracován.
      :param name: Název nebo identifikátor používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: filter_objekt_pozn_pocet()

      Metoda pro filtrování podle poznámky a počtu objektu.

      :param queryset: Vstupní queryset, který má být dále zpracován.
      :param name: Název nebo identifikátor používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: filter_jistota()

      Metoda pro filtrování podle jistoty.

      :param queryset: Vstupní queryset, který má být dále zpracován.
      :param name: Název nebo identifikátor používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: filter_neident_poznamka()

      Metoda pro filtrování podle neident akce.

      :param queryset: Vstupní queryset, který má být dále zpracován.
      :param name: Název nebo identifikátor používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: filter_let_poznamka()

      Metoda pro filtrování podle letu.

      :param queryset: Vstupní queryset, který má být dále zpracován.
      :param name: Název nebo identifikátor používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: filter_id_AZ()

      Metoda pro filtrování podle id AZ.

      :param queryset: Vstupní queryset, který má být dále zpracován.
      :param name: Název nebo identifikátor používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: filter_id_projekt()

      Metoda pro filtrování podle id projektu.

      :param queryset: Vstupní queryset, který má být dále zpracován.
      :param name: Název nebo identifikátor používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: filter_exist_neident_akce()

      Metoda pro filtrování podle existence neident akce.

      :param queryset: Vstupní queryset, který má být dále zpracován.
      :param name: Název nebo identifikátor používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: filter_exist_komponenty()

      Metoda pro filtrování podle existence komponenty.

      :param queryset: Vstupní queryset, který má být dále zpracován.
      :param name: Název nebo identifikátor používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: filter_exist_nalezy()

      Metoda pro filtrování podle existence nálezu.

      :param queryset: Vstupní queryset, který má být dále zpracován.
      :param name: Název nebo identifikátor používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: filter_exist_tvary()

      Metoda pro filtrování podle existence tvaru.

      :param queryset: Vstupní queryset, který má být dále zpracován.
      :param name: Název nebo identifikátor používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: filter_exist_soubory()

      Metoda pro filtrování podle existence souboru.

      :param queryset: Vstupní queryset, který má být dále zpracován.
      :param name: Název nebo identifikátor používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: DokumentFilterFormHelper

   Třída pro správně zobrazení filtru.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param form: Formulářová instance zpracovávaná funkcí.

