# Spec Delta

## Purpose

Anonymizace kopie produkční databáze na testovacím serveru: které údaje se nahrazují, které záznamy jsou z anonymizace vyloučené a kdy běh blokuje navazující publikaci metadat.

Normativní klíčová slova `MUST` a `MUST NOT` se čtou podle RFC 2119.

## ADDED Requirements

### Requirement: Chráněné texty jen u chráněných záznamů
Anonymizace MUST nahradit neprázdná chráněná textová pole (typy `*-chranene_udajeType` ve schématu `amcr.xsd`) jen u záznamů s přístupností vyšší než A. U záznamů s přístupností A MUST NOT tato pole měnit. Projekt bez určené přístupnosti se MUST posuzovat jako chráněný.

#### Scenario: Veřejná lokalita si ponechá název
- **WHEN** lokalita s přístupností A má název „Hradiště“
- **THEN** po anonymizaci má lokalita název „Hradiště“

#### Scenario: Chráněná akce dostane zástupnou lokalizaci
- **WHEN** akce s přístupností C má vyplněnou lokalizaci okolností
- **THEN** po anonymizaci nese lokalizace okolností zástupnou hodnotu

### Requirement: Vyloučené uživatelské účty
Anonymizace MUST ponechat beze změny účty ve skupině administrátorů a účty napojené na osobu `OS-007414`. Příjmení účtu MUST NOT o vyloučení rozhodovat. Pokud osoba `OS-007414` v databázi neexistuje, anonymizace MUST vypsat varování a jako vyloučené ponechat jen administrátory.

#### Scenario: Účet napojený na anonymní osobu se nemění
- **WHEN** účet bez administrátorské role je napojený na osobu `OS-007414`
- **THEN** po anonymizaci má účet původní jméno, e-mail, heslo i napojení na osobu

#### Scenario: Příjmení Anonym bez napojení výjimku nezakládá
- **WHEN** účet má příjmení „Anonym“, ale není napojený na osobu `OS-007414` ani není administrátor
- **THEN** účet se anonymizuje

### Requirement: Anonymizovaný účet se odpojí od osoby
U každého anonymizovaného účtu MUST anonymizace zrušit napojení na osobu a odstranit ORCID. Záznamy osob samotné MUST NOT měnit.

#### Scenario: Odpojení a ORCID
- **WHEN** anonymizovaný účet je napojený na osobu a má ORCID
- **THEN** po anonymizaci účet nemá napojenou osobu ani ORCID a záznam osoby zůstává beze změny

### Requirement: Nedoručitelné zástupné adresy
Každá zástupná e-mailová adresa, kterou anonymizace zapíše, MUST ležet v doméně nejvyšší úrovně `.invalid` (RFC 2606). Anonymizace MUST nahradit i neprázdné e-mailové adresy krajů. Adresa, která už nese zástupnou hodnotu ve starší doméně, se MUST při opakovaném běhu přepsat do domény `.invalid`.

#### Scenario: E-mail kraje
- **WHEN** kraj má vyplněný e-mail
- **THEN** po anonymizaci má kraj e-mail v doméně `.invalid`

#### Scenario: Starší zástupná adresa
- **WHEN** oznamovatel má adresu ve tvaru zástupné hodnoty v doméně `example.cz`
- **THEN** po anonymizaci má adresu v doméně `.invalid`

### Requirement: Historie změny katastru u chráněných záznamů
U záznamů historie typu `KAT` (změna katastru), které patří chráněnému archeologickému záznamu, chráněnému projektu nebo chráněnému samostatnému nálezu, MUST anonymizace odstranit poznámku. Ostatní údaje záznamu historie MUST NOT měnit.

#### Scenario: Poznámka změny katastru u chráněné akce
- **WHEN** chráněná akce má v historii záznam typu `KAT` s poznámkou „KOŠUMBERK -> LUŽE“
- **THEN** po anonymizaci záznam historie existuje a nemá poznámku

#### Scenario: Veřejný záznam si historii ponechá
- **WHEN** veřejná akce má v historii záznam typu `KAT` s poznámkou
- **THEN** po anonymizaci poznámka zůstává

### Requirement: Náhradní řešení polohy
Pokud pro chráněný PIAN neexistuje nová poloha uvnitř průniku původního okresu a původního listu ZM50, anonymizace MUST PIAN přesunout kamkoli do původního okresu a přepočítat mu mapové listy. Pokud pro chráněný projekt, samostatný nález nebo dokument nejde novou polohu najít vůbec, anonymizace MUST jeho geometrii odstranit a katastr, který by prozradil původní polohu, nahradit nebo odstranit.

#### Scenario: PIAN u hranice listu
- **WHEN** chráněný PIAN leží v okrese, jehož průnik s původním listem ZM50 neumožní novou polohu
- **THEN** PIAN se přesune jinam v témže okresu a jeho list ZM50 odpovídá nové poloze

#### Scenario: Nález v okrese bez hranice
- **WHEN** chráněný samostatný nález leží v okrese bez hranice
- **THEN** po anonymizaci nemá nález geometrii ani původní katastr

### Requirement: Blokující předběžná kontrola
Před prvním zápisem do databáze MUST anonymizace zjistit chráněné polohy a katastry, které nepůjde nahradit ani podle náhradního řešení, a vypsat jejich počty a identifikátory podle důvodu. Pokud nějaké najde, MUST skončit nenulovým návratovým kódem a MUST NOT nic zapsat. Režim `--dry-run` MUST vypsat tutéž kontrolu.

#### Scenario: Nevyřešitelný PIAN zastaví běh před zápisem
- **WHEN** chráněný PIAN leží v okrese bez hranice
- **THEN** anonymizace vypíše jeho identifikátor s důvodem, skončí nenulovým kódem a databáze zůstane beze změny

### Requirement: Výsledek běhu
Anonymizace MUST skončit nenulovým návratovým kódem, pokud po běhu zůstala nenahrazená chráněná poloha nebo katastr, nebo pokud došlo k chybě. V takovém případě MUST NOT hlásit úspěšné dokončení.

#### Scenario: Chyba při převodu
- **WHEN** během běhu selže převod souřadnic jedné chráněné polohy
- **THEN** anonymizace skončí nenulovým kódem a vypíše identifikátor dotčeného záznamu
