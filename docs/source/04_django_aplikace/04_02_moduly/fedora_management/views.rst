FEDORA_MANAGEMENT views
=======================

Definice views.

Třídy
------

.. py:class:: AdminRecordProcessingView

   Základ dávkového zpracování záznamů polovaného z administrace.

   Průběh drží Redis: pod klíčem ``job_id`` leží ``"<index>;<ident>;<ident>…"``
   a každé zavolání zpracuje jeden ident a index posune. JS na stránce průběhu
   volá endpoint dokola, dokud zbývají záznamy.

   Podtřída dodá :meth:`process_record`; protokol (čtení fronty, posun indexu,
   výpočet progresu, ošetření chyb) je společný, aby se opravy nemusely dělat
   na dvou místech.

   **Metody:**

   .. py:method:: process_record()

      Zpracuje jeden záznam v rámci dávkového zpracování metadat — přepisuje se v podtřídách.

      :param record: Instance záznamu ke zpracování.
      :param result: Slovník s výsledky průběhu zpracování.
      :param kwargs: Další parametry předané z pohledu.
      :return: Aktualizovaný slovník ``result``.

   .. py:method:: je_platny_job_id()

      Ověří, že klíč patří do jmenného prostoru téhle úlohy.

      :param job_id: Identifikátor z URL.
      :return: ``True``, když prefix sedí nebo se kontrola nepoužívá.

   .. py:method:: get()

      Zpracuje další záznam ve frontě a vrátí JSON s progresem.

      :param request: HTTP GET požadavek.
      :param kwargs: Klíčové argumenty včetně ``job_id`` identifikujícího dávkovou úlohu v Redis.

      :return: ``JsonResponse`` se strukturou ``{progress, remaining, ident_cely, result, detail}``.
      :raises Http404: Když ``job_id`` nepatří do jmenného prostoru úlohy.


.. py:class:: ContinueMedataProcessing

   Implementuje komponentu ``ContinueMedataProcessing`` v rámci aplikace.

   **Metody:**

   .. py:method:: process_record()

      Uloží metadata záznamu do Fedory a aktualizuje výsledkový slovník o stav zpracování.

      :param record: Instance záznamu, jehož metadata mají být uložena.
      :param result: Slovník s výsledky průběhu zpracování.
      :param kwargs: Další parametry předané z pohledu.

      :return: Vrací proměnná ``result``.

