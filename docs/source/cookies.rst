Cookies
=======

Cookies v prohlížeči jsou malé bloky dat, které webové stránky ukládají na vašem počítači. Tyto informace mohou
obsahovat různé údaje, jako jsou vaše přihlašovací údaje, preference na dané webové stránce nebo obsah
vašeho nákupního košíku na e-shopu.

Když se na stránku vrátíte, prohlížeč pošle uložené cookies zpět na server, což umožňuje webu "si vás pamatovat".
Díky tomu může web okamžitě načíst vaše nastavení, jako je například zvolený jazyk stránky, nebo vás automaticky
přihlásit, aniž byste museli znovu zadávat své uživatelské jméno a heslo.

Cookies jsou užitečné pro uživatele i provozovatele webů, protože zjednodušují a zpříjemňují procházení internetu.
Níže naleznete přehled cookies, které ukládá aplikace AMČR.

Pro zobrazení cookies, které ukládá aplikace AMČR ve vašem prohlížeči, můžete postupovat podle těchto obecných kroků.
Přesné kroky se liší v závislosti na konkrétním prohlížeči, který používáte:

**Google Chrome**:

1. Klikněte na tři tečky v pravém horním rohu prohlížeče a vyberte „Nastavení“.
2. Posuňte se dolů a klikněte na „Pokročilá nastavení“.
3. V sekci „Soukromí a zabezpečení“ vyberte „Nastavení obsahu“ nebo „Nastavení webu“.
4. Klikněte na „Cookies“.
5. Zde můžete zobrazit a spravovat cookies pro konkrétní stránky.

**Mozilla Firefox**:

1. Klikněte na tři čáry v pravém horním rohu a vyberte „Možnosti“ nebo „Předvolby“.
2. Vyberte panel „Soukromí a zabezpečení“.
3. V sekci „Cookies a data stránek“ můžete zobrazit a spravovat cookies.

**Safari**:

1. V nabídce Safari vyberte „Předvolby“.
2. Přejděte na kartu „Soukromí“.
3. Zde můžete spravovat nastavení cookies a data webových stránek.

**Microsoft Edge**:

1. Klikněte na tři tečky v pravém horním rohu a vyberte „Nastavení“.
2. Vyberte „Soukromí, vyhledávání a služby“.
3. V sekci „Vymazat údaje procházení“ klikněte na „Zvolit, co chcete vymazat“.
4. Vyberte „Cookies a další data webových stránek“ a poté „Zobrazit další“ pro správu cookies.

ID relace (Session ID)
-----------------------

Session ID cookie je malý datový soubor, který webový server pošle a uloží v prohlížeči uživatele,
když uživatelnavštíví webovou stránku. Tento cookie obsahuje jedinečný identifikátor, známý jako Session ID,
který server používá k rozpoznání konkrétního uživatelského sezení. Díky tomu může server udržovat stavové
informace pro uživatele, i když HTTP protokol, který webové stránky používají, je bezstavový. Bezstavovost znamená,
že každý požadavek na server je nezávislý a server standardně neudržuje žádné informace o uživatelích mezi
různými požadavky.

Jak Session ID Cookie funguje:

1. **Vytvoření Session ID**: Když uživatel poprvé navštíví webovou stránku, server vytvoří Session ID pro toto sezení. Toto ID je jedinečné pro každé sezení a slouží k identifikaci uživatele během jeho interakce s webem.
2. **Uložení Session Cookie**: Server poté pošle toto Session ID zpět prohlížeči uživatele ve formě cookie. Prohlížeč cookie uloží a bude ho odesílat zpět serveru s každým dalším požadavkem na stránku.
3. **Použití Session ID**: Při každém dalším požadavku na server prohlížeč posílá cookie s Session ID zpět serveru. Server použije toto ID k zjištění, že požadavky pocházejí od stejného uživatele, a může tak uživateli přizpůsobit obsah, udržovat stav přihlášení, sledovat nákupní košík v e-shopu atd.
4. **Expirace a bezpečnost**: V případě aplikace AMČR dojde ke smazání cookie a odhlášení uživatele po hodinové neaktivitě. Poté je nutné se opět přhlásit.

