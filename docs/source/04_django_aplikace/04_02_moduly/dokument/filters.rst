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

      :return: Vrací výsledek provedené operace.


.. py:class:: HistorieFilter

   Třída pro zakladní filtrování historie. Třída je dedená v jednotlivých filtracích záznamů.

   **Metody:**

   .. py:method:: set_filter_fields()

      Nastaví filter fields.

      :param user: Vstupní hodnota ``user`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: _get_history_subquery()

      Vrací history subquery.

      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: Model3DFilter

   Třída pro zakladní filtrování modelu 3D a jejich potomků.

   **Metody:**

   .. py:method:: filter_queryset()

      Filtruje queryset.

      :param queryset: Vstupní hodnota ``queryset`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: filter_popisne_udaje()

      Metoda pro filtrování podle popisu, poznámky, odkazu a poznámek v objektech a předmětech.

   .. py:method:: filter_roky()

      Metoda pro filtrování podle roku revize a popisu ADB.

   .. py:method:: filter_roky_range()

      Metoda pro filtrování podle roku revize a popisu ADB.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).


.. py:class:: Model3DFilterFormHelper

   Třída pro správně zobrazení filtru.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param form: Vstupní hodnota ``form`` pro danou operaci.
      :return: Funkce nevrací hodnotu (``None``).


.. py:class:: DokumentFilter

   Třída pro zakladní filtrování dokumentu a jejich potomků.

   **Metody:**

   .. py:method:: filter_uzemni_prislusnost()

      Metoda pro filtrování podle územní príslušnosti.

   .. py:method:: filter_popisne_udaje()

      Metoda pro filtrování podle popisu, poznámky, licence, čísla objektu, regiónu a události.

   .. py:method:: filter_predmet_pozn_pocet()

      Metoda pro filtrování podle poznámky a počtu predmětu.

   .. py:method:: filter_objekt_pozn_pocet()

      Metoda pro filtrování podle poznámky a počtu objektu.

   .. py:method:: filter_jistota()

      Metoda pro filtrování podle jistoty.

   .. py:method:: filter_neident_poznamka()

      Metoda pro filtrování podle neident akce.

   .. py:method:: filter_let_poznamka()

      Metoda pro filtrování podle letu.

   .. py:method:: filter_id_AZ()

      Metoda pro filtrování podle id AZ.

   .. py:method:: filter_id_projekt()

      Metoda pro filtrování podle id projektu.

   .. py:method:: filter_exist_neident_akce()

      Metoda pro filtrování podle existence neident akce.

   .. py:method:: filter_exist_komponenty()

      Metoda pro filtrování podle existence komponenty.

   .. py:method:: filter_exist_nalezy()

      Metoda pro filtrování podle existence nálezu.

   .. py:method:: filter_exist_tvary()

      Metoda pro filtrování podle existence tvaru.

   .. py:method:: filter_exist_soubory()

      Metoda pro filtrování podle existence souboru.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).


.. py:class:: DokumentFilterFormHelper

   Třída pro správně zobrazení filtru.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param form: Vstupní hodnota ``form`` pro danou operaci.
      :return: Funkce nevrací hodnotu (``None``).

