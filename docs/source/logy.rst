Ukládání a analýza logů
=======================

Systém pro ukládání a analýzu logů se skládá z následujících komponent:
Logstash, Elasticsearch, Kibana.

Logstash
--------

Logstash je otevřený softwarový nástroj pro příjem, analýzu a
předzpracování logovacích dat. Logstash je schopný shromažďovat data z
různých zdrojů a v různých formátech. Tato data může dále transformovat
a odeslat do různých cílových systémů pro další zpracování a analýzu.
Logstash je zvlášť užitečný pro shromažďování logů a událostí v reálném
čase. Při zpracování dat umí provádět různé operace jako filtraci, výběr
specifických atributů, přidávání dalších informací a transformaci dat do
jiných formátů.

Elasticsearch
-------------

Elasticsearch je vysoce škálovatelný open-source full-textový
vyhledávací a analytický nástroj. Je schopen uložit, prohledávat a
analyzovat velké množství dat v reálném čase. Je optimalizován pro
distribuované prostředí a podporuje mnoho datových typů, od textu až po
geografické polohy. Jedním z klíčových vlastností Elasticsearch je jeho
schopnost provádět komplexní vyhledávání pomocí dotazů, které mohou
zahrnovat plnotextové vyhledávání, vyhledávání podle rozsahu a fuzzy
vyhledávání. Tento nástroj je často používán v aplikacích, které
vyžadují komplexní vyhledávací funkce, jako jsou webové vyhledávače,
logovací a monitorovací systémy, analýza dat, a další.

Kibana
------

Kibana je open-source nástroj pro vizualizaci dat, který umožňuje
uživatelům prozkoumávat a vizualizovat data uložená v Elasticsearch.
Kibana poskytuje uživatelské rozhraní pro Elasticsearch a umožňuje
uživatelům vytvářet různé druhy vizualizací, včetně grafů, tabulek, map
a dalších. Umožňuje také tvorbu interaktivních dashboardů, které mohou
zobrazovat mnoho různých vizualizací najednou a mohou být upraveny pro
různé potřeby. Kibana také poskytuje nástroje pro správu a monitorování
Elasticsearch clusterů, stejně jako nástroje pro prohlížení a analýzu
logů a událostí, které byly shromážděny a zpracovány pomocí Logstash. V
kombinaci s ostatními nástroji Elastic Stacku (Elasticsearch a
Logstash), Kibana nabízí silný nástroj pro shromažďování, zpracování,
vyhledávání a vizualizaci dat.

Konfigurace systému
-------------------

Logové zprávy jsou posílány z Django aplikace do Logstash přes TCP
protokol s využitím modulu
`python-logstash <https://github.com/vklochan/python-logstash>`__.
Nastavení je v souboru ``base.py``.

.. code:: py

   {
       "logstash": {
           "level": "DEBUG",
           "class": "logstash.TCPLogstashHandler",
           "host": "logstash",
           "port": 5959,
           "version": 1,
           "message_type": "logstash",
           "fqdn": false
       }
   }

Níže je konfigurace systému Logstash.

::

   input {
       tcp {
           port => 5959
           codec => json
       }
   }

   output {
       elasticsearch {
           hosts => ["IP:9200"]
           index => "amcr"
           password => "CHANGE_ME"
           user => "amcr"
       }
   }

Input (vstup): - tcp: Tato část konfigurace definuje TCP jako zdroj dat.
TCP je protokol, který se používá pro přenos dat z Django (viz výše). -
port => 5959: Tato část konfigurace určuje, že Logstash bude naslouchat
na portu 5959 pro příchozí data. - codec => json: Tato část konfigurace
určuje, že příchozí data budou ve formátu JSON.

Output (výstup): - elasticsearch: Tato část konfigurace definuje
Elasticsearch jako místo, kam Logstash pošle zpracovaná data. - hosts =>
[“IP:9200”]: Toto určuje, že Logstash pošle zpracovaná data na adresu
Elasticsearch hostitele, který je na IP adrese IP a na portu 9200. Je
doporučeno používat IP adresy serverů v síti (tj. začínající 192.168.) -
index => “amcr”: Toto určuje, že zpracovaná data budou uložena v
Elasticsearch indexu nazvaném “amcr”. - user => “amcr” a password =>
“CHANGE_ME”: Tyto části konfigurace definují jméno uživatele a heslo,
které Logstash použije pro autentizaci u Elasticsearch.

.. _elasticsearch-1:

Elasticsearch
-------------