Session ID cookie je tedy klíčovým nástrojem pro udržení kontinuity a bezproblémové interakce mezi uživatelem
a webovou aplikací v bezstavovém prostředí internetu.

CSRF token
----------

CSRF token uložený do cookie má za cíl zvýšit bezpečnost aplikace.

CSRF útoky, neboli útoky typu "Cross-Site Request Forgery", jsou formou zneužití, při kterém útočník využije důvěru,
kterou má webová aplikace v prohlížeč uživatele. Představte si, že jste přihlášeni do webové aplikace AMČR
a současně si prohlížíte jiné stránky. Pokud by aplikace nebyla chráněna proti útoku typu CSRF,
útočník by mohl vytvořit škodlivou stránku nebo email, který bez vašeho vědomí
odešle požadavek do aplikace AMČR, jako byste jej odeslali vy sami.

Aby se webové aplikace chránily proti CSRF útokům, často používají tzv. CSRF tokeny. CSRF token je jedinečný,
tajný řetězec, který server přidává do formulářů nebo URL adres, které vyžadují interakci uživatele. Když uživatel
odesílá formulář nebo provádí akci, která vyžaduje ověření, server zkontroluje, zda se odeslaný token shoduje s tím,
který byl vygenerován pro danou uživatelskou session. Pokud se tokeny neshodují nebo je token chybějící, server
požadavek odmítne s předpokladem, že se může jednat o CSRF útok.

Token zajišťuje, že každý požadavek, který má být proveden na serveru, musí být doprovázen platným tokenem,
který nemůže být vygenerován na žádné jiné stránce než na té, kterou kontroluje server. Tím se zabraňuje útočníkům
v zasílání neoprávněných požadavků v zastoupení ničeho netušících uživatelů.

Google Analytics Cookies
------------------------

Cookies od Google Analytics se využívají k analýze návštěvnosti webových stránek. Tyto cookies pomáhají provozovateli
služby pochopit, jak návštěvníci interagují s webem. Informace, které tyto cookies shromažďují, zahrnují například
počet návštěvníků na stránce, odkud návštěvníci přicházejí a které stránky navštěvují nejčastěji. Tato data
umožňují zlepšovat fungování našeho webu a zajišťují, aby byl pro uživatele co nejpříjemnější a nejužitečnější.

**Používání Google Analytics Cookies**:

1. **Sběr dat**: Cookies od Google Analytics automaticky sbírají informace o vašem používání webu. Tato data zahrnují například, kolik času uživatelé stráví na stránce, na které odkazy klikají a které stránky navštívili.

2. **Anonymizace IP**: V souladu s ochranou soukromí se IP adresy návštěvníků mohou anonymizovat. To znamená, že osobní identifikace uživatele je výrazně omezena.

3. **Zpracování a analýza dat**: Informace shromážděné pomocí těchto cookies jsou zpracovány Google Analytics pro vytváření analytických reportů o aktivitách uživatelů na stránce. Tyto reporty pomáhají provozovatelům webu pochopit a zlepšit výkon stránky.

Cookies služby Google Analytics neshromažďují informace, které by uživatele osobně identifikovaly. Veškeré informace jsou shromažďovány
anonymně a slouží pouze k vylepšení funkčnosti webu.

Další cookies
-------------

Cookie `show-form` slouží k uložení formuláře, na který má být prohlížeč přesměrován. Jedná se zpravidla o případ,
kdy uživatel/uživatelka provede akci na jednom formuláři a po potvrzení této akce je přesněmovaný na jiný formuláře.
Hodnota s prefixem `detail_dj_form_` slouží k přesměrování na formulář dokumentační jednotky, například po odpojení
PAINu.

Cookie `detail-id-shown` slouží k nastavení zoomu mapy pro formulář detailu archeologického záznamu a lokality.

Cookie `set-active` je používána k uchování aktivního prvku pro editaci.  Hodnota s prefixem
`el_div_dokumentacni_jednotka_` slouží k označení aktuálně upravovaná dokumentační jednotce na stránce se detailem
archeologického záznamu.

Cookie `next_url` slouží k přesměrování, například po automatickém přihlášení.

Cookie `zpet` slouží k nastavení odkazu pro přechod na předchozí stránku u obrazovky pro detail dokumentu.
