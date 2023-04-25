# Postup vytvoření scénáře

## Požadované vlastnosti testovacího scénáře

Požadované vlastnosti testovacího scénáře jsou následující (vychází z článku 
[How to Write Test Cases in Software Testing with Examples](https://www.guru99.com/test-case.html):

* testovací scénář by měl být jednoduchý a měl by testovat max. jednu stránku či jednu sadu funkcí,
* testovací scénář musí být napsán a vytvořen z pohledu uživatele, tj. musí přesně simulovat kroky, které by prováděl uživatel, pokud by chtěl dosáhnout daného výsledku,
* testy by se neměly překrývat,
* u každého testu musí být specifikována alespoň jedna metrika úspěšnosti průběhu.

## Postup vytvoření kódu testu

Pro scénář je třeba připravit sadu vstupních dat a kontrolní výstup.

# Přehled testovacích scénářů

## Struktura popisu scénáře

Popis scénáře musí obsahovat následující:

* ID scénáře,
* stručný popis scénáře,
* předpoklady pro průběh testu (pokud jsou), 
* uživatelské kroky, které scénář simuluje,
* testovací data,
* očekávané výsledky (tj. metriky, které oveřují úspěšný průběh testu).

Scénáře jsou seskupeny podle jednotlivých aplikací.

## Core

### CORE-001

* Testuje přihlášení uživatele.

#### Uživatelské kroky

1. Vyplnění formuláře na titulní stránce

#### Testovací data

| Field       | Value                         |
|-------------|-------------------------------|
| id_username | e-mail testovacího uživatele  |
| id_password | heslo testovacího uživatele   |

#### Očekávané výsledky

1. Uživatel je přesměrován na stránku s titulkem AMČR Homepage

#### Stav testu

Implementováno

## Projekt

#### PROJEKT-001

Testuje tabulku s projekty. Ověřuje, zda funguje řazení podle jednotlivých sloupců a zobrazení/skrývání 
sloupců.

Využívá metodu `_check_column_hiding`.

#### Předpoklady

* Uživatel je přihlášen.

#### Uživatelské kroky

1. Uživatel klikne na menu Projekty -> Vybrat projekty
1. Uživatel kliká na záhlaví jednotlivých sloupců
1. Uživatel skyje a znovu zobrazí jednotlivé sloupce pomocí výsuvného menu

#### Testovací data

*Žádná*

#### Očekávané výsledky

1. Po kliknutí na název sloupce je do adresy stránky přidán řetězec `sort=sloupec`
1. Po skytí sloupce zmizí název sloupce ze záhlaví
1. Po zobrazení sloupce je sloupec v záhlaví tabulky

#### Stav testu

Implementován

### Zapsání projektu

Test zapsání projektu na stránce `/projekt/zapsat`.

#### Předpoklady

* Uživatel je přihlášen.
* Jsou vložena kompletní data o katastrech, okresech a krajích.

#### Uživatelské kroky

1. Uživatel klikne na menu Projekty -> Zapsat
1. Uživatel vyplní data do formuláře a kliknutím na mapu vybere hlavní katastr
1. Uživatel klikne na tlačítko Uložit

#### Testovací data

| Field                | Value                                              |
|----------------------|----------------------------------------------------|
| typ_projektu         | záchranný                                          |
| id_podnet            | test                                               |
| id_lokalizace        | test                                               |
| id_parcelni_cislo    | test                                               |
| id_planovane_zahajeni| dynamicky vložené datum (dnes + dva dny - dnes + pět dní)|
| id_oznamovatel       | test                                               |
| id_odpovedna_osoba   | test                                               |
| id_adresa            | test                                               |
| id_telefon           | +420123456789                                      |
| id_email             | test@example.com                                   |

#### PROJEKT-ZAPSAT-P-001

Test simuluje zadání validních data měl by končit zapsáním projektu do databáze.

##### Očekávané výsledky

* Pole id_oznamovatel, id_odpovedna_osoba, id_adresa, id_telefon a id_material
* Po kliknutí na tlačítko Uložit je v databázi o 1 projekt více

##### Stav testu

Implementován

#### test_projekt_zapsat_p_001

##### Předpoklady

- Uživatel je přihlášen.
- Uživatel otevře stránku Zapsat projekt.

##### Uživatelské kroky

Uživatel vyplní formulář.

##### Testovací data

| Pole                  | Hodnota                                             |
|-----------------------|-----------------------------------------------------|
| id_typ_projektu       | záchranný                                           |
| projectMap            | (click_count: 5)                                    |
| id_podnet             | test                                                |
| id_lokalizace         | test                                                |
| id_parcelni_cislo     | test                                                |
| id_planovane_zahajeni | (date range calculated: 2 days and 5 days from now) |
| id_oznamovatel        | test                                                |
| id_odpovedna_osoba    | test                                                |
| id_adresa             | test                                                |
| id_telefon            | +420734456789                                       |
| id_email              | test@example.com                                    |


##### Očekávané výsledky

- Pole `id_oznamovatel` je povoleno.
- Pole `id_odpovedna_osoba` je povoleno.
- Pole `id_adresa` je povoleno.
- Pole `id_telefon` je povoleno.
- Pole `id_email` je povoleno.
- Počet projektů se zvýšil o 1.

##### Stav testu

Implementován

#### test_projekt_zapsat_n_001

##### Předpoklady

- Uživatel je přihlášen.
- Uživatel otevře stránku Zapsat projekt.

##### Uživatelské kroky

Uživatel otevře stránku Zapsat projekt.

##### Testovací data

Pokud není uvedeno, jsou stejná jako u `test_projekt_zapsat_p_001`.

| Field ID            | Value                                      |
|---------------------|--------------------------------------------|
| id_planovane_zahajeni | (date range calculated: -9 days and -5 days from today) |


##### Očekávané výsledky

- Počet projektů se nezměnil.

##### Stav testu

Implementován.

#### test_projekt_zapsat_p_001

##### Předpoklady

- Uživatel je přihlášen.
- Uživatel otevře stránku Zapsat projekt.

##### Uživatelské kroky

Uživatel vyplní formulář.

##### Testovací data

| Pole                  | Hodnota                                             |
|-----------------------|-----------------------------------------------------|
| id_typ_projektu       | záchranný                                           |
| projectMap            | (click_count: 5)                                    |
| id_podnet             | test                                                |
| id_lokalizace         | test                                                |
| id_parcelni_cislo     | test                                                |
| id_planovane_zahajeni | (date range calculated: 2 days and 5 days from now) |
| id_oznamovatel        | test                                                |
| id_odpovedna_osoba    | test                                                |
| id_adresa             | test                                                |
| id_telefon            | +420734456789                                       |
| id_email              | test@example.com                                    |


##### Očekávané výsledky

- Pole `id_oznamovatel` je povoleno.
- Pole `id_odpovedna_osoba` je povoleno.
- Pole `id_adresa` je povoleno.
- Pole `id_telefon` je povoleno.
- Pole `id_email` je povoleno.
- Počet projektů se zvýšil o 1.

##### Stav testu

Implementován

#### test_projekt_zapsat_n_001

##### Předpoklady

- Uživatel je přihlášen.
- Uživatel otevře stránku Zapsat projekt.

##### Uživatelské kroky

Uživatel otevře stránku Zapsat projekt.

##### Testovací data

Pokud není uvedeno, jsou stejná jako u `test_projekt_zapsat_p_001`.

| Field ID            | Value                                      |
|---------------------|--------------------------------------------|
| id_planovane_zahajeni | (date range calculated: -9 days and -5 days from today) |


##### Očekávané výsledky

- Počet projektů se nezměnil.

##### Stav testu

Implementován.

#### test_projekt_zapsat_n_002

##### Předpoklady

- Uživatel je přihlášen.
- Uživatel otevře stránku Zapsat projekt.

##### Uživatelské kroky

Uživatel otevře stránku Zapsat projekt.

##### Testovací data

Pokud není uvedeno, jsou stejná jako u `test_projekt_zapsat_p_001`.

| Field ID            | Value                                      |
|---------------------|--------------------------------------------|
| id_telefon | XXX |


##### Očekávané výsledky

- Počet projektů se nezměnil.

##### Stav testu

Implementován.

#### test_projekt_zapsat_n_003

##### Předpoklady

- Uživatel je přihlášen.
- Uživatel otevře stránku Zapsat projekt.

##### Uživatelské kroky

Uživatel otevře stránku Zapsat projekt.

##### Testovací data

Pokud není uvedeno, jsou stejná jako u `test_projekt_zapsat_p_001`.

| Field ID            | Value                                      |
|---------------------|--------------------------------------------|
| id_planovane_zahajeni | (date range calculated: 600 days and 620 days from today) |


##### Očekávané výsledky

- Počet projektů se nezměnil.

##### Stav testu

Implementován.

#### test_projekt_zapsat_n_002

##### Předpoklady

- Uživatel je přihlášen.
- Uživatel otevře stránku Zapsat projekt.

##### Uživatelské kroky

Uživatel otevře stránku Zapsat projekt.

##### Testovací data

Pokud není uvedeno, jsou stejná jako u `test_projekt_zapsat_p_001`.

| Field ID            | Value                                      |
|---------------------|--------------------------------------------|
| id_telefon | XXX |


##### Očekávané výsledky

- Počet projektů se nezměnil.

##### Stav testu

Implementován.

#### test_projekt_zahajit_vyzkum_p_001

##### Předpoklady

- Uživatel je přihlášen.
- Uživatel otevře stránku Zapsat projekt.
- Existuje projekt ve stavu A2.

##### Uživatelské kroky

Uživatel otevře projekt ve stavu A2.

##### Testovací data

| Field ID          | Value                                      |
|-------------------|--------------------------------------------|
| id_datum_zahajeni | (date calculated: -5 days from today)      |

##### Očekávané výsledky

- Projekt přesunut do stavu A3
- Datum zahájení projektu odpovídá testovacím datům.

##### Stav testu

Implementován.

#### test_projekt_ukoncit_vyzkum_p_001

##### Předpoklady

- Uživatel je přihlášen.
- Uživatel otevře stránku Zapsat projekt.
- Existuje projekt ve stavu A3.

##### Uživatelské kroky

Uživatel otevře projekt ve stavu A3.

##### Testovací data

| Field ID          | Value                                 |
|-------------------|---------------------------------------|
| id_datum_ukonceni | (date calculated: -1 days from today) |

##### Očekávané výsledky

- Projekt přesunut do stavu A4.
- Datum zahájení projektu odpovídá testovacím datům.

##### Stav testu

Implementován.

#### test_projekt_ukoncit_vyzkum_n_001

##### Předpoklady

- Uživatel je přihlášen.
- Uživatel otevře stránku Zapsat projekt.
- Existuje projekt ve stavu A3.

##### Uživatelské kroky

Uživatel otevře projekt ve stavu A3.

##### Testovací data

| Field ID          | Value                                 |
|-------------------|---------------------------------------|
| id_datum_ukonceni | (date calculated: 90 days from today) |

##### Očekávané výsledky

- Projekt zůstal ve stavu A3.
- Zobrazena chyba `Datum nesmí být dále než měsíc v budoucnosti`.

##### Stav testu

Implementován.

#### test_projekt_ukoncit_vyzkum_p_001

##### Předpoklady

- Uživatel je přihlášen.
- Uživatel otevře stránku Zapsat projekt.
- Existuje projekt ve stavu A3.

##### Uživatelské kroky

Uživatel otevře projekt ve stavu A3.

##### Testovací data

| Field ID          | Value                                 |
|-------------------|---------------------------------------|
| id_datum_ukonceni | (date calculated: -1 days from today) |

##### Očekávané výsledky

- Projekt přesunut do stavu A4.
- Datum zahájení projektu odpovídá testovacím datům.

##### Stav testu

Implementován.

#### test_projekt_uzavrit_p_001

##### Předpoklady

- Uživatel je přihlášen.
- Uživatel otevře stránku Zapsat projekt.
- Existuje projekt ve stavu A4, který má projektovou akci.

##### Uživatelské kroky

Uživatel otevře projekt ve stavu A4.

##### Testovací data

Žádná.

##### Očekávané výsledky

- Projekt přestunut do stavu A5.

##### Stav testu

Implementován.

#### test_projekt_uzavrit_n_001

##### Předpoklady

- Uživatel je přihlášen.
- Uživatel otevře stránku Zapsat projekt.
- Existuje projekt ve stavu A4, který nemá projektovou akci.

##### Uživatelské kroky

Uživatel otevře projekt ve stavu A4.

##### Testovací data

Žádná.

##### Očekávané výsledky

- Projekt zůstal ve stavu A4.
- Zobrazena chyba `Projekt musí mít alespoň jednu projektovou akci`.

##### Stav testu

Implementován.

#### test_projekt_archivovat_p_001

##### Předpoklady

- Uživatel je přihlášen.
- Uživatel otevře stránku Zapsat projekt.
- Existuje projekt ve stavu A5, který má archivovanou projektovou akci.

##### Uživatelské kroky

Uživatel otevře projekt ve stavu A5.

##### Testovací data

Žádná

##### Očekávané výsledky

- Projekt je přesunut do stavu A6.

##### Stav testu

Implementován.

#### test_projekt_uzavrit_n_001

##### Předpoklady

- Uživatel je přihlášen.
- Uživatel otevře stránku Zapsat projekt.
- Existuje projekt ve stavu A5, který má nearchivovanou projektovou akci.

##### Uživatelské kroky

Uživatel otevře projekt ve stavu A5.

##### Testovací data

Stejná jako u `test_projekt_zapsat_p_001`.

##### Očekávané výsledky

- Projekt zůstal ve stavu A5.
- Zobrazena chyba `Akce musí být archivovaná`.

##### Stav testu

Implementován.

#### ProjektVratitArchivovanySeleniumTest

##### Předpoklady

- Uživatel je přihlášen.
- Uživatel otevře stránku Zapsat projekt.
- Existuje projekt ve stavu A6.

##### Uživatelské kroky

Uživatel otevře projekt ve stavu A6.

##### Testovací data

| Field ID  | Value |
|-----------|-------|
| id_reason | test  |


##### Očekávané výsledky

- Projekt přesunut do stavu A5.
- Zobrazena chyba `Akce musí být archivovaná`.

##### Stav testu

Implementován.

#### ProjektVratitUzavrenySeleniumTest

##### Předpoklady

- Uživatel je přihlášen.
- Uživatel otevře stránku Zapsat projekt.
- Existuje projekt ve stavu A5.

##### Uživatelské kroky

Uživatel otevře projekt ve stavu A5.

##### Testovací data

| Field ID  | Value |
|-----------|-------|
| id_reason | test  |


##### Očekávané výsledky

- Projekt přesunut do stavu A4.

##### Stav testu

Implementován.

#### ProjektVratitUkoncenySeleniumTest

##### Předpoklady

- Uživatel je přihlášen.
- Uživatel otevře stránku Zapsat projekt.
- Existuje projekt ve stavu A4.

##### Uživatelské kroky

Uživatel otevře projekt ve stavu A4.

##### Testovací data

| Field ID  | Value |
|-----------|-------|
| id_reason | test  |


##### Očekávané výsledky

- Projekt přesunut do stavu A3.

##### Stav testu

Implementován.

#### ProjektVratitZahajenySeleniumTest

##### Předpoklady

- Uživatel je přihlášen.
- Uživatel otevře stránku Zapsat projekt.
- Existuje projekt ve stavu A3.

##### Uživatelské kroky

Uživatel otevře projekt ve stavu A3.

##### Testovací data

| Field ID  | Value |
|-----------|-------|
| id_reason | test  |


##### Očekávané výsledky

- Projekt přesunut do stavu A2.

##### Stav testu

Implementován.

#### ProjektVratitPrihlasenySeleniumTest

##### Předpoklady

- Uživatel je přihlášen.
- Uživatel otevře stránku Zapsat projekt.
- Existuje projekt ve stavu A2.

##### Uživatelské kroky

Uživatel otevře projekt ve stavu A2.

##### Testovací data

| Field ID  | Value |
|-----------|-------|
| id_reason | test  |


##### Očekávané výsledky

- Projekt přesunut do stavu A1.

##### Stav testu

Implementován.

#### test_projekt_zrusit_p_001

##### Předpoklady

- Uživatel je přihlášen.
- Uživatel otevře stránku Zapsat projekt.
- Existuje projekt.

##### Uživatelské kroky

Uživatel otevře projekt.

##### Testovací data

| Field ID  | Value      |
|-----------|------------|
| reason | item no. 2 |


##### Očekávané výsledky

- Projekt přesunut do stavu A7.

##### Stav testu

Implementován.

#### test_projekt_zrusit_p_002

##### Předpoklady

- Uživatel je přihlášen.
- Uživatel otevře stránku Zapsat projekt.
- Existuje projekt.

##### Uživatelské kroky

Uživatel otevře projekt.

##### Testovací data

| Field ID  | Value      |
|-----------|------------|
| reason | item no. 1 |
| id_projekt_id | test       |


##### Očekávané výsledky

- Projekt přesunut do stavu A7.

##### Stav testu

Implementován.

#### test_projekt_zrusit_n_001

##### Předpoklady

- Uživatel je přihlášen.
- Uživatel otevře stránku Zapsat projekt.
- Existuje projekt s projektovými akcemi.

##### Uživatelské kroky

Uživatel otevře projekt s projektovými akcemi.

##### Testovací data

| Field ID  | Value      |
|-----------|------------|
| reason | item no. 2 |


##### Očekávané výsledky

- Projekt zůstal ve výchozím stavu.
- Zobrazena chyba `Projekt před zrušením nesmí mít projektové akce`.

##### Stav testu

Implementován.

#### test_projekt_zrusit_p_001

##### Předpoklady

- Uživatel je přihlášen.
- Uživatel otevře stránku Zapsat projekt.
- Existuje projekt ve stavu A7.

##### Uživatelské kroky

Uživatel otevře projekt s projektovými akcemi.

##### Testovací data

| Field ID  | Value |
|-----------|-------|
| id_reason_text | test  |


##### Očekávané výsledky

- Projekt je přesunut do stavu A8.

##### Stav testu

Implementován.

## Nadpisy

#### ID scénáře
##### Předpoklady
##### Uživatelské kroky
##### Testovací data
##### Očekávané výsledky
##### Stav testu