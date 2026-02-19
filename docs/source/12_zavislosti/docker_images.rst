Docker images
=============

.. TODO: Přidat obsah o base images, third-party containers


.. list-table:: Přehled Docker imagí
   :header-rows: 1
   :widths: 30 15 55

   * - Image
     - Verze
     - Popis
   * - ``${amcr_image}``
     - proměnná
     - Vlastní image aplikace AMCR postavená na bázi GDAL. Obsahuje Django aplikaci a všechny potřebné závislosti pro provoz webové aplikace.
   * - ``${proxy_image}``
     - proměnná
     - Vlastní image Nginx proxy serveru založená na nginxinc/nginx-unprivileged. Zajišťuje reverzní proxy a servování statických souborů.
   * - ``${redis_image}`` / ``aiscr/webamcr-redis:latest``
     - proměnná / latest
     - Vlastní Redis image založená na oficiálním Redis image. Používá se pro ukládání cache a jako message broker pro Celery.
   * - ``postgis/postgis:16-3.4``
     - 16-3.4
     - PostgreSQL databáze s PostGIS rozšířením pro geografická data. Používá se pro lokální vývoj a testování.
   * - ``postgres:12.3``
     - 12.3
     - PostgreSQL databáze pro Fedora repository. Používá se jako databázový backend pro Fedora Commons.
   * - ``eeacms/rsync:3.0``
     - 3.0
     - Image pro synchronizaci souborů pomocí rsync. Používá se pro zálohování lokalizačních souborů.
   * - ``oliver006/redis_exporter:v1.80.1-alpine``
     - v1.80.1-alpine
     - Exportér metrik pro Redis pro Prometheus monitoring. Shromažďuje metriky o výkonu Redis instance.
   * - ``danihodovic/celery-exporter:0.10.14``
     - 0.10.14
     - Exportér metrik pro Celery úlohy pro Prometheus. Monitoruje stav a výkon asynchronních úloh.
   * - ``grafana/grafana-enterprise:12.2.1``
     - 12.2.1
     - Grafana Enterprise pro vizualizaci metrik a monitoringu. Poskytuje dashboardy pro sledování výkonu aplikace.
   * - ``prom/prometheus:v3.7.3``
     - v3.7.3
     - Prometheus pro sběr a ukládání metrik. Slouží jako centrální systém pro monitoring aplikace a infrastruktury.
   * - ``docker.elastic.co/logstash/logstash:8.19.0``
     - 8.19.0
     - Logstash pro zpracování a transformaci logů. Zajišťuje parsování a indexování logů do Elasticsearch.
   * - ``docker.elastic.co/elasticsearch/elasticsearch:8.19.0``
     - 8.19.0
     - Elasticsearch pro fulltextové vyhledávání a analýzu logů. Ukládá a indexuje logy aplikace.
   * - ``docker.elastic.co/kibana/kibana:8.19.0``
     - 8.19.0
     - Kibana pro vizualizaci a analýzu logů z Elasticsearch. Poskytuje webové rozhraní pro prohlížení a vyhledávání v logech.
   * - ``selenium/standalone-chromium:143.0``
     - 143.0
     - Selenium standalone Firefox pro automatizované testování. Používá se pro end-to-end testy webové aplikace.
   * - ``gcr.io/cadvisor/cadvisor:v0.52.1``
     - v0.52.1
     - cAdvisor pro monitorování využití zdrojů kontejnerů. Shromažďuje metriky o CPU, paměti a síti.
   * - ``prometheuscommunity/postgres-exporter:v0.18.1``
     - v0.18.1
     - Exportér metrik pro PostgreSQL databázi pro Prometheus. Monitoruje výkon a stav databázových operací.
   * - ``dpage/pgadmin4``
     - latest
     - pgAdmin4 webové rozhraní pro správu PostgreSQL databází. Používá se pro lokální vývoj a správu databáze.
   * - ``memcached:latest``
     - latest
     - Memcached pro ukládání cache v paměti. Používá se pro zrychlení aplikace pomocí cache vrstvy.
   * - ``fcrepo/fcrepo:6.5.1-tomcat9``
     - 6.5.1-tomcat9
     - Fedora Commons Repository pro ukládání digitálních objektů. Slouží jako digitální repozitář pro archivaci dat.


