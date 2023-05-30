Pridelovani ident_cely
=======================

Kazdy zaznam ma prideleny ident_cely na zaklade svojej logiky.

========
Projekt
========

Docasny ident
---------------

* Prideluje sa pre projekty vytvorene v ramci oznameni

* Logika slozeni je: "X-" + region (M alebo C) + "-" + 9 mistne cislo (id ze sequence `projekt_xident_seq` doplnene na 9 cisel nulami)

* Priklad: "X-M-000001234"

* Kod: `webclient/core/ident_cely.py/get_temporary_project_ident`

Permanentny ident
--------------------

* Prideluje sa pre projekty vytvorene prihlasenymi uzivateli AMCR a pri schvaleni projektu (ak projekt uz nema permanentny ident)

* Logika slozeni je: region (M alebo C) + "-" + rok + cislo sekvence z tabulky 'projekt_sekvence' doplnene na 5 cisel nulami

* Priklad: "M-202100034"

* Pri prekroceni maxima cisla sekvence (99999) se vrati uzivateli na web chybova hlaska

* Kod: `webclient/projekt/models.py/set_permanent_ident_cely`

Projekt akcia
--------------

* Prideluje sa pre projektove archeologicke zaznamy

* Logika slozeni je: ident_cely projektu + pismeno abecedy v postupnosti od A po Z

* Priklad: "M-202100034A"

* Pri prekroceni maxima akcii u projektu (26) sa zobrazi chybova hlaska na webe

* Kod: `webclient/core/ident_cely.py/get_project_event_ident`

========
Dokument
========
Docasny ident
--------------

* Prideluje sa pre vytvorene dokumenty a 3D modely

* Logika slozeni je: "X-" + region (M alebo C) + "-" + rada (TX/DD/3D) + "-" + 9 místne číslo (id ze sequence `dokument_xident_seq` doplněno na 9 čísel nulama)

* Priklad: "X-M-TX-000000034"
* 
* Kod: `webclient/core/ident_cely.py/get_temp_dokument_ident`

Permanentny ident
------------------

* Prideluje sa pre dokumenty pri archivaci. astavy sa i pro casti a komponenty

* Logika slozeni je: region- (M/C) + rada (TX/DD/3D) + "-" + rok + cislo sekvence z tabulky `dokument_sekvence` doplnene na 5 cisel nulami

* Tabulka `dokument_sekvence` se automaticky doplnuje o nova sekvence

* Priklad: "M-DD-202100034"

* Pri prekroceni maxima cisla sekvence (99999) se vrati uzivateli na web chybova hlaska

* Kod: `webclient/dokumenty/models.py/set_permanent_ident_cely`

===============
Cast Dokumentu
===============

* Prideluje sa pre casti dokumentu

* Logika slozeni je: ident_cely dokumentu + "-D" + poradove cislo casti per dokument doplnene na 3 cislice nulami

* Priklad: "M-DD-202100034-D001"

* Pri prekroceni maxima casti u dokumentu (999) sa zobrazi chybova hlaska na webe

* Kod: `webclient/core/ident*cely.py/get*cast*dokumentu*ident`

=====================
Dokumentacni jednotka
=====================

* Prideluje sa pre dokumentacnu jednotku archeologickeho zaznamu

* Logika slozeni je: ident_cely arch zaznamu + "-D" + poradove cislo DJ per arch zaznam doplnene na 2 cislice nulami

* Priklad: "M-202100034A-D01"

* Pri prekroceni maxima DJ u arch zaznamu (99) sa zobrazi chybova hlaska na webe

* Kod: `webclient/core/ident*cely.py/get*dj_ident`

================================
Komponenta dokumentacni jednotky
================================

* Prideluje sa pre komponentu dokumentacni jednotky

* Logika slozeni je: ident_cely arch zaznamu + "-K" + poradove cislo komponenty per arch zaznam (pod DJ) doplnene na 3 cislice nulami

* Priklad: "M-202100034A-K001"

* Pri prekroceni maxima komponent u arch zaznamu pod DJ (999) sa zobrazi chybova hlaska na webe

* Kod: `webclient/core/ident*cely.py/get*komponenta_ident`

====================
Komponenta dokumentu
====================

* Prideluje sa pre komponentu dokumentu

* Logika slozeni je: ident_cely dokumentu + "-K" + poradove cislo komponenty per arch zaznam (pod DJ) doplnene na 3 cislice nulami

* Priklad: "M-DD-202100034-K001"

* Pri prekroceni maxima komponent u dokumentu (999) sa zobrazi chybova hlaska na webe

* Kod: `webclient/core/ident*cely.py/get*dokument*komponenta*ident`

====
Pian
====
Docasny ident
-------------

* Prideluje sa pre vytvorene piany

* Logika slozeni je: "N-" + cislo zm50 (bez "-") + "-" + 6 mistne cislo (první volné číslo pro zm50)

* Priklad: "N-1224-001234"

