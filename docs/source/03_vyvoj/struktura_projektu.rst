Struktura projektu
==================
 
Níže je přehled hlavních (top-level) adresářů v repozitáři a stručný popis jejich obsahu.

.. list-table::
	 :header-rows: 1
	 :widths: 20 80

	 * - Adresář
		 - Popis
	 * - ``cert/``
		 - TLS certifikáty a související konfigurace pro služby a proxy
	 * - ``docs/``
		 - Dokumentace projektu (Sphinx source, build konfigurační soubory)
	 * - ``elasticsearch/``
		 - Konfigurace a příklady nastavení pro Elasticsearch
	 * - ``fedora/``
		 - Konfigurace a pomocné soubory pro Fedora repository (fcrepo)
	 * - ``kibana/``
		 - Konfigurace a příklady pro Kibana
	 * - ``logstash/``
		 - Konfigurace Logstash pipeline a ukázkové konfigurační soubory
	 * - ``prometheus/``
		 - Konfigurace Prometheus a sběrače (collectors)
	 * - ``proxy/``
		 - Reverzní proxy využívající ``nginx``
	 * - ``redis/``
		 - Redis ``Dockerfile``, konfigurační soubory a healthcheck skripty
	 * - ``scripts/``
		 - Nasazovací skripty, pomocné nástroje a utility pro údržbu
	 * - ``webclient/``
		 - Kód Django aplikace

Poznámka: V kořenovém adresáři se navíc nacházejí konfigurační soubory jako `Dockerfile`, `docker-compose.yml` a různé YAML soubory pro 
lokální a testovací konfigurace.



