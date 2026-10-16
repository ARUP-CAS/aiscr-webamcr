Django settings
===============

.. TODO: Přidat obsah o Django settings struktuře

Novinkový kanál (News Feed)
---------------------------

.. setting:: NEWS_FEED_BASE_URL

   Základní URL novinkového kanálu ze služby aiscr-news:

   .. autodata:: webclient.settings.base.NEWS_FEED_BASE_URL
      :value:

.. setting:: NEWS_FEED_LANGUAGES

   Podporované jazyky novinkového kanálu:

   .. autodata:: webclient.settings.base.NEWS_FEED_LANGUAGES
      :value:

.. setting:: NEWS_FEED_CACHE_TTL

   Doba platnosti cache pro novinkový kanál:

   .. autodata:: webclient.settings.base.NEWS_FEED_CACHE_TTL
      :value:

.. setting:: NEWS_FEED_CACHE_KEY_PREFIX

   Prefix pro klíče cache novinkového kanálu:

   .. autodata:: webclient.settings.base.NEWS_FEED_CACHE_KEY_PREFIX
      :value:

Periodické úlohy (Celery Beat)
------------------------------

.. setting:: CELERY_BEAT_SCHEDULE

   Konfigurace periodických úloh pro Celery, včetně obnovy novinkového kanálu:

   .. autodata:: webclient.settings.base.CELERY_BEAT_SCHEDULE
      :value:

   Perioda obnovy novinkového kanálu se odvozuje od ``NEWS_FEED_CACHE_TTL``.

