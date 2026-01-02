Monitorování aktuálního stavu aplikace
======================================

Systém pro ukládání a analýzu logů se skládá z následujících komponent:
Prometheus, Grafana.

Prometheus
----------

Prometheus je open-source systém pro monitorování a upozorňování. Sbírá
metriky z konfigurovaných cílů v daných intervalech, vyhodnocuje
pravidla upozornění, zobrazuje výsledky a může oznámit nebo eskalovat
upozornění, pokud je detekováno určité chování. Metriky jsou sbírány
pomocí HTTP pull modelu, což znamená, že Prometheus vyhledává aktivní
služby a odebírá od nich data, místo toho, aby je přijímal od nich
pasivně. Prometheus poskytuje svůj vlastní dotazovací jazyk nazvaný
PromQL, který je určený pro vyhledávání a analýzu dat. Také umožňuje
integraci s grafickými nástroji pro vizualizaci dat, jako je například
Grafana.

Grafana
-------

Grafana je otevřený nástroj pro vizualizaci časových řad a monitorování
dat. Je navržen tak, aby uživatelům poskytl možnost snadno vytvářet
dashboards, které agregují data z různých zdrojů do jednoho uživatelsky
přívětivého a interaktivního zobrazení. Grafana podporuje širokou škálu
databází, včetně, ale nejen, Prometheus, Elasticsearch, InfluxDB, MySQL,
PostgreSQL a mnoho dalších. To umožňuje uživatelům kombinovat data z
různých zdrojů na jednom dashboardu.

Monitorování Django aplikace
----------------------------

V systému Grafana jsou připravené dva dashboardy k monitorování
aplikace. Jako zdroj dat je nastaven systém Prometheus.

Níže jsou základní úkony pro práci s dashboardy:

-  Vytvoření nového dashboardu: Klikněte na ikonu plus (+) v navigačním
   panelu a vyberte “Dashboard”.
-  Přidání panelů na dashboard: Panel je základní prvek dashboardu,
   který zobrazuje vizualizaci dat z vybraného zdroje. Klikněte na “Add
   new panel” a vyberte zdroj dat a typ vizualizace.
-  Konfigurace panelů: Můžete upravit nastavení každého panelu, včetně
   dotazu pro zdroj dat, stylu a formátu vizualizace, barev a dalších
   vlastností.
-  Uspořádání panelů: Panely můžete přesouvat a měnit jejich velikost
   podle vašich potřeb. To umožňuje přizpůsobit uspořádání a zobrazení
   dat na dashboardu.
-  Ukládání a sdílení dashboardu: Jakmile jste spokojeni s vaším
   dashboardem, můžete ho uložit. Grafana také umožňuje exportovat
   dashboard do JSON formátu, což umožňuje jeho sdílení a import do jiné
   instance Grafana.
-  Nastavení proměnných: Proměnné jsou pokročilý nástroj, který umožňuje
   vytvářet interaktivní ovládací prvky na dashboardu, jako jsou
   rozevírací seznamy a posuvníky, které mění zobrazení dat na panelech.
-  Nastavení upozornění: Na panelech můžete nastavit upozornění, která
   budou aktivována, když data splní určité podmínky. Upozornění mohou
   být odeslána různými způsoby, včetně e-mailu, Slacku, webhooků a
   dalších.

Předávání dat je zajištěno modulem
`django-prometheus <https://github.com/korfuri/django-prometheus>`__.
