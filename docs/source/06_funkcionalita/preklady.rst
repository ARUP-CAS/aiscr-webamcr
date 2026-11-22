Překlady
========

Výchozí překladové katalogy jsou součástí repozitáře v souborech
``locale/cs/LC_MESSAGES/django.po`` a ``locale/en/LC_MESSAGES/django.po``.
Repozitář je autoritativním zdrojem obsahu. Při nasazení se katalogy z image
zkopírují na volume ``locale_data`` v ``/vol/web/locale``, doplní se nové klíče
pomocí ``makemessages`` a vytvoří se binární katalogy ``.mo`` pomocí
utility ``msgfmt`` v pracovním adresáři image. Soubory ``.mo`` se do repozitáře
neukládají.

Překlady je možné spravovat přímo v aplikaci přes administraci pomocí
rozšíření ``rosetta``.

Rosetta
--------
Pomocí rozšíření je možné spravovat překlady pro všechny jazyky aplikace.
Rosetta pracuje s katalogy na runtime volume. Změna provedená přímo v běžící
aplikaci platí do dalšího nasazení; při nasazení ji nahradí obsah z repozitáře.
Před přepsáním existujícího katalogu entrypoint porovná aktuální katalog na
volume s nově vygenerovaným katalogem. Pokud jsou soubory shodné, záloha se
nevytvoří a v logu se uvede, že byla přeskočena. Tím se při běžném restartu
nevytvářejí opakované shodné zálohy. Pokud se katalogy liší, entrypoint vytvoří
kopii ``django_backup_DDMMYYYYHHMMSS.po`` ve stejném adresáři na volume
``locale_data``. Zálohy jsou tak uložené vedle katalogu daného jazyka.

Entrypoint průběžně udržuje počet záloh v rozumných mezích. Zálohy starší než
365 dní odstraní a následně ponechá nejvýše 100 nejnovějších záloh pro každý
jazyk. Pravidla se vztahují na zálohy vytvořené entrypointem i Rosettou.
Služba ``sidecar`` zůstává beze změny a průběžně synchronizuje obsah volume
``locale_data`` do svého zálohovacího umístění.

**Úprava a přenos překladu do repozitáře**:

#. Otevřete v Rosettě hlavní soubor ``django.po`` pro požadovaný jazyk a
   upravte překlady.
#. Uložte změny a použijte akci **Download this catalog**.
#. Stažený soubor nahraďte v repozitáři odpovídajícím souborem pod
   ``locale/<jazyk>/LC_MESSAGES/django.po``.
#. Zkontrolujte diff, proveďte code review a změnu commitněte.
#. Po nasazení ověřte, že se katalog zobrazuje v Rosettě pouze jednou a že
   aplikace používá nově zacommitované hodnoty.

Import nového souboru v Rosettě nejdřív připraví zálohu (kopii původního katalogu
``django_backup_DDMMYYYYHHMMSS.po``), nový ``.po`` i zkompilovaný ``.mo`` v dočasných
souborech vedle katalogu a teprve pak je bezprostředně po sobě přejmenuje na cílové
soubory. Pokud se nahraný soubor nepodaří načíst nebo se cokoli z přípravy nezdaří,
katalog ani seznam záloh se nezmění a administrace zobrazí chybovou hlášku.

Každé přejmenování je atomické samostatně; dvojice katalogů netvoří společnou
transakci. Selže-li publikace zálohy, katalogy i seznam záloh zůstanou beze změny.
Selže-li náhrada ``.po``, záloha už zůstává zveřejněná. Selže-li až náhrada ``.mo``,
zůstane nové ``.po``, původní ``.mo`` a záloha původního ``.po``. Běžící aplikace
nadále překládá podle původního ``.mo``. Při zachycené chybě se zbývající dočasné
soubory smažou a administrace zobrazí chybu; obnova po ukončení procesu není
zaručena. Zálohy vytvořené Rosettou i entrypointem zůstávají na runtime volume
a do repozitáře se nepřenášejí.

Převzetí změn běžícími procesy a prodlevu opakovaných pokusů po chybě popisuje
část Rosetta v :doc:`administrace`. Kontrola nezaručuje konzistentní snímek
souběžně měněných souborů ani okamžité zotavení po přechodné chybě čtení.

Text odstávky
-------------

Text provozní odstávky není překladový katalog. Ukládá se přímo v modelu
``OdstavkaSystemu`` v polích ``text_cs`` a ``text_en`` a administrace jej z
těchto polí čte i zapisuje. Uložení odstávky proto nemění ``.po`` ani ``.mo``
soubor. Výchozí katalog již neslouží jako úložiště klíče
``base.odstavka.text``.
