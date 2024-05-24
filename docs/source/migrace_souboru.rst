Migrace souborů
================================

Soubory je možné migraovat z napojeného disku. Adresář disku je potřeba připojit v souboru `docker-compose.yml`

.. code::
    volumes:
      - static_data:/vol/web
      - locale_data:/vol/web/locale
      - nginx_data:/vol/web/nginx/data
      - /opt/data-migrace:/vol/data-migrace

Dále je potřeba pomocí `docker ps` zjistit jméno kontejneru `web`.

.. code::
  CONTAINER ID   IMAGE                                                  COMMAND                  CREATED             STATUS                       PORTS                                       NAMES
  e194b701484f   docker.elastic.co/kibana/kibana:8.7.0                  "/bin/tini -- /usr/l…"   About an hour ago   Up About an hour             5601/tcp                                    swarm_webamcr_kibana.1.4px4trp5xijig0ejcqz1acg5d
  3402cefa27e7   docker.elastic.co/logstash/logstash:8.7.0              "/usr/local/bin/dock…"   About an hour ago   Up About an hour             5044/tcp, 9600/tcp                          swarm_webamcr_logstash.1.71klpmeb3q272lzcc1pakoqjf
  7b3be0411ce4   aiscr/webamcr:latest                                   "celery -A webclient…"   About an hour ago   Up About an hour (healthy)                                               swarm_webamcr_celery_beat.1.g1zndizd68dfu708230td1tfy
  0cf413cdc3b1   aiscr/webamcr:latest                                   "entrypoint.sh"          About an hour ago   Up About an hour (healthy)                                               swarm_webamcr_web.1.1q93chcyn82p3zdo8iu984uri
  cef2470cc831   prom/prometheus:latest                                 "/bin/prometheus --c…"   About an hour ago   Up About an hour             9090/tcp                                    swarm_webamcr_prometheus.1.osz30uu1pckcogflzh9se7tmd
  5cab21877946   aiscr/webamcr:latest                                   "celery -A webclient…"   About an hour ago   Up About an hour (healthy)                                               swarm_webamcr_celery_worker.1.752w4bsoyableg6x1zdnrcwgr
  850b1657a7a1   aiscr/webamcr-redis:latest                             "/scripts/docker-ent…"   9 hours ago         Up 9 hours (healthy)         6379/tcp                                    swarm_webamcr_redis.1.xslv39mgzz2zudr3z72v4thjy
  f19ba9884667   eeacms/rsync:latest                                    "/docker-entrypoint.…"   9 hours ago         Up 9 hours                                                               swarm_webamcr_sidecar.1.sg7q4p5cyh8l91m0krfdvihxl
  a5231bf3a418   selenium/standalone-chrome-debug:latest                "/opt/bin/entry_poin…"   9 hours ago         Up 9 hours                   4444/tcp, 5900/tcp                          swarm_webamcr_selenium.1.xibwehurioq04rd6xg03754f9
  d18717dde41a   gcr.io/cadvisor/cadvisor:v0.47.2                       "/usr/bin/cadvisor -…"   9 hours ago         Up 9 hours (healthy)         8080/tcp                                    swarm_webamcr_cadvisor.1.24gby7pk1b3348kx4dt1gusoq
  ce64c257ab86   quay.io/prometheuscommunity/postgres-exporter:latest   "/bin/postgres_expor…"   9 hours ago         Up 9 hours                   9187/tcp                                    swarm_webamcr_postgresql_exporter.1.mez0feh4u795p6k1egxqa039x
  86525998ff16   grafana/grafana-enterprise:8.2.0                       "/run.sh"                9 hours ago         Up 9 hours                   3000/tcp                                    swarm_webamcr_grafana.1.5yuq1l4hrvxplx9b2dcghdvzj
  9abf78420bd6   docker.elastic.co/elasticsearch/elasticsearch:8.7.0    "/bin/tini -- /usr/l…"   9 hours ago         Up 9 hours                   9200/tcp, 9300/tcp                          swarm_webamcr_elasticsearch.1.tysx1j4ls70ugef3e9v99ited
  ba0e5ae5d249   portainer/portainer-ce:latest                          "/portainer"             9 hours ago         Up 9 hours                   8000/tcp, 9000/tcp, 9443/tcp                tooling_portainer.1.l0spxbs4cp2cbas9m20cltz4g
  7d5bffc3d20d   aiscr/webamcr-proxy:latest                             "/docker-entrypoint.…"   9 hours ago         Up 9 hours (healthy)         8080/tcp                                    swarm_webamcr_proxy.1.ks8xasq9q09ldme8d1ophkx1n
  79b452459fe9   fcrepo/fcrepo:6.4.0                                    "catalina.sh run"        7 months ago        Up 5 weeks                   0.0.0.0:8081->8080/tcp, :::8081->8080/tcp   fcrepo
  633a10eb8ccf   postgres:12.3                                          "docker-entrypoint.s…"   7 months ago        Up 2 months                  0.0.0.0:5433->5432/tcp, :::5433->5432/tcp   fcrepo-postgres

Např. v tomto případě je název `swarm_webamcr_web.1.1q93chcyn82p3zdo8iu984uri`. Název je pak třeba vložit do příkazu
pro spuštění Django shellu.

.. code::
  docker exec -it swarm_webamcr_web.1.1q93chcyn82p3zdo8iu984uri python3 manage.py shell --settings=webclient.settings.production

Poté je potřeba provést import třídy `FedoraRepositoryConnector`.

.. code:: py
  from core.repository_connector import FedoraRepositoryConnector

Pro migraci konkrétního souboru je potřeba zavolat metodu `save_single_file_from_storage` třídy `FedoraRepositoryConnector`.
Prvním argumentem je ID záznamu, druhým namapovaný adresář v kontejneru. Ve sloužece se soubory by název souboru měl být
ve formátu `ID.ext`, např. `646372.txt`.

.. code:: py
  FedoraRepositoryConnector.save_single_file_from_storage(646372, "/vol/data-migrace")

Pro import většího množství souborů je možné použít metodu `save_files_from_storage`. Prvním argumentem musí být
iterovatelný objekt, např. seznam nebo rozsah.

.. code:: py
  FedoraRepositoryConnector.save_files_from_storage(range(646372, 646373), "/vol/data-migrace")
