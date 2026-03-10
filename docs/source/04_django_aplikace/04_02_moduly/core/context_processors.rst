CORE context_processors
=======================

Modul context_processors.

Funkce
------

.. py:function:: constants_import(request)

   Automatický import stavov projektú do kontextu všech template.

   :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``constants_import``.

   :return: Vrací proměnná ``constants_dict``.

.. py:function:: digi_links_from_settings(request)

   Automatický import linkov na digitálni archiv zo settings do kontextov všech template.

   :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``digi_links_from_settings``.

   :return: Vrací výsledek volání ``getattr()``.

.. py:function:: logout_next_url(request)

   Provádí operaci logout next url.

   :param request: Parametr ``request`` předává se do volání ``debug()``, pracuje se s atributy ``path``, vstupuje do návratové hodnoty.

   :return: Vrací slovník.

.. py:function:: auto_logout_client(request)

   Automatický výpočet a import kontextu potrebného pro správně zobrzazení automatického logoutu na všech stránkach.

   :param request: Parametr ``request`` se předává do volání ``str()``, ``seconds_until_session_end()``, pracuje se s atributy ``user``, ovlivňuje větvení podmínek.

   :return: Vrací hodnotu podle větve zpracování, typicky: slovník, proměnná ``ctx``.

.. py:function:: main_shows(request)

   Provádí operaci main shows.

   :param request: Parametr ``request`` pracuje se s atributy ``user``, ovlivňuje větvení podmínek.

   :return: Vrací proměnná ``main_show``.
