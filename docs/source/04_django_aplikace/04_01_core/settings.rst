Django settings
===============

.. TODO: Přidat obsah o Django settings struktuře

Novinkový kanál (News Feed)
---------------------------

.. setting:: NEWS_FEED_BASE_URL

   Základní URL pro novinkový kanál ze služby aiscr-news.

   .. code-block:: python

      NEWS_FEED_BASE_URL = "https://arup-cas.github.io/aiscr-news/feed/amcr-info"

.. setting:: NEWS_FEED_LANGUAGES

   Seznam podporovaných jazyků novinkového kanálu.

   .. code-block:: python

      NEWS_FEED_LANGUAGES = ["cs", "en"]

.. setting:: NEWS_FEED_CACHE_TTL

   Doba platnosti cache pro novinkový kanál v sekundách.

   .. code-block:: python

      NEWS_FEED_CACHE_TTL = 3600  # 1 hodina

.. setting:: NEWS_FEED_CACHE_KEY_PREFIX

   Prefix pro klíče cache novinkového kanálu.

   .. code-block:: python

      NEWS_FEED_CACHE_KEY_PREFIX = "news_feed"

Periodické úlohy (Celery Beat)
------------------------------

.. setting:: CELERY_BEAT_SCHEDULE

   Konfigurace periodických úloh pro Celery.

   .. code-block:: python

      CELERY_BEAT_SCHEDULE = {
          "load-news-feed": {
              "task": "webclient.cron.tasks_news_feed.load_news_feed",
              "schedule": timedelta(seconds=(NEWS_FEED_CACHE_TTL - 60)),
              "options": {
                  "max_retries": 3,
              },
          }
      }

   Úloha ``load-news-feed`` načítá novinkový kanál pro všechny podporované jazyky
   a ukládá je do cache. Spouští se každých 59 minut (cache_ttl - 60 sekund).
   Při chybě se úloha automaticky zopakuje s maximálně 3 pokusy.


