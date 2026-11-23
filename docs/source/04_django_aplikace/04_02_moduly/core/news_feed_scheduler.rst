CORE news_feed_scheduler
========================

Modul news_feed_scheduler.

Přehled modulu
--------------

Sladění databázového plánu obnovy novinek na přihlašovací stránce.

Funkce
------

.. py:function:: reconcile_news_feed_schedule(config)

   Sladí interval úlohy s TTL a zachová ostatní nastavení operátora.

   Vlastní neintervalový plán, cizí úlohu a neplatný plán ponechá beze změny.
   Při shodném intervalu úlohu neukládá a neupozorňuje plánovač.

   :param config: Snímek konfigurace pro izolované testy. Produkční volání jej
       nepředává, aby se aktuální hodnota načetla pod zámkem databázového řádku.
   :return: Vytvořená, aktualizovaná nebo beze změny zachovaná periodická úloha.
