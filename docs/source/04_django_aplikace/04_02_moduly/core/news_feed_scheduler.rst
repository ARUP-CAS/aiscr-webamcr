CORE news_feed_scheduler
========================

Modul news_feed_scheduler.

Přehled modulu
--------------

Reconciliation helpers for the database-backed login news-feed schedule.

Funkce
------

.. py:function:: reconcile_news_feed_schedule(config)

   Nastaví interval obnovy zpráv a upozorní databázový plánovač.

   :param config: Konfigurace intervalu; pokud chybí, načte se aktuální.
   :return: Vytvořená nebo aktualizovaná periodická úloha.
