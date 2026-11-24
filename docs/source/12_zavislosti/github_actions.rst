GitHub Actions: závislosti a důvěra
========================================

Externí akce v ``.github/workflows/`` odkazují na úplný, 40znakový commit SHA.
Na stejném řádku zůstává komentář úplné verze, například ``# v7.0.1``.
Pravidlo platí také pro akce organizací ``actions`` a ``github``. Lokální
volání ``./.github/workflows/publish_images.yml`` používá obsah stejné revize
repozitáře. SHA identifikuje kód akce; neověřuje bezpečnost tohoto kódu ani
neměnnost stažených nástrojů, kontejnerů, databází nebo síťových služeb.

Inventář závislostí
----------------------------------------

Tabulku sestavuje ``docs/generate_module_docs.py`` z aktivních YAML položek
``uses`` v jobech a krocích workflow. Zahrnuje GitHub i third-party akce;
komentované kroky, shellový text a lokální volání vynechává. Opakovaná volání
stejného vydání sdružuje, rozdílné verze téže akce ponechává samostatně.
Zdrojem verze a commitu jsou workflow, nikoli ručně udržovaný seznam.

.. BEGIN GENERATED GITHUB ACTIONS

.. list-table:: Aktivní externí GitHub Actions
   :header-rows: 1

   * - Akce
     - Vlastník
     - Vydání
     - Commit a zdroj
     - Workflow
   * - ``actions/attest``
     - `actions <https://github.com/actions>`__
     - `v4.2.2 <https://github.com/actions/attest/releases/tag/v4.2.2>`__
     - `1e69f48acb82d1966a394da916b4c1698aa569d6 <https://github.com/actions/attest/tree/1e69f48acb82d1966a394da916b4c1698aa569d6>`__
     - ``.github/workflows/publish_images.yml:205``, ``.github/workflows/publish_images.yml:216``
   * - ``actions/attest-build-provenance``
     - `actions <https://github.com/actions>`__
     - `v4.2.2 <https://github.com/actions/attest-build-provenance/releases/tag/v4.2.2>`__
     - `4d101475d8b20a2381f78447822ac1eab6504dd8 <https://github.com/actions/attest-build-provenance/tree/4d101475d8b20a2381f78447822ac1eab6504dd8>`__
     - ``.github/workflows/publish_images.yml:179``, ``.github/workflows/publish_images.yml:187``
   * - ``actions/cache``
     - `actions <https://github.com/actions>`__
     - `v6.1.0 <https://github.com/actions/cache/releases/tag/v6.1.0>`__
     - `55cc8345863c7cc4c66a329aec7e433d2d1c52a9 <https://github.com/actions/cache/tree/55cc8345863c7cc4c66a329aec7e433d2d1c52a9>`__
     - ``.github/workflows/pre_commit.yml:126``, ``.github/workflows/pre_commit.yml:135``
   * - ``actions/checkout``
     - `actions <https://github.com/actions>`__
     - `v7.0.1 <https://github.com/actions/checkout/releases/tag/v7.0.1>`__
     - `3d3c42e5aac5ba805825da76410c181273ba90b1 <https://github.com/actions/checkout/tree/3d3c42e5aac5ba805825da76410c181273ba90b1>`__
     - ``.github/workflows/deployment.yml:66``, ``.github/workflows/new-version.yml:211``, ``.github/workflows/new-version.yml:70``, ``.github/workflows/pre_commit.yml:111``, ``.github/workflows/publish_images.yml:68``, ``.github/workflows/run-tests.yml:75``
   * - ``actions/create-github-app-token``
     - `actions <https://github.com/actions>`__
     - `v3.4.0 <https://github.com/actions/create-github-app-token/releases/tag/v3.4.0>`__
     - `f418cff399f7aef4c2f0ad47e25ca7a6abbdd6fc <https://github.com/actions/create-github-app-token/tree/f418cff399f7aef4c2f0ad47e25ca7a6abbdd6fc>`__
     - ``.github/workflows/new-version.yml:203``, ``.github/workflows/new-version.yml:62``, ``.github/workflows/pre_commit.yml:279``
   * - ``actions/github-script``
     - `actions <https://github.com/actions>`__
     - `v9.0.0 <https://github.com/actions/github-script/releases/tag/v9.0.0>`__
     - `3a2844b7e9c422d3c10d287c895573f7108da1b3 <https://github.com/actions/github-script/tree/3a2844b7e9c422d3c10d287c895573f7108da1b3>`__
     - ``.github/workflows/pre_commit.yml:338``
   * - ``actions/setup-python``
     - `actions <https://github.com/actions>`__
     - `v7.1.0 <https://github.com/actions/setup-python/releases/tag/v7.1.0>`__
     - `6d4fd22b20465ccc0f7354476588e8df7c9ca0e0 <https://github.com/actions/setup-python/tree/6d4fd22b20465ccc0f7354476588e8df7c9ca0e0>`__
     - ``.github/workflows/pre_commit.yml:120``
   * - ``actions/upload-artifact``
     - `actions <https://github.com/actions>`__
     - `v7.0.2 <https://github.com/actions/upload-artifact/releases/tag/v7.0.2>`__
     - `cf430e030ddbb5b0abf93d22962f4752f3646cd9 <https://github.com/actions/upload-artifact/tree/cf430e030ddbb5b0abf93d22962f4752f3646cd9>`__
     - ``.github/workflows/run-tests.yml:221``
   * - ``aquasecurity/trivy-action``
     - `aquasecurity <https://github.com/aquasecurity>`__
     - `v0.36.0 <https://github.com/aquasecurity/trivy-action/releases/tag/v0.36.0>`__
     - `ed142fd0673e97e23eac54620cfb913e5ce36c25 <https://github.com/aquasecurity/trivy-action/tree/ed142fd0673e97e23eac54620cfb913e5ce36c25>`__
     - ``.github/workflows/publish_images.yml:196``, ``.github/workflows/publish_images.yml:227``
   * - ``docker/build-push-action``
     - `docker <https://github.com/docker>`__
     - `v7.4.0 <https://github.com/docker/build-push-action/releases/tag/v7.4.0>`__
     - `c3c9e263c25d99ce0380d002d59b67737d91b0dc <https://github.com/docker/build-push-action/tree/c3c9e263c25d99ce0380d002d59b67737d91b0dc>`__
     - ``.github/workflows/docker_scout.yml:57``, ``.github/workflows/publish_images.yml:121``
   * - ``docker/login-action``
     - `docker <https://github.com/docker>`__
     - `v4.8.0 <https://github.com/docker/login-action/releases/tag/v4.8.0>`__
     - `8aa5831fb8d48d8f76594c7ddde61ae58019f550 <https://github.com/docker/login-action/tree/8aa5831fb8d48d8f76594c7ddde61ae58019f550>`__
     - ``.github/workflows/docker_scout.yml:34``, ``.github/workflows/publish_images.yml:87``, ``.github/workflows/publish_images.yml:94``
   * - ``docker/metadata-action``
     - `docker <https://github.com/docker>`__
     - `v6.2.0 <https://github.com/docker/metadata-action/releases/tag/v6.2.0>`__
     - `dc802804100637a589fabce1cb79ff13a1411302 <https://github.com/docker/metadata-action/tree/dc802804100637a589fabce1cb79ff13a1411302>`__
     - ``.github/workflows/docker_scout.yml:43``, ``.github/workflows/publish_images.yml:101``
   * - ``docker/scout-action``
     - `docker <https://github.com/docker>`__
     - `v1.30.0 <https://github.com/docker/scout-action/releases/tag/v1.30.0>`__
     - `b265cd48f8a1451d2680815b3e8dc4ed65ee16e7 <https://github.com/docker/scout-action/tree/b265cd48f8a1451d2680815b3e8dc4ed65ee16e7>`__
     - ``.github/workflows/docker_scout.yml:73``
   * - ``docker/setup-buildx-action``
     - `docker <https://github.com/docker>`__
     - `v4.4.1 <https://github.com/docker/setup-buildx-action/releases/tag/v4.4.1>`__
     - `f87e5991a6d7451dcb8d9637bfbc97413f497069 <https://github.com/docker/setup-buildx-action/tree/f87e5991a6d7451dcb8d9637bfbc97413f497069>`__
     - ``.github/workflows/docker_scout.yml:30``, ``.github/workflows/publish_images.yml:84``
   * - ``github/codeql-action/upload-sarif``
     - `github <https://github.com/github>`__
     - `v4.39.4 <https://github.com/github/codeql-action/releases/tag/v4.39.4>`__
     - `1bd86f2fdb4b86187fa4059f16f31a3202acc9ea <https://github.com/github/codeql-action/tree/1bd86f2fdb4b86187fa4059f16f31a3202acc9ea/upload-sarif>`__
     - ``.github/workflows/publish_images.yml:236``
   * - ``sigstore/cosign-installer``
     - `sigstore <https://github.com/sigstore>`__
     - `v4.1.3 <https://github.com/sigstore/cosign-installer/releases/tag/v4.1.3>`__
     - `756fe2d284c7292c4e9b62c8a28f1e5629c59532 <https://github.com/sigstore/cosign-installer/tree/756fe2d284c7292c4e9b62c8a28f1e5629c59532>`__
     - ``.github/workflows/publish_images.yml:167``