Nastavení Elasticsearch je součástí docker-compose.yml souborů.

-  discovery.type=single-node: Toto nastavení říká Elasticsearch, že se
   jedná o jediný uzel (node).
-  ES_JAVA_OPTS=-Xms750m -Xmx750m: Tyto Java nastavení definují
   minimální (-Xms) a maximální (-Xmx) velikost paměti heap, kterou může
   Elasticsearch využít. V tomto případě je nastaveno na 750 megabajtů.
-  http.host=0.0.0.0: Toto nastavení definuje IP adresu, na které bude
   Elasticsearch naslouchat příchozím HTTP spojením. Hodnota 0.0.0.0
   znamená, že Elasticsearch bude naslouchat na všech síťových
   rozhraních.
-  xpack.security.enabled=true: Toto nastavení aktivuje X-Pack Security,
   což je součást Elastic Stacku, která poskytuje různé bezpečnostní
   funkce, jako je autentizace, autorizace, šifrování komunikace a
   další.
-  XPACK_MONITORING_ENABLED=false: Toto nastavení deaktivuje X-Pack
   Monitoring. Monitoring je další součást Elastic Stacku, která
   poskytuje nástroje pro sledování výkonu a zdraví Elasticsearch
   clusteru. Cílem nastavení je snížit zatížení systému.

.. _kibana-1:

Kibana
------

Níže je konfigurace systému Kibana

::

   server.host: "0.0.0.0"
   server.shutdownTimeout: "5s"
   elasticsearch.hosts: [ "http://elasticsearch:9200" ]

   monitoring.ui.container.elasticsearch.enabled: true
   monitoring.ui.container.logstash.enabled: true

   elasticsearch.username: user
   elasticsearch.password: CHANGE_ME

-  ``server.host: "0.0.0.0"``: Toto nastavení definuje IP adresu, na
   které bude Kibana naslouchat příchozím spojením. Hodnota 0.0.0.0
   znamená, že Kibana bude naslouchat na všech dostupných síťových
   rozhraních.
-  ``server.shutdownTimeout: "5s"``: Toto nastavení definuje, kolik času
   má Kibana k dispozici pro bezpečné ukončení své činnosti před tím,
   než je násilně ukončena. V tomto případě je to nastaveno na 5 sekund.
-  ``elasticsearch.hosts: [ "http://elasticsearch:9200" ]``: Toto
   nastavení definuje adresy uzlů Elasticsearch, ke kterým se Kibana
   připojí. V tomto případě je nastavena jedna adresa:
   http://elasticsearch:9200.
-  ``monitoring.ui.container.elasticsearch.enabled: true`` a
   ``monitoring.ui.container.logstash.enabled: true``: Tyto dvě
   nastavení aktivují monitorování kontejnerů Elasticsearch a Logstash v
   rámci uživatelského rozhraní Kibany. Toto umožňuje uživatelům
   sledovat výkon a zdraví těchto služeb přímo z Kibany.
-  ``elasticsearch.username: kibana_system`` a
   ``elasticsearch.password: CHANGE_ME``: Tyto dva řádky definují jméno
   a heslo, které Kibana použije pro připojení k Elasticsearch. Toto je
   součást autentizace a je důležité pro zabezpečení dat.

Nasazení systému
----------------

Po nasazení je potřeba sputit následující příkaz a nastavit hesla
systémových účtů.

::

   sudo docker exec -t -i $(sudo docker ps -q -f name=swarm_webamcr_elasticsearch) bin/elasticsearch-reset-password -u elastic -i --url http://localhost:9200

::

   sudo docker exec -t -i $(sudo docker ps -q -f name=swarm_webamcr_elasticsearch) bin/elasticsearch-reset-password -u kibana_system -i --url http://localhost:9200

Po nastavení je nutné restartovat kontejner Kibana a vytvořit index
``amcr`` s využitím konzole (konzoli lze otevřít kliknutím na odkaz Dev
Tool na titulní stránce).

::

   PUT /amcr
   {
     "settings": {
       "number_of_shards": 1,
       "number_of_replicas": 1
     }
   }

Dále je nutné vytvořit roli ``amcr`` a uživatele ``amcr`` a nastavit mu
stejné heslo jako v konfiguračním souboru ``logstash.conf``.

Vytvoření role: Klikněte na ikonu “Management” (správa) v hlavním
navigačním panelu. V sekci Stack Management vyberte možnost “Security” a
přejděte na Roles (role). Dále klikněte na tlačítko “Create role”. Do
pole “Role name” zadejte název nové role a nastavte oprávnění. Nakonec
klikněte na tlačítko “Create role” pro uložení role.

