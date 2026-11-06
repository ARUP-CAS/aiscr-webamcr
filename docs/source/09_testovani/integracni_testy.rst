.. _integracni-testy:

Integrační testy
=========================

Integrační testy ověřují spolupráci více vrstev aplikace přes skutečné HTTP požadavky.
Test uploadu fotografie prochází cestou nginx → uWSGI → Django. Testy Fedory ověřují přímo
protokol úložiště. Žádný z těchto testů nevyužívá Django test client.
Pro test PAS je nutné na cílové prostředí nasadit ověřovanou verzi aplikace **i proxy**.

Spuštění testů
--------------

Všechny zde popsané integrační testy povoluje společné Django nastavení
``FEDORA_INTEGRATION_TESTS``. Načítá se přes ``get_secret("FEDORA_INTEGRATION_TESTS", False)``
a povolí testy při hodnotě ``true``, ``"true"``, ``1`` nebo ``"1"`` v JSON konfiguraci. Výchozí stav je
``False``; v ``webclient.settings.dev`` je explicitně nastaven na ``True``. Testy čtou
``settings.FEDORA_INTEGRATION_TESTS``, nikoli proměnnou prostředí. Přepínač nenahrazuje
kontrolu cílové adresy ani další potřebné vstupy jednotlivých testů. Nahrazuje původní
přímé čtení přepínače testů Fedory z prostředí. Název ``FEDORA_INTEGRATION_TESTS``
se používá společně i pro PAS integrační test.

Pro vývojové settings není další zapnutí potřeba. Pro ostatní prostředí
v konfiguraci načítané funkcí ``get_secret`` nastavte ``"FEDORA_INTEGRATION_TESTS": true``.
V Dockeru jde o připojený secret ``/run/secrets/db_conf``, lokálně se používá
``webclient/webclient/settings/sample_secrets_db.json``. Konfiguraci s přihlašovacími údaji
nevkládejte do Git. Nastavení se načítá při startu procesu; po změně spusťte nový testovací
proces. Pouhé ``export FEDORA_INTEGRATION_TESTS=1`` nebo ``docker exec -e`` přepínač nezapne.

Povolená prostředí
~~~~~~~~~~~~~~~~~~

Vedle společného přepínače musí pro **všechny integrační testy** platit jedna z podmínek:

* Cíl je přesně **https://amcr-test.aiscr.cz** na standardním HTTPS portu. Na této testovací
  aplikaci lze test spustit i při ``DEBUG=False`` v testovacím procesu i cílové aplikaci.
* Cíl je loopback adresa ``localhost``, ``127.0.0.1`` nebo ``[::1]`` a testovací proces má
  ``DEBUG=True``. Nepoužívejte tunel na produkční aplikaci.

Produkční doména ``amcr.aiscr.cz`` a jiné vzdálené domény jsou odmítnuty **i s DEBUG=True**.
Všechny tři testovací moduly používají společnou kontrolu
``core.tests.integration.require_integration_environment``. Ověří se před vytvořením
velkého PNG i před prvním zápisem do Fedory. Nenastavená cílová adresa nebo lokální cíl
s ``DEBUG=False`` test přeskočí; nepovolená URL způsobí chybu konfigurace.

Cílová adresa aplikace pochází u PAS z ``PAS_UPLOAD_BASE_URL``, u testů Fedory z Django
nastavení ``SITE_URL``. Fedora používá tuto adresu k ověření aplikačního prostředí, samotné
požadavky ale posílá na úložiště z nastavení Fedory. ``SITE_URL`` proto musí pravdivě
odpovídat prostředí, k němuž nakonfigurovaná Fedora patří. URL nesmí obsahovat přihlašovací
údaje, cestu kromě volitelného koncového lomítka, query ani fragment.

PAS API
~~~~~~~

Test ``api/tests/test_upload_foto_integration.py`` pracuje s již běžící aplikací, existujícím
vyhrazeným testovacím nálezem a účtem s oprávněním ``soubor_nahrat_pas`` pro tento nález.
Nezakládá nález ani testovací databázi. Nastavení API musí umožňovat opakovaná volání bez
throttlingu. Pro test používejte vyhrazený nález a účet. Přihlašovací údaje nevkládejte do Git.