.. END GENERATED GITHUB ACTIONS

Ponechané third-party integrace
----------------------------------------

* ``docker/login-action`` (vlastník ``docker``) přijímá registry tokeny.
  ``docker/setup-buildx-action`` připravuje builder,
  ``docker/metadata-action`` vytváří tagy a metadata a
  ``docker/build-push-action`` sestavuje a publikuje image. Tyto integrace
  Dockeru poskytují potřebnou práci s registry a buildy; publikační job má
  oprávnění ``packages: write``. SHA wrapperů nepinuje Buildx, builder image
  ani vstupní image.
* ``docker/scout-action`` (vlastník ``docker``) zajišťuje existující přehled
  bezpečnosti image a komentáře s oprávněním ``pull-requests: write``.
  Využívá registry a stažené nástroje služby Docker Scout.
* ``aquasecurity/trivy-action`` (vlastník ``aquasecurity``) poskytuje oba
  potřebné výstupy, SBOM a SARIF. Ponechání upstream wrapperu zachovává jeho
  instalační a cache logiku bez vlastní implementace instalátoru CLI. Job má
  mimo jiné ``id-token: write`` a ``packages: write``; stažený Trivy a jeho
  databáze zůstávají dalšími závislostmi. Verze wrapperu není verzí Trivy CLI.
