..
   Tento soubor je automaticky generován. Neupravujte ručně.
   Změny tagů: ``docker-compose*.yml``, ``Dockerfile-DB``; popis a licence:
   ``docs/docker_images_meta.yaml``. Obnovení: ``python docs/generate_module_docs.py``
   nebo ``python docs/licenses/convert_to_rst.py``.
Docker images
=============

Vlastní image
-------------

Tyto image jsou vyvíjeny vývojovým týmem aplikace a jsou specifické pro provoz AMCR.

${amcr_image}
~~~~~~~~~~~~~

- **Verze:** proměnná
- **Licence:** GPL-3.0-or-later
- **Odkaz:** https://github.com/ARUP-CAS/aiscr-webamcr/pkgs/container/aiscr-webamcr, https://hub.docker.com/repository/docker/aiscr/webamcr

- **Bázový image:** ghcr.io/osgeo/gdal
- **Licence bázového image:** MIT License
- **Odkaz na bázový image:** https://github.com/OSGeo/gdal/pkgs/container/gdal

Vlastní image aplikace AMCR postavená na bázi GDAL. Obsahuje Django aplikaci a všechny potřebné závislosti pro provoz webové aplikace.

${proxy_image}
~~~~~~~~~~~~~~

- **Verze:** proměnná
- **Licence:** GPL-3.0-or-later
- **Odkaz:** https://github.com/ARUP-CAS/aiscr-webamcr/pkgs/container/aiscr-webamcr-proxy, https://hub.docker.com/repository/docker/aiscr/webamcr-proxy

- **Bázový image:** nginxinc/nginx-unprivileged
- **Licence bázového image:** BSD 2 License
- **Odkaz na bázový image:** https://github.com/nginxinc/docker-nginx

Vlastní image Nginx proxy serveru založená na nginxinc/nginx-unprivileged. Zajišťuje reverzní proxy a servování statických souborů.

${redis_image} / aiscr/webamcr-redis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Verze:** proměnná
- **Licence:** GPL-3.0-or-later
- **Odkaz:** https://github.com/ARUP-CAS/aiscr-webamcr/pkgs/container/aiscr-webamcr-redis, https://hub.docker.com/repository/docker/aiscr/webamcr-redis

- **Bázový image:** redis
- **Licence bázového image:** RSALv2, SSPLv1
- **Odkaz na bázový image:** https://github.com/redis/redis

Vlastní Redis image založená na oficiálním Redis image. Používá se pro ukládání cache a jako message broker pro Celery.

Generické image
---------------

Tyto image jsou standardní open-source image používané pro provoz podpůrných služeb.

redis
~~~~~

- **Verze:** 8.6.2
- **Licence:** RSALv2, SSPLv1
- **Odkaz:** https://github.com/redis/redis

Oficiální Redis image. Používá se v lokálním vývojovém prostředí jako přímá náhrada za vlastní AMCR Redis image.

postgis/postgis
~~~~~~~~~~~~~~~

- **Verze:** 16-3.4
- **Licence:** MIT License
- **Odkaz:** https://github.com/postgis/docker-postgis

PostgreSQL databáze s PostGIS rozšířením pro geografická data. Používá se pro lokální vývoj a testování.

postgres
~~~~~~~~

- **Verze:** 12.3
- **Licence:** PostgreSQL License
- **Odkaz:** https://github.com/docker-library/postgres

PostgreSQL databáze pro Fedora repository. Používá se jako databázový backend pro Fedora Commons.

eeacms/rsync
~~~~~~~~~~~~

- **Verze:** 3.0
- **Licence:**
- **Odkaz:** https://github.com/eea/eea.docker.rsync

Image pro synchronizaci souborů pomocí rsync. Používá se pro zálohování lokalizačních souborů.

oliver006/redis_exporter
~~~~~~~~~~~~~~~~~~~~~~~~

- **Verze:** v1.82.0-alpine
- **Licence:** MIT license
- **Odkaz:** https://github.com/oliver006/redis_exporter