Vytvoření uživatelského účtu: Klikněte na “Users” a poté na tlačítko
“Create user”. Do polí “Username” a “Password” zadejte jméno uživatele a
heslo. Můžete také zadat “Full name”, “Email” a “Password confirmation”.
Také můžete rozhodnout, zda chcete, aby uživatel musel změnit heslo při
příštím přihlášení. V sekci “Roles” můžete vybrat jednu nebo více rolí,
které chcete uživateli přiřadit. Tyto role určují, jaká oprávnění má
uživatel v Elasticsearch a Kibana. Nakonec klikněte na tlačítko “Create
user” pro uložení uživatele.

Práce s obrazovkou Discover
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Obrazovka “Discover” v Kibana je nástroj, který umožňuje prozkoumávat a
hledat data uložená v Elasticsearch. Tato obrazovka je často využívána
pro zkoumání dat v reálném čase, hledání specifických záznamů, analýzu
trendů a pro ladění aplikací.

Při použití obrazovky “Discover” můžete provést následující akce: -
Výběr indexu: Nejprve musíte vybrat index, který chcete prozkoumat. To
můžete udělat v pravém horním rohu obrazovky. Vyberte index ``amcr``. -
Prohlížení a hledání dat: Poté můžete procházet dokumentu ve zvoleném
indexu. Každý záznam představuje jeden logový záznam. - Filtrace dat:
Můžete vytvářet filtry, které omezí zobrazené záznamy na ty, které
splňují určité kritéria. - Prohlížení detailů záznamu: Kliknutím na
záznam můžete zobrazit jeho detaily, včetně všech jeho polí a jejich
hodnot. - Výběr časového období: V horní části obrazovky můžete vybrat
časové období, pro které chcete data zobrazit. - Vytváření a ukládání
vyhledávání: Po vytvoření vyhledávání, které chcete znovu použít, můžete
toto vyhledávání uložit pro budoucí použití.

Dashboardy
~~~~~~~~~~

Dashboardy v Kibana představují kolekce vizualizací a interaktivních
ovládacích prvků, které jsou uspořádány na jedné stránce a slouží k
monitoringu, analýze a vizualizaci dat z Elasticsearch.

Při práci s dashboardy můžete provádět následující kroky: - Vytvoření
nového dashboardu: Klikněte na “Dashboard” v hlavním navigačním panelu a
pak na “Create new dashboard”. - Přidání vizualizací na dashboard:
Klikněte na “Add” a vyberte vizualizaci, kterou chcete přidat. Můžete
přidat jakékoli vizualizace, které jste vytvořili v Kibana, včetně
grafů, map, tabulek a dalších. - Úprava a uspořádání prvků na
dashboardu: Prvky na dashboardu můžete přesouvat, měnit jejich velikost
a upravovat jejich nastavení podle vašich potřeb. - Ukládání a sdílení
dashboardu: Jakmile jste s dashboardem spokojeni, můžete ho uložit pro
budoucí použití. Také ho můžete sdílet s ostatními členy svého týmu nebo
vytvořit URL, které lze vložit do jiných webových stránek. - Využití
filtrů a interaktivních ovládacích prvků: Dashboardy mohou obsahovat
interaktivní ovládací prvky, jako jsou rozevírací seznamy nebo
posuvníky, které umožňují filtrovat a prozkoumávat data na různých
úrovních granularit. - Zobrazení dat v reálném čase: Některé dashboardy
mohou být nastaveny tak, aby zobrazovaly data v reálném čase. To je
užitečné pro monitorování výkonu systému, logování událostí nebo
jakékoliv jiné aktivity, které vyžadují okamžité zobrazení dat.

Vyčištění databáze
~~~~~~~~~~~~~~~~~~

Pokud je v databázi příliš mnoho záznamů, je možné uvolnit místo
smazáním všech záznamů s úrovní DEBUG.

::

   POST /amcr/_delete_by_query
   {
     "query": { 
       "term": {
         "level.keyword": "DEBUG"
       }
     }
   }


Kontrola stavu kontejneru
-------------------------

Stav kontejneru může být zkontrolován pomocí příkazu

::

   docker inspect --format='{{json .State.Health}}' <container_name_or_id>

Stav služby ve swarm módu může být zkontrolován příkazem

::
   docker service ps <service_name> --no-trunc
