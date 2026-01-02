Překlady
========

Překlady v aplikaci jsou ukládány na volume docker `locale_data`, čím je zabezpečená jich kontinuita i po nasazení nové verze aplikace.
Překlady je možné spravovat přímo v aplikaci cez admin rozhraní pomocí rozšíření `rosetta`. 

Rosetta
--------
Pomocí rozšíření je možné spravovat překlady pro všechny jazyky aplikace. 
V základním přehledu jsou zobrazená překlady pro všechny jazyky které je možné z listu vybrat.
V listu jsou zobrazená hlavní překladové soubory aktuálně používaná `django.po`, 
které není možné odstranit a backup soubory `_backup_DDMMYYYYHHMM` vzniklé pri importu, 
které je možné odstranit.

**Rosetta úprava souborů**:

Po kliknutí na překladový soubor z listu je uživatel přesměrován na stránku formuláře pro úpravu.
V daném formuláři je možné upravovat jen hlavní souboru. To samé platí i o importu nového souboru.
Všechny soubory je ale možné stáhnout k sobe.

**Rosetta import souborů**:

Na stránce formuláře v pravé horní části je tlačítko pro import, 
pomocí kterého je uživatel přesměrován na formulář pro nahrání nové verze překladového souboru.
Soubor musí mít příponu `.po` a velikost nejméně `1000B`.
Po nahrání nového souboru se starý přejmenuje na backup soubor `django_backup_DDMMYYYYHHMM.po`.


