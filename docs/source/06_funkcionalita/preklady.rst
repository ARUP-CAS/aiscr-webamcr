Překlady
========

Výchozí překladové katalogy jsou součástí repozitáře v souborech
``locale/cs/LC_MESSAGES/django.po`` a ``locale/en/LC_MESSAGES/django.po``.
Repozitář je autoritativním zdrojem obsahu. Při nasazení se katalogy z image
zkopírují na volume ``locale_data`` v ``/vol/web/locale``, doplní se nové klíče
pomocí ``makemessages`` a vytvoří se binární katalogy ``.mo`` pomocí
``compilemessages``. Soubory ``.mo`` se do repozitáře neukládají.

Překlady je možné spravovat přímo v aplikaci přes administraci pomocí
rozšíření ``rosetta``.

Rosetta
--------
Pomocí rozšíření je možné spravovat překlady pro všechny jazyky aplikace.
Rosetta pracuje s katalogy na runtime volume. Změna provedená přímo v běžící
aplikaci platí do dalšího nasazení; při nasazení ji nahradí obsah z repozitáře.
Před přepsáním existujícího katalogu entrypoint vytvoří kopii
``django_backup_DDMMYYYYHHMMSS.po`` v ``$HOME/translations_backup``. Vedle
této kopie pokračuje v provozu také služba ``sidecar``, která volume průběžně
synchronizuje do stejného zálohovacího umístění.

**Úprava a přenos překladu do repozitáře**:

#. Otevřete v Rosettě hlavní soubor ``django.po`` pro požadovaný jazyk a
   upravte překlady.
#. Uložte změny a použijte akci **Download this catalog**.
#. Stažený soubor nahraďte v repozitáři odpovídajícím souborem pod
   ``locale/<jazyk>/LC_MESSAGES/django.po``.
#. Zkontrolujte diff, proveďte code review a změnu commitněte.
#. Po nasazení ověřte, že se katalog zobrazuje v Rosettě pouze jednou a že
   aplikace používá nově zacommitované hodnoty.

Import nového souboru v Rosettě před uložením přejmenuje původní katalog na
``django_backup_DDMMYYYYHHMMSS.po``. Záložní soubory Rosetty i zálohy
z entrypointu zůstávají pouze na serveru a do repozitáře se nepřenášejí.

Text odstávky
-------------

Text provozní odstávky není překladový katalog. Ukládá se přímo v modelu
``OdstavkaSystemu`` v polích ``text_cs`` a ``text_en`` a administrace jej z
těchto polí čte i zapisuje. Uložení odstávky proto nemění ``.po`` ani ``.mo``
soubor. Výchozí katalog již neslouží jako úložiště klíče
``base.odstavka.text``.

