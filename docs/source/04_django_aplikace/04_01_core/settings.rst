Django settings
===============

.. TODO: Přidat obsah o Django settings struktuře

Novinkový kanál (News Feed)
---------------------------

.. rubric:: ``NEWS_FEED_BASE_URL``

Základní URL novinkového kanálu ze služby aiscr-news:

.. autodata:: webclient.settings.base.NEWS_FEED_BASE_URL

.. rubric:: ``NEWS_FEED_LANGUAGES``

Podporované jazyky novinkového kanálu:

.. autodata:: webclient.settings.base.NEWS_FEED_LANGUAGES

.. rubric:: ``NEWS_FEED_CACHE_TTL``

Doba platnosti cache pro novinkový kanál:

.. autodata:: webclient.settings.base.NEWS_FEED_CACHE_TTL

.. rubric:: ``NEWS_FEED_CACHE_KEY_PREFIX``

Prefix pro klíče cache novinkového kanálu:

.. autodata:: webclient.settings.base.NEWS_FEED_CACHE_KEY_PREFIX

.. rubric:: ``NEWS_FEED_TIMEOUT``

Časový limit HTTP požadavku na jeden jazykový kanál v sekundách (výchozí hodnota ``10``).
Po jeho překročení se načtení daného jazyka považuje za neúspěšné a Celery úloha jej zkusí
znovu podle nastavení opakování úlohy.

.. autodata:: webclient.settings.base.NEWS_FEED_TIMEOUT

.. rubric:: ``NEWS_FEED_WARNING_RATE_LIMIT``

Interval v sekundách, během kterého se upozornění pro položku se stejným slugem zapíše do
logu nejvýše jednou; upozornění bez slugů se neomezují (výchozí hodnota ``3600``, tedy jedna
hodina).

.. autodata:: webclient.settings.base.NEWS_FEED_WARNING_RATE_LIMIT

Periodické úlohy (Celery Beat)
------------------------------

.. rubric:: ``CELERY_BEAT_SCHEDULE``

Konfigurace periodických úloh pro Celery, včetně obnovy novinkového kanálu:

.. autodata:: webclient.settings.base.CELERY_BEAT_SCHEDULE

Perioda obnovy novinkového kanálu se odvozuje od ``NEWS_FEED_CACHE_TTL``.
