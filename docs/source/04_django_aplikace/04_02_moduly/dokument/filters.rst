DOKUMENT filtry
===============

Definice filtrů.

Třídy
------

.. py:class:: SouborTypFilter

   Popis není k dispozici.

   **Metody:**

   .. py:method:: field()


.. py:class:: HistorieFilter

   Třída pro základní filtrování historie. Třída je děděná v jednotlivých filtracích záznamů.

   **Metody:**

   .. py:method:: set_filter_fields()

   .. py:method:: _get_history_subquery()

   .. py:method:: filter_ident_cely()

      Metoda pro filtrování podle identu projektu, ale i dočasného.


.. py:class:: Model3DFilter

   Třída pro základní filtrování modelu 3D a jejich potomků.

   **Metody:**

   .. py:method:: filter_queryset()

   .. py:method:: filter_popisne_udaje()

      Metoda pro filtrování podle popisu, poznámky, odkazu a poznámek v objektech a předmětech.

   .. py:method:: filter_roky()

      Metoda pro filtrování podle roku revize a popisu ADB.

   .. py:method:: filter_roky_range()

      Metoda pro filtrování podle roku revize a popisu ADB.

   .. py:method:: __init__()


.. py:class:: Model3DFilterFormHelper

   Třída pro správně zobrazení filtru.

   **Metody:**

   .. py:method:: __init__()


.. py:class:: DokumentFilter

   Třída pro základní filtrování dokumentu a jejich potomků.

   **Metody:**

   .. py:method:: filter_uzemni_prislusnost()

      Metoda pro filtrování podle územní příslušnosti.

   .. py:method:: filter_popisne_udaje()

      Metoda pro filtrování podle popisu, poznámky, licence, čísla objektu, regionu a události.

   .. py:method:: filter_predmet_pozn_pocet()

      Metoda pro filtrování podle poznámky a počtu předmětů.

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


.. py:class:: DokumentFilterFormHelper

   Třída pro správně zobrazení filtru.

   **Metody:**

   .. py:method:: __init__()

