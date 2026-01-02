EZ filtry
=========

Definice filtrů.

Třídy
------

.. py:class:: ExterniZdrojFilter

   Třída pro zakladní filtrování externího zdroju a jejich potomků.

   **Metody:**

   .. py:method:: filter_queryset()

   .. py:method:: filter_popisne_udaje()

      Metoda pro filtrování podle názvu, edice, sborníku, časopisu, isbn, issn, roku vydání a poznámek.

   .. py:method:: filter_akce_ident()

      Metoda pro filtrování podle identu celý akce.

   .. py:method:: filter_lokalita_ident()

      Metoda pro filtrování podle identu celý lokality.

   .. py:method:: __init__()


.. py:class:: ExterniZdrojFilterFormHelper

   Třída pro správně zobrazení filtru.

   **Metody:**

   .. py:method:: __init__()