* ``sigstore/cosign-installer`` (vlastník ``sigstore``) zajišťuje instalaci
  nástroje pro podepisování image v GHCR a Docker Hubu. Upstream instalátor
  obsahuje bootstrap kontrolní součty a ověření dalších vydání, které by jinak
  musel zajišťovat vlastní instalátor. Zůstává důvěra v Sigstore, OIDC a registry;
  SHA instalátoru sama neověřuje výsledný podpis image.

Aktualizace a obnova dokumentace
----------------------------------------

Dependabot používá týdenní ekosystém ``github-actions`` s cílem ``test``
a skupinami ``docker-actions`` a ``attest``. Aktualizace prochází běžným
lidským review závislostí. GitHub popisuje aktualizaci SHA i komentáře verze
v `podporovaných ekosystémech Dependabotu <https://docs.github.com/en/code-security/reference/supply-chain-security/supported-ecosystems-and-repositories>`_.

Inventář obnovuje existující pre-commit hook ``generate-module-docs`` společně
s další dokumentací závislostí, bez síťových volání a přihlašovacích údajů:

.. code-block:: bash

   pre-commit run generate-module-docs --all-files

Generátor také kontroluje tvar SHA a verzního komentáře; při změně dokumentace
vrátí standardní nenulový kód hooku. Změněné soubory projdou běžnou kontrolou
diffu a dalším spuštěním hooku. Ručně upravovaný text mimo generovaný blok
zachovává. Implementace parseru i inventáře je v ``docs/generate_module_docs.py``;
regresní testy jsou v ``scripts/test_pre_commit_actions_trust.py`` a
``scripts/test_generate_github_actions.py`` a spouští je existující CI test job.

