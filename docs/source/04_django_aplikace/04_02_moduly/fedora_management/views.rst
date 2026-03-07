FEDORA_MANAGEMENT views
=======================

Definice views.

Třídy
------

.. py:class:: AdminRecordProcessingView

   Implementuje komponentu ``AdminRecordProcessingView`` v rámci aplikace.

   **Metody:**

   .. py:method:: process_record()

      Provádí operaci process record.

      :param record: Parametr ``record`` slouží jako vstup pro logiku funkce ``process_record``.
      :param result: Textový název, klíč nebo zpráva ``result`` používaná v rámci operace.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``process_record``.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``process_record()``, pracuje se s atributy ``get``.

      :return: Vrací výsledek volání ``JsonResponse()``.


.. py:class:: ContinueMedataProcessing

   Implementuje komponentu ``ContinueMedataProcessing`` v rámci aplikace.

   **Metody:**

   .. py:method:: process_record()

      Provádí operaci process record.

      :param record: Parametr ``record`` předává se do volání ``isinstance()``, ``debug()``, pracuje se s atributy ``save_metadata``, ``ident_cely``, ovlivňuje větvení podmínek.
      :param result: Textový název, klíč nebo zpráva ``result`` používaná v rámci operace.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``process_record``.

      :return: Vrací proměnná ``result``.