Pro PAS musí adresa vést na nginx, například ``http://127.0.0.1:8080``, nikoliv přímo
na Django/uWSGI. Jméno a heslo testovacího účtu se načítají přes Django settings
``INTEGRATION_API_TEST_USERNAME`` a ``INTEGRATION_API_TEST_PASSWORD``, obě přes ``get_secret``
s výchozí prázdnou hodnotou. Pokud chybí některý z údajů, test se přeskočí před přihlášením
a před vytvořením velkého PNG. Chybějící identifikátor nálezu při úplných přihlašovacích
údajích způsobí chybu konfigurace.

Test se jednou přihlásí JSON požadavkem ``POST /api/token-auth/`` s poli ``username``
a ``password``. Z odpovědi HTTP 200 převezme ``token`` a používá jej v Bearer hlavičce
následných uploadů. Lokální HTTPS na loopback adrese při ``DEBUG=True`` používá
neověřovaný vývojový certifikát (ekvivalent ``verify=False``) pro přihlášení i uploady.
Vzdálené HTTPS certifikáty se vždy ověřují. Neúspěšné přihlášení, přesměrování nebo neplatná odpověď způsobí
selhání testu. Heslo, token ani tělo chybové přihlašovací odpovědi test nevypisuje.

Proměnná ``PAS_UPLOAD_BASE_URL`` obsahuje pouze adresu serveru: ``https://amcr-test.aiscr.cz``.
Přihlašovací cesta ``/accounts/login/?next=/`` do ní nepatří. Test používá Bearer token,
nikoli přihlášení přes webový formulář. URL nesmí obsahovat uživatelské údaje, cestu kromě
volitelného koncového lomítka, query ani fragment. Přesměrování HTTP klient nenásleduje,
takže přesměrování z testovací domény na produkci neodešle token ani soubor na produkci.

Příkaz ke spuštění
~~~~~~~~~~~~~~~~~~

V Django konfiguraci povolte společný přepínač a v prostředí nastavte vstupy PAS testu:

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Proměnná
     - Hodnota
   * - ``FEDORA_INTEGRATION_TESTS``
     - ``true`` v JSON konfiguraci přes ``get_secret``; v ``dev.py`` je vždy ``True``
   * - ``PAS_UPLOAD_BASE_URL``
     - ``https://amcr-test.aiscr.cz`` nebo povolená lokální adresa nginx
   * - ``INTEGRATION_API_TEST_USERNAME``
     - Uživatelské jméno testovacího účtu v secret konfiguraci, načtené přes Django settings
   * - ``INTEGRATION_API_TEST_PASSWORD``
     - Heslo testovacího účtu v secret konfiguraci, načtené přes Django settings
   * - ``PAS_UPLOAD_IDENT_CELY``
     - Identifikátor existujícího vyhrazeného testovacího nálezu

Z adresáře ``webclient/`` spusťte se settings modulem nastaveným pro testovací proces::

   python manage.py test api.tests.test_upload_foto_integration \
       --testrunner django.test.runner.DiscoverRunner

Pro lokální cíl přidejte ``--debug-mode``. Standardní Django test runner totiž jinak
přepne ``DEBUG`` na ``False``; test sám DEBUG nezapíná. Pro vzdálenou testovací aplikaci
není ``--debug-mode`` potřeba a DEBUG může zůstat vypnutý.

Fedora — spuštění v Dockeru
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Moduly ``core/tests/test_fedora_integration_child_walk.py`` a
``core/tests/test_fedora_integration_paradata.py`` zapisují přímo do úložiště nastaveného
v Django settings. Nevyžadují ``PAS_UPLOAD_BASE_URL``, přihlašovací údaje API ani existující nález.
Před spuštěním ověřte, že nastavení Fedory ukazuje na **lokální nebo vyhrazenou testovací
instanci**, nikdy na produkční úložiště. Pro zápis používají administrátorské údaje Fedory
ze settings. Před přípravou dočasného záznamu společná pojistka ověří ``SITE_URL``,
``DEBUG`` a přepínač ``FEDORA_INTEGRATION_TESTS``.

Každá metoda vytvoří vlastní dočasný záznam s náhodným identifikátorem ``X-PROTOCOL-…``.
Po testu jej smaže včetně tombstonu. Testy jsou typu ``SimpleTestCase`` a nepotřebují
vytvářet testovací databázi.

V běžícím vývojovém Dockeru spusťte oba moduly::

   docker compose -f docker-compose-dev-local-db-all-containers.yml exec \
       web python manage.py test \
       core.tests.test_fedora_integration_child_walk \
       core.tests.test_fedora_integration_paradata \
       --testrunner django.test.runner.DiscoverRunner --verbosity=2 --debug-mode