Sdílené CI dokumentace vynechává větve Dependabotu a dalších botů. Inventář
se proto nemusí změnit už v prvním diffu Dependabot PR; obnovuje se při běžném
spuštění pre-commit nebo existujícím obnovení dokumentace závislostí při vydání.
Nevzniká samostatný údržbový workflow ani další pravidelná revize.

Při ručním přidání či opravě pinu lze zjistit commit vydání pomocí
``gh api repos/OWNER/REPO/git/ref/tags/vX.Y.Z``. Je-li ``object.type`` rovno
``tag``, pokračujte přes URL tagového objektu až k typu ``commit``.
SHA anotovaného tagu ani souboru není commit. Alternativou je rozbalený záznam
``^{}`` ve výstupu ``git ls-remote``. Zapište ověřený commit a odpovídající
``# vX.Y.Z`` na stejný řádek; zachovejte subpath a shodné odkazy na stejné vydání.
Lokální kontrola neověřuje existenci commitu v upstream repozitáři.

Relevantní nekompatibilita nebo bezpečnostní omezení patří k vysvětlení dané
aktualizace. Pin wrapperu nepinuje všechny jeho runtime závislosti a Dependabot
nesleduje libovolné verze nástrojů zadané přes ``with: version``.

Nativní SSH agent pro testy na DEV
--------------------------------------

``Run tests`` spouští nativní ``ssh-agent`` a načítá existující
``SSH_PRIVATE_KEY_SERVER_DEV`` pomocí ``ssh-add`` po odstranění CR znaků.
Klíč je předán proměnnou prostředí pouze inicializačnímu kroku, bez shellového
trasování a bez zápisu do artefaktů. Mezi kroky se přes ``GITHUB_ENV`` přenášejí
jen ``SSH_AUTH_SOCK`` a ``SSH_AGENT_PID``. Proto agent slouží pozdějšímu SSH
i kroku pro získání výsledků aktuálního pokusu. Neúspěšná inicializace
uklidí agenta ihned; krok s ``always()`` zajišťuje úklid po použití agenta
i po chybě SSH/SCP. Následuje odpojení VPN a kontrola výsledku testů.
Ověření hostitele přes existující ``known_hosts`` a VPN se nemění.

Stažený ``test_summary.env`` se čte pouze jako data: musí obsahovat právě
jeden záznam ``PASSED`` a jeden ``FAILED`` s nezáporným celočíselným počtem.
Chybějící, duplicitní, neznámé či neplatné záznamy a binární obsah způsobí
neúspěch před zápisem výstupů a souhrnné tabulky. Obsah souboru se nespouští
jako shell. Konce řádků LF i CRLF a chybějící poslední nový řádek jsou
podporované; úvodní nuly se odstraní před předáním čísel do dalších kroků.
Úklid agenta proběhne i při odmítnutí souhrnu.

Workflow nasazení předává privátní klíč pouze svému kroku SSH. Agent se v něm
načte, použije a ukončí pomocí EXIT trapu při úspěchu i chybě načtení klíče
nebo vzdáleného příkazu. Jeho stav se nepřenáší do dalších kroků a úklid
nezmění původní neúspěšný výsledek na úspěch.

