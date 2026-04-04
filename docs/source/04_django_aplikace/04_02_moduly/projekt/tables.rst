PROJEKT tables
==============

Modul tables.

Třídy
------

.. py:class:: ProjektTable

   Třída pro definování tabulky pro projekt použitých pro zobrazení přehledu projektů a exportu.

   **Metody:**

   .. py:method:: render_planovane_zahajeni()

      Vyrenderuje planovane zahajeni.

      :param value: Parametr ``value`` předává se do volání ``isinstance()``, ``str()``, pracuje se s atributy ``lower``, ``upper``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

          :return: Vrací hodnotu podle větve zpracování, typicky: None, hodnotu podle větve zpracování, výsledek volání ``str()``.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``. Může obsahovat klíč ``user`` s instancí přihlášeného uživatele, který se používá pro řízení viditelnosti oznamovatele na úrovni řádku.

   .. py:method:: render_oznamovatel_oznamovatel()

      Vyrenderuje oznamovatele s ohledem na pravidla viditelnosti.

      Implementuje plnou logiku ``get_show_oznamovatel``, včetně časových podmínek závislých na datu
      přihlášení (30 dní) a uzavření (90 dní). Tato data jsou předpočítána jako anotace querysetu
      (``datum_prihlaseni``, ``datum_uzavreni``) a přístupná přes ``getattr`` na záznamu modelu.
      Pokud není uživatel k dispozici (kontext generování Redis snapshotu), vrátí hodnotu bez filtrování.

      :param value: Hodnota pole ``oznamovatel.oznamovatel`` z přidruženého záznamu.
      :param record: Instance projektu z aktuálního řádku tabulky.
      :return: Hodnota oznamovatele, přeložený label ``oznamovatel_oznamovatel.hidden`` pokud uživatel
          nemá oprávnění ji zobrazit, nebo prázdný řetězec pokud projekt nemá oznamovatele.

