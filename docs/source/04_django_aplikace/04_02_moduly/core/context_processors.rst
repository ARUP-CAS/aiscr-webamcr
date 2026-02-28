CORE context_processors
=======================

Modul context_processors.

Funkce
------

.. py:function:: constants_import(request)

   Automatický import stavov projektú do kontextu všech template.
   :param request: Hodnota parametru ``request`` použitého touto operací.

.. py:function:: digi_links_from_settings(request)

   Automatický import linkov na digitálni archiv zo settings do kontextov všech template.
   :param request: Hodnota parametru ``request`` použitého touto operací.

.. py:function:: logout_next_url(request)

   Provádí operaci logout next url.

   :param request: Django HTTP požadavek použitý při zpracování.
   :return: Vrací výsledek provedené operace.

.. py:function:: auto_logout_client(request)

   Automatický výpočet a import kontextu potrebného pro správně zobrzazení automatického logoutu na všech stránkach.
   :param request: Hodnota parametru ``request`` použitého touto operací.

.. py:function:: main_shows(request)

   Provádí operaci main shows.

   :param request: Django HTTP požadavek použitý při zpracování.
   :return: Vrací výsledek provedené operace.