Tag nasazení a vstupy testů se načítají z proměnných prostředí kroku.
Před připojením VPN se ověří formát tagu, režim testů, boolean nasazení
a číselný obsah každého zadaného ``test_cislo``; režim ``konkretni`` číslo
vyžaduje. Vstupy i názvy referencí se předávají jako argumenty se samostatným
uvozením pro vzdálený shell. Tělo vzdáleného testovacího skriptu zůstává
statické; lokální uvozovky samy neřeší další interpretaci příkazu přes SSH.

Neinteraktivní příkazy nasazení a testování mají uzavřený standardní vstup.
Nemohou tak přečíst zbytek skriptu předávaného vzdálenému Bash přes stdin.
Regresní test používá náhradu nasazení, která stdin skutečně spotřebuje,
a kontroluje následné spuštění všech režimů i zastavení po chybě nasazení.

Runner ověřuje návratový kód migrace i testovacího procesu a před vyhodnocením
dočte oba výstupní proudy. Chybějící či rozporný souhrn, chyba startu a nulový
běžný běh znamenají chybu. Jen režim neúspěšných testů s platným předchozím
vstupem a prázdným výběrem smí skončit jako výslovné ``no-tests``. Chybějící
tabulka nebo nenalezené číslo testu jsou chyby, nikoli úspěšné prázdné běhy.

Vlastní diagnostika runneru uvádí ověřenou identitu pokusu a pevně pojmenovanou
fázi selhání. Nevypisuje nakonfigurovaný kořen výsledků ani nezpracovaný text
výjimky; totéž platí pro zprávu v ``outcome.json``. Pokud selže i zveřejnění
chybového výsledku, runner vrátí neúspěch a pevnou zprávu bez tracebacku.
Zachycený výstup samotných testů se tím nefiltruje.

Každý pokus má identitu ``<github.run_id>-<github.run_attempt>`` a vlastní
adresář ``runs/<pokus>/`` ve stávajícím svazku výsledků. Samostatné spuštění
vygeneruje lokální identitu. Runner předá adresář testovacímu nastavení přes
``AMCR_TEST_OUTPUT_DIR``; souhrn, nové tabulky a výstup tak patří jedinému
pokusu. Předchozí ``results.xlsx`` zůstává vstupem výběru. Po dokončení se
kompatibilní vstup pro příští výběr obnoví; selektivní běh neztratí ostatní
známé testy. Záznam ``outcome.json`` s identitou, režimem, stavem a otisky
souborů se atomicky zveřejní poslední. Neúplný adresář není hotovým výsledkem.

Workflow stáhne záznam očekávaného pokusu, ověří jeho schéma a teprve potom
stahuje přesně pojmenované soubory. Před zveřejněním počtů ověří jejich otisky
a vzájemný soulad. Staré soubory bez identity, jiné pokusy a chybějící či
smíšené artefakty jsou odmítnuty. Výsledkový krok běží i po chybě testů,
aby uchoval aktuální diagnostiku; neúspěch tím nezmění na úspěch. Artefakt
obsahuje jen ověřený aktuální balík, u ``no-tests`` žádnou starou tabulku.

Povinné operace sestavení, stažení image, odstranění existujícího stacku,
nasazení a klonování databáze propagují neúspěch přes všechny obaly až do
workflow. PTY obal používá ``script --return`` a nepředává procesu zbytek
vzdáleného skriptu na stdin. Ověřená absence starého stacku je při úklidu
přípustná; chyba jeho inspekce není totéž. Chyba volitelné kompakce paměti
zůstává varováním. Záznam posledního úspěšně nasazeného tagu se změní až po
úspěchu povinné přípravy a kontroly připravenosti. Automatický rollback se
tím nezavádí.

Oba CI nasazovací skripty používají společnou kontrolu připravenosti přes
Python 3 a jeho standardní knihovnu na nasazovacím hostiteli. Očekávané služby
odvodí z Compose konfigurace sloučené Docker CLI. Kontrolují jen cílový stack,
počty a stav požadovaných úloh, probíhající či neúspěšný rollout a skutečné
zdraví dostupných kontejnerů. ``starting`` ani ``unhealthy`` není připravenost.
Chybějící služby, neúplná či chybující inspekce a vypršení desetiminutového
limitu znamenají neúspěch. Záměrně nulové repliky, očekávané dokončené úlohy
a služby bez healthchecku mají výslovné výjimky; cizí kontejnery hostitele
výsledek neovlivňují.

