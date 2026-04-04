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

      **Parametry:**

      - ``record``: Instance záznamu ke zpracování.
      - ``result``: Slovník s výsledky průběhu zpracování.
      - ``kwargs``: Další parametry předané z pohledu.


   .. py:method:: get()

      Vrací výsledek operace.

      **Parametry:**

      - ``request``: HTTP GET požadavek.
      - ``kwargs``: Klíčové argumenty včetně ``job_id`` identifikujícího dávkovou úlohu v Redis.

      **Návratová hodnota:**

      Vrací výsledek volání ``JsonResponse()``.



.. py:class:: ContinueMedataProcessing

   Implementuje komponentu ``ContinueMedataProcessing`` v rámci aplikace.

   **Metody:**

   .. py:method:: process_record()

      Uloží metadata záznamu do Fedory a aktualizuje výsledkový slovník o stav zpracování.

      **Parametry:**

      - ``record``: Instance záznamu, jehož metadata mají být uložena.
      - ``result``: Slovník s výsledky průběhu zpracování.
      - ``kwargs``: Další parametry předané z pohledu.

      **Návratová hodnota:**

      Vrací proměnná ``result``.