Exportér metrik pro Redis pro Prometheus monitoring. Shromažďuje metriky o výkonu Redis instance.

danihodovic/celery-exporter
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Verze:** 0.10.14
- **Licence:** MIT license
- **Odkaz:** https://github.com/danihodovic/celery-exporter

Exportér metrik pro Celery úlohy pro Prometheus. Monitoruje stav a výkon asynchronních úloh.

grafana/grafana-enterprise
~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Verze:** 12.4.2
- **Licence:** AGPL-3.0 License
- **Odkaz:** https://github.com/grafana/grafana

Grafana Enterprise pro vizualizaci metrik a monitoringu. Poskytuje dashboardy pro sledování výkonu aplikace.

prom/prometheus
~~~~~~~~~~~~~~~

- **Verze:** v3.10.0
- **Licence:** Apache-2.0 License
- **Odkaz:** https://github.com/prometheus/prometheus

Prometheus pro sběr a ukládání metrik. Slouží jako centrální systém pro monitoring aplikace a infrastruktury.

docker.elastic.co/logstash/logstash
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Verze:** 9.3.3
- **Licence:** SSPL, Elastic License 2.0, Apache License 2.0
- **Odkaz:** https://github.com/elastic/logstash

Logstash pro zpracování a transformaci logů. Zajišťuje parsování a indexování logů do Elasticsearch.

docker.elastic.co/elasticsearch/elasticsearch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Verze:** 9.3.3
- **Licence:** SSPL, Elastic License 2.0, Apache License 2.0
- **Odkaz:** https://github.com/elastic/elasticsearch

Elasticsearch pro fulltextové vyhledávání a analýzu logů. Ukládá a indexuje logy aplikace.

docker.elastic.co/kibana/kibana
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Verze:** 9.3.3
- **Licence:** SSPL, Elastic License 2.0, Apache License 2.0
- **Odkaz:** https://github.com/elastic/kibana

Kibana pro vizualizaci a analýzu logů z Elasticsearch. Poskytuje webové rozhraní pro prohlížení a vyhledávání v logech.

selenium/standalone-chromium
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Verze:** 147.0
- **Licence:** Apache License 2.0
- **Odkaz:** https://github.com/SeleniumHQ/docker-selenium

Selenium standalone Chromium pro automatizované testování. Používá se pro end-to-end testy webové aplikace.

gcr.io/cadvisor/cadvisor
~~~~~~~~~~~~~~~~~~~~~~~~

- **Verze:** v0.55.1
- **Licence:** Apache License 2.0
- **Odkaz:** https://github.com/google/cadvisor

cAdvisor pro monitorování využití zdrojů kontejnerů. Shromažďuje metriky o CPU, paměti a síti.

prometheuscommunity/postgres-exporter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Verze:** v0.19.1
- **Licence:** Apache-2.0 License
- **Odkaz:** https://github.com/prometheus-community/postgres_exporter

Exportér metrik pro PostgreSQL databázi pro Prometheus. Monitoruje výkon a stav databázových operací.

dpage/pgadmin4
~~~~~~~~~~~~~~

- **Verze:** latest
- **Licence:** PostgreSQL License
- **Odkaz:** https://github.com/pgadmin-org/pgadmin4

pgAdmin4 webové rozhraní pro správu PostgreSQL databází. Používá se pro lokální vývoj a správu databáze.

memcached
~~~~~~~~~

- **Verze:** latest
- **Licence:** BSD License
- **Odkaz:** https://github.com/docker-library/memcached

Memcached pro ukládání cache v paměti. Používá se pro zrychlení aplikace pomocí cache vrstvy.

fcrepo/fcrepo
~~~~~~~~~~~~~

- **Verze:** 6.5.1-tomcat9
- **Licence:** Apache-2.0 License
- **Odkaz:** https://github.com/fcrepo/fcrepo

Fedora Commons Repository pro ukládání digitálních objektů. Slouží jako digitální repozitář pro archivaci dat.