Lokální testy používají dočasný testovací klíč a izolované procesy, nikoli
produkční secrets nebo DEV připojení. Kombinovaná fixture zachovává spustitelné
oprávnění kopírovaných náhrad příkazů a před lokálním i emulovaným vzdáleným
krokem ověřuje jejich skutečný výběr shellem. Chybějící, nespustitelná nebo
zastíněná náhrada test zastaví; neočekávaný neúspěch jiné fáze není platnou
negativní kontrolou. Tato cesta se ověřuje také na Linuxu.
Skutečný kontrolní běh potřebuje
samostatné schválení cíle a operace. Pro regresi zvolte ``nasadit_verzi: false``,
platné ``test_mod`` a předem dohodnutý test (v režimu ``konkretni`` i odpovídající
``test_cislo``). Výchozí hodnota nasazení v existujícím workflow je ``true``;
při tomto testu ji proto výslovně změňte. Nasazení vyžaduje další souhlas.
Uložte URL běhu, jeho commit a výsledek SSH i následného stažení výsledků SCP.

Zapnutí vynucení a obnova
-----------------------------

Nastavení je pro celý repozitář. Pinování pouze na ``test`` nestačí, pokud
``main``, vydávaný tag nebo jiná spouštěná větev používá staré akce. GitHub
vynucuje SHA i pro vlastní akce; jeho pravidlo pro reusable workflows je
odlišné. Zdejší lokální kontrola záměrně požaduje SHA u všech externích
``uses``, lokální ``./`` volání zachovává. Podrobnosti:
`nastavení GitHub Actions <https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository>`_.

1. Po lidském review dostaňte připnuté workflow do ``test`` a následně
   schválenou cestou do ``main``. Vyjmenujte všechny další refy určené ke
   spouštění; připravte je, nebo výslovně ukončete podporu jejich opakovaných
   běhů. Publikované tagy se nepřesouvají. Prohlédněte i závislosti v composite
   akcích, které budou na těchto refech skutečně použity.
2. Dokončete schválený DEV kontrolní běh a zaznamenejte skutečné Dependabot PR.
   Před aktivací znovu načtěte stav a zachovejte všechna ostatní nastavení:

   .. code-block:: bash

      gh api repos/ARUP-CAS/aiscr-webamcr/actions/permissions

3. Předložte ke schválení přesnou změnu ``sha_pinning_required`` a kontrolní
   probe. Teprve po připravenosti všech podporovaných refů zapněte v
   ``Settings → Actions → General`` požadavek na úplný commit SHA. Potvrďte
   stejným čtecím API ``sha_pinning_required: true`` a nezměněný zbytek nastavení.
4. Na schváleném dočasném refu spusťte neškodný připnutý kontrolní workflow
   a odpovídající variantu s akcí odkazovanou tagem. Oba mají být bez secrets,
   přístupu k infrastruktuře, publikace image a write tokenu. Připnutá kontrola
   musí projít, varianta s tagem musí být odmítnuta konkrétně kvůli SHA politice.
   Uložte URL, commit a výsledek obou běhů a schválenou cestou odstraňte probe.

Při problému s vybranou akcí nejdříve zvolte jiný ověřený kompatibilní SHA.
Vrácení mutabilních tagů při zapnutém vynucení by obnovu zablokovalo. Vyžaduje-li
nouzová obnova vypnutí pravidla, předem schvalte přesný zásah, zaznamenejte
dočasný stav a teprve pak vraťte workflow. Před opětovným zapnutím zopakujte
kontrolu refů, nastavení a oba probe. Úprava workflow sama vynucení nezapíná.
