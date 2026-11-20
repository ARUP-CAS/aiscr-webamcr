Django settings
===============

.. TODO: Přidat obsah o Django settings struktuře

Novinkový kanál (News Feed)
---------------------------

Novinkový kanál se nastavuje v databázové skupině ``news_feed`` v administraci
``CustomAdminSettings``. Hodnoty, jejich výchozí nastavení a chování cache popisuje
:doc:`../../02_instalace_nasazeni/news_feed_settings`.

Periodické úlohy (Celery Beat)
------------------------------

.. rubric:: ``CELERY_BEAT_SCHEDULE``

Výchozí konfigurace periodických úloh pro Celery:

.. autodata:: webclient.settings.base.CELERY_BEAT_SCHEDULE

Periodická obnova novinkového kanálu se spravuje v databázi a její interval se
odvozuje od nastavení ``news_feed_cache_ttl``.