Před příkazem povolte přepínač v připojené konfiguraci přes ``get_secret``.
Při úplném Selenium běhu přes ``webclient/run_tests.py`` jsou oba moduly součástí výběru
testů proti Fedoře z ``webclient.settings.dev_test``. Runner přepínač nepřepisuje; používá
jeho hodnotu z Django settings. I v tomto běhu platí
společná kontrola prostředí: pokud je ``SITE_URL`` lokální a testovací proces má
``DEBUG=False``, Fedora testy se přeskočí. Pro jejich ruční lokální spuštění použijte
uvedený příkaz s ``--debug-mode``. Samotný přepínač pravidla adresy a DEBUG neobchází.

Vyhodnocení výsledků testu
--------------------------

Výsledek vypisuje Django test runner do terminálu. U obou modulů Fedory musí být všech
**šest metod** označeno ``ok``, nikoli ``skipped``. Kromě nastavení ``settings.FEDORA_INTEGRATION_TESTS=True``
je tak nutné kontrolovat i skutečný počet spuštěných a přeskočených testů.

U testu PAS je každá kombinace velikosti, způsobu přenosu
a opakování je samostatný subtest. Úspěch vyžaduje úplnou odpověď HTTP ``422``, typ
``application/json`` a očekávaný popis překročené velikosti v poli ``detail``. Odpověď ``413``,
``502``, timeout, neúplná odpověď nebo přesměrování znamenají neúspěch. Jedno volání má limit
600 sekund. Test posílá ``Accept-Language: en`` a ověřuje anglický text chyby.

Požadavky odmítnuté aplikací mají neúspěšný ``ApiRequestLog``; požadavky odmítnuté přímo
nginx jsou pouze v logu proxy. Po běhu lze na vyhrazeném nálezu ověřit, že se nepřipojily
žádné fotografie. Integrační test sám nečte databázi cílové aplikace.

Struktura popisu scénáře
------------------------

Stejně jako u Selenium testů popis obsahuje ID, stručný popis, uživatelskou roli,
předpoklady, kroky, testovací data a očekávané výsledky. Scénáře jsou seskupeny podle aplikací.

PAS API
--------

PAS-HTTP-001 — Nadlimitní fotografie
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Soubor:** ``webclient/api/tests/test_upload_foto_integration.py``.

**Metoda:** ``UploadFotoHttpIntegrationTests.test_oversized_png_returns_422_through_proxy``.

**Popis:** Ověření shodné odpovědi při překročení limitu fotografie v aplikaci i limitu
celého HTTP těla v nginx. Podrobnosti limitů jsou v :doc:`/05_integrace/pas_api`.

**Uživatelská role:** Uživatel s oprávněním ``soubor_nahrat_pas`` pro zvolený nález.

**Předpoklady:** ``settings.FEDORA_INTEGRATION_TESTS=True``, povolené prostředí, nasazená aplikace a proxy, existující
testovací nález, přihlašovací údaje testovacího účtu v secrets a možnost opakovaných požadavků
bez throttlingu. Klient potřebuje
dostatek RAM pro PNG o velikosti až 500 MiB. Server a nginx mohou používat dočasné soubory.

**Kroky:**

#. Ověřit dostupnost jména a hesla z Django settings; při chybějící hodnotě test přeskočit.
#. Přihlásit se přes ``POST /api/token-auth/`` a získat token pro všechny uploady.
#. V paměti vytvořit malé platné PNG a doplnit platný pomocný chunk na požadovanou velikost.
#. Po částech vypočítat SHA-512 nad PNG a sestavit ``Content-Digest``.
#. Odeslat soubor jako multipart požadavek na ``POST /api/pas/nalez/{ident_cely}/upload-foto``.
#. Ověřit kód, JSON typ odpovědi a konkrétní popis chyby.
#. Každý případ zopakovat třikrát s hlavičkou ``Content-Length``. Pro limit + 11 MiB
   navíc ověřit přítomnost i nepřítomnost hlavičky ``Expect: 100-continue``.

**Testovací data:** Velikosti PNG se odvozují od konstanty limitu souboru: limit + 1 bajt,
limit + 5 MiB, limit + 11 MiB a dvojnásobek limitu (aktuálně 250 MiB + 1 bajt, 255 MiB,
261 MiB a 500 MiB). Souborový
limit aplikace se nepřepisuje. PNG vznikají jeden po druhém pouze v paměti klienta, nejsou
součástí Git a klient je neukládá na disk. Digest i přenos se zpracovávají po částech bez další
úplné kopie multipart těla.

