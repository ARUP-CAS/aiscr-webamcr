"""Worker procesu pro test konkurence record-locku, spouštěný metodou ``spawn``.

Modul na úrovni importu nenačítá nic z Django ani aplikace: potomek ho importuje dřív, než
zavolá ``django.setup()``, a import modelů by v tu chvíli selhal na ``AppRegistryNotReady``.
"""

import os


def process_worker(ident, results_q, database_names):
    """Načte Django, pokusí se získat zámek záznamu a výsledek vloží do fronty.

    Nový interpret nezdědí sokety ani zámky rodiče, proto nic nezavírá (zavření spojení zděděného
    přes ``fork`` by ukončilo PostgreSQL relaci rodiče). Čerstvě načtené settings ukazují na
    konfigurované databáze, proto worker přepne aliasy na testovací databáze rodiče.

    :param ident: Identifikátor záznamu, o jehož zámek procesy soutěží.
    :param results_q: Fronta, do které worker vloží výsledek pokusu nebo text chyby.
    :param database_names: Názvy testovacích databází rodiče podle aliasu.
    """
    import django

    django.setup()
    from api.views import PasApiBaseView
    from django.db import connections

    for alias, name in database_names.items():
        connections[alias].close()
        connections[alias].settings_dict["NAME"] = name

    try:
        acquired, _ttl = PasApiBaseView._acquire_record_lock(ident)
        results_q.put(acquired)
    except Exception as error:
        # Chybu vrátí rodiči jako text, aby se v asserci neztratila.
        results_q.put(repr(error))
    finally:
        # Výsledek se nejdřív vyprázdní do roury, pak proces skončí bez atexit handlerů
        # a finalizerů Django a cache klientů, které výsledek testu nijak neovlivňují.
        results_q.close()
        results_q.join_thread()
        os._exit(0)
