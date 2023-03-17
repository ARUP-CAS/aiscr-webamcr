# Postup vytvoření scénáře

## Požadované vlastnosti testovacího scénáře

Požadované vlastnosti testovacího scénáře jsou následující (vychází z článku 
[How to Write Test Cases in Software Testing with Examples](https://www.guru99.com/test-case.html):

* testovací scénář by měl být jednoduchý a měl by testovat max. jednu stránku či jednu sadu funkcí,
* testovací scénář musí být napsán a vytvořen z pohledu uživatele, tj. musí přesně simulovat kroky, které by prováděl uživatel, pokud by chtěl dosáhnout daného výsledku,
* testy by se neměly překrývat,
* u každého testu musí být specifikována alespoň jedna metrika úspěšnosti průběhu.

## Postup vytvoření kódu testu

K vytvoření kódu lze využít rozšíření prohlížeče [Selenium IDE](https://www.selenium.dev/selenium-ide/), rozšíření je
dostupné pro Firefox a Google Chrome. Test je možné nahrát pomocí následujícího postupu:

* Spusťte prohlížeč a otevřete rozšíření Selenium IDE. Založte nový projekt či otevřete existující.
* Klikněte na tlačítko Record vpravo nahoře. Zadejte adresu webu. Poté se otevře nové okno prohlížeče.
* Proveďte uživatelskou akci, která má být otestována.
* Po dokončení akce klikněte na tlačítko STOP a zadejte název testu.
* Klikněte pravým tlačítkem na název testu v panelu vlevo a zvolte možnost Export.
* V dialogovém okně vyberte možnost Python pytest a klikněte na Export. Výsledkem je vygenerovaný Python skript s průběhem testu.
* Test je třeba doplnit popisem a metrikou pro ověření úspěšného průběhu testu.

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

* id_username = e-mail testovacího uživatele
* id_password = heslo testovacího uživatele

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

* typ_projektu = záchranný
* id_podnet = test
* id_lokalizace = test
* id_parcelni_cislo = test
* id_planovane_zahajeni = dynamicky vložené datum (dnes + dva dny - dnes + pět dní)
* id_oznamovatel = test
* id_odpovedna_osoba = test
* id_adresa = test
* id_telefon = +420123456789
* id_email = test@example.com

#### PROJEKT-ZAPSAT-P-001

Test simuluje zadání validních data měl by končit zapsáním projektu do databáze.

##### Očekávané výsledky

* Pole id_oznamovatel, id_odpovedna_osoba, id_adresa, id_telefon a id_material
* Po kliknutí na tlačítko Uložit je v databázi o 1 projekt více

##### Stav testu

Implementován

## Nadpisy

#### ID scénáře
##### Předpoklady
##### Uživatelské kroky
##### Testovací data
##### Očekávané výsledky
##### Stav testu