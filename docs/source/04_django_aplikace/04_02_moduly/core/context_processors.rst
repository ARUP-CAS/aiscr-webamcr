CORE context_processors
=======================

Modul context_processors.

Funkce
------

.. py:function:: constants_import(request)

   Automatický import stavov projektú do kontextu všech template.

   :param request: HTTP požadavek; není přímo využit, ale Django jej předává každému context processoru.

       :return: Vrací proměnná ``constants_dict``.

.. py:function:: digi_links_from_settings(request)

   Automatický import linkov na digitálni archiv zo settings do kontextov všech template.

   :param request: HTTP požadavek; není přímo využit, ale Django jej předává každému context processoru.

       :return: Vrací výsledek volání ``getattr()``.

.. py:function:: logout_next_url(request)

   Vrátí do kontextu šablony aktuální cestu požadavku pro použití jako ``next`` parametr po odhlášení.

   :param request: HTTP požadavek, z jehož atributu ``path`` se čte aktuální URL.

       :return: Vrací slovník.

.. py:function:: auto_logout_client(request)

   Automatický výpočet a import kontextu potrebného pro správně zobrzazení automatického logoutu na všech stránkach.

   :param request: Parametr ``request`` se předává do volání ``str()``, ``seconds_until_session_end()``, pracuje se s atributy ``user``, ovlivňuje větvení podmínek.

       :return: Vrací hodnotu podle větve zpracování, typicky: slovník, proměnná ``ctx``.

.. py:function:: main_shows(request)

   Připraví do kontextu šablony příznaky viditelnosti hlavních sekcí aplikace podle role přihlášeného uživatele.

   :param request: HTTP požadavek, z jehož atributu ``user`` se čte přihlášený uživatel a jeho role.

       :return: Vrací proměnná ``main_show``.