* Pri prekroceni maxima pian pre dane zm50 (999999) sa zobrazi chybova hlaska na webe

* Kod: `webclient/core/ident*cely.py/get*temporary*pian*ident`

Permanentny ident
------------------

* Prideluje sa pre potvrdene piany

* Logika slozeni je: "P-" + cislo zm50 (bez "-") + "-" + cislo sekvence z tabulky 'pian_sekvence' (podle zm50 a katastru) doplnene na 6 cisel nulami

* Priklad: "P-1224-100321"

* Pri prekroceni maxima cisla sekvence (999999) se vrati uzivateli na web chybova hlaska

* Kod: `webclient/pian/models.py/set*permanent*ident_cely`

================
Samostatny nalez
================

* Prideluje sa pre samostatny nalez

* Logika slozeni je: ident_cely projektu + "-N" + poradove cislo SN per projekt doplnene na 5 cislice nulami

* Priklad: "M-202100034A-N00001"

* Pri prekroceni maxima SN u projektu (99999) sa zobrazi chybova hlaska na webe

* Kod: `webclient/core/ident*cely.py/get*sn_ident`

===
ADB
===

* Prideluje sa pre ADB

* Logika slozeni je: "ADB-" + mapno pre sm5 + "-" + cislo sekvence z tabulky 'adb_sekvence' (podle kladysm5) doplnene na 6 cisel nulami

* Priklad: "ADB-PRAH43-000012"

* Pri prekroceni maxima SN u projektu (999999) sa zobrazi chybova hlaska na webe

* Kod: `webclient/core/ident*cely.py/get*adb_ident`

============
Vyskove body
============

* Prideluje sa pre Vyskovy bod 

* Logika slozeni je: ident_cely ADB + "-V" + poradove cislo vyskoveho bodu per ADB doplnene na 4 cislice nulami

* Priklad: "ADB-PRAH43-000012-V0001"

* Pri prekroceni maxima VB u adb (9999) sa zobrazi chybova hlaska na webe

* Kod: `webclient/adb/models.py/get*vyskovy*bod`

========
Uzivatel
========
Ident cely
-----------

* Přiděluje se v databázi

* Logika slozeni je: ident_cely "U" + poradove cislo uzivatele doplnene na 6 cislice nulami

* Kod: auth*user.ident*cely

=========
Lokalita
=========
Docasny ident
-------------

* Prideluje sa pre vytvorene lokality

* Logika složení je: "X-" + region (M anebo C) + "-" + typ + 9 místne číslo ze sekvence `lokalita_xident_seq` doplňeno na 9 číslic.

* Příklad: "X-M-L000123456"

* Kod: `webclient/core/ident_cely.py/get_temp_lokalita_ident`

Permanentny ident
------------------

* Prideluje sa pre archivované lokality

* Logika slozeni je: region (M anebo C) + "-" + typ + 9 místne číslo ze sequnce lokalita_xident_seq doplňeno na 9 číslic.

* Priklad: "P-1224-100321"

* Pri prekroceni maxima cisla sekvence (999999) se vrati uzivateli na web chybova hlaska

* Kod: `webclient/arch_z/models.py/set_lokalita_permanent_ident_cely`

================
Samostatná akce
================
Dočasný ident
-------------

* Prideluje sa pre vytvorene samostatné akce

* Logika složení je: "X-" + region (M anebo C) + "-9" + typ + 9 místne číslo ze sekvence `akce_xident_seq` doplňeno na 9 číslic + "A".

* Příklad: "X-M-9000123456A"

* Kod: `webclient/core/ident_cely.py/get_temp_akce_ident`

Permanentny ident
------------------

* Prideluje sa pre archivované lokality

* Logika slozeni je: region (M anebo C) + "-" + typ + 9 místne číslo ze sequnce lokalita_xident_seq doplňeno na 9 číslic.

* Priklad: "P-1224-100321"

* Pri prekroceni maxima cisla sekvence (999999) se vrati uzivateli na web chybova hlaska

* Kod: `webclient/arch_z/models.py/set_lokalita_permanent_ident_cely`


================
Externí zdroj
================
Dočasný ident
-------------

* Prideluje sa pre vytvorene externé zdroje

* Logika složení je: "X-BIB" + 9 místne číslo ze sekvence `externi_zdroj_xident_seq` doplňeno na 9 číslic.

* Příklad: "X-BIB-000123456"◊

* Kod: `webclient/core/ident_cely.py/get_temp_ez_ident`

Permanentny ident
------------------

* Prideluje sa pre archivované lokality

* Logika slozeni je: region (M anebo C) + "-" + typ + 9 místne číslo ze sequnce lokalita_xident_seq doplňeno na 9 číslic.

* Priklad: "P-1224-100321"

* Pri prekroceni maxima cisla sekvence (999999) se vrati uzivateli na web chybova hlaska

* Kod: `webclient/arch_z/models.py/set_lokalita_permanent_ident_cely`