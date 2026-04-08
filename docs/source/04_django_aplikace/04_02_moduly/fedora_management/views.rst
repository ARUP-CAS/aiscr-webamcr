FEDORA_MANAGEMENT views
=======================

Definice views.

Třídy
------

.. py:class:: AdminRecordProcessingView

   Implementuje komponentu ``AdminRecordProcessingView`` v rámci aplikace.

   **Metody:**

   .. py:method:: process_record()

      Zpracuje jeden záznam v rámci dávkového zpracování metadat — přepisuje se v podtřídách.

      :param record: Instance záznamu ke zpracování.
      :param result: Slovník s výsledky průběhu zpracování.
      :param kwargs: Další parametry předané z pohledu.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: HTTP GET požadavek.
      :param kwargs: Klíčové argumenty včetně ``job_id`` identifikujícího dávkovou úlohu v Redis.

      :return: Vrací výsledek volání ``JsonResponse()``.


.. py:class:: ContinueMedataProcessing

   Implementuje komponentu ``ContinueMedataProcessing`` v rámci aplikace.

   **Metody:**

   .. py:method:: process_record()

      Uloží metadata záznamu do Fedory a aktualizuje výsledkový slovník o stav zpracování.

      :param record: Instance záznamu, jehož metadata mají být uložena.
      :param result: Slovník s výsledky průběhu zpracování.
      :param kwargs: Další parametry předané z pohledu.

      :return: Vrací proměnná ``result``.