**Očekávané výsledky:** Každé volání vrátí HTTP ``422`` a JSON
``{"detail": "The uploaded file exceeds the maximum allowed size."}``. Soubor nad 250 MiB,
jehož celé multipart tělo nepřesahuje 260 MiB, odmítne aplikace; tělo nad 260 MiB odmítne nginx.
Žádný z případů nesmí skončit HTTP ``413``, HTTP ``502`` ani timeoutem.


Fedora
------

FEDORA-HTTP-001 — Průchod potomky souboru
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Soubor:** ``webclient/core/tests/test_fedora_integration_child_walk.py``.

**Třída:** ``FedoraChildWalkIntegrationTest``.

**Popis:** Ověření protokolu Fedory při přejmenování souboru a sběru jeho vnořených distribucí
s paradaty pro kopírování při změně identifikátoru. Scénář pochází z PR
`#4197 <https://github.com/ARUP-CAS/aiscr-webamcr/pull/4197>`__.

**Uživatelská role:** Administrátor testovací Fedory z Django settings.

**Předpoklady:** ``settings.FEDORA_INTEGRATION_TESTS=True``, dostupná neprodukční Fedora a oprávnění vytvářet,
číst, přejmenovávat a mazat dočasné zdroje včetně tombstonů.

**Kroky a testovací data:**

#. Vytvořit dočasný záznam, kontejner souboru a binární zdroje ``orig``, ``ocr/alto-xml``
   a ``paradata/ocr/alto-xml`` s původním základem názvu ``CTX900000001A``.
#. Metodou ``test_rename_reaches_every_binary_child`` přejmenovat názvy na základ
   ``CTX900000001B`` a načíst RDF metadata každého binárního potomka.
#. V samostatné metodě ``test_collect_returns_distributions_and_paradata_with_their_paths``
   načíst potomky pro kopírování včetně cest, názvů, MIME typů a obsahu.
#. Po každé metodě odstranit dočasný záznam a jeho tombstone.

**Očekávané výsledky:** Přejmenování dosáhne všech tří binárních potomků včetně vnořených
kontejnerů a aktualizuje jejich ``ebucore:filename``. Sběr vrátí distribuci a paradata se
správnými relativními cestami, názvy, MIME typy a obsahem; původní ``orig`` vynechá.

FEDORA-HTTP-002 — Zjišťování paradat souboru
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Soubor:** ``webclient/core/tests/test_fedora_integration_paradata.py``.

**Třída:** ``FedoraParadataIntegrationTest``.

**Popis:** Ověření ``has_paradata`` a ``paradata_exists`` proti skutečnému chování RDF
kontejnerů, binárních zdrojů, HTTP 404 a HTTP 410 ve Fedoře. Scénář pochází z PR #4197.

**Uživatelská role:** Administrátor testovací Fedory z Django settings.

**Předpoklady:** Stejné jako u FEDORA-HTTP-001.

**Kroky a testovací data:**

#. Vytvořit dočasný záznam a dva soubory s ``orig``. Prvnímu přidat distribuci ``ocr/alto-xml``
   a binární paradata ``paradata/ocr/alto-xml``; druhý ponechat bez paradat.
#. ``test_has_paradata_finds_the_paradata_container`` ověří soubor s RDF kontejnerem paradat.
#. ``test_has_paradata_is_false_for_a_file_without_paradata`` ověří soubor bez paradat.
#. ``test_has_paradata_is_false_after_the_paradata_were_deleted`` smaže kontejner paradat
   a ověří stav po vytvoření tombstonu.
#. ``test_paradata_exists_only_for_distributions_with_paradata`` ověří distribuci
   ``ocr/alto-xml`` s paradaty a ``orig`` bez paradat.
#. Po každé metodě odstranit dočasný záznam a jeho tombstone.

**Očekávané výsledky:** Existující RDF kontejner se rozpozná jako paradata, přestože jeho
``fcr:metadata`` vrací 404. Chybějící kontejner (404) ani smazaný kontejner (410) nejsou
považovány za existující paradata. ``paradata_exists`` vrátí ``True`` pro ``ocr/alto-xml``
a ``False`` pro ``orig``.
