Přidělování ident_cely
=======================

Každému záznamu je na základě jeho logiky přiřazen ident_cely.

========
Projekt
========

Dočasný ident
---------------

* Přiřazuje se pro projekty vytvořené na základě oznámení

* Logika složení je: "X-" + region (M anebo C) + "-" + devítimístné číslo (id ze sekvence `projekt_xident_seq` doplněné nulami na 9 číslic)

* Příklad: "X-M-000001234"

* Kód: https://github.com/ARUP-CAS/aiscr-webamcr/blob/dev/webclient/core/ident_cely.py#L44 `get_temporary_project_ident`

Permanentní ident
--------------------

* Přiděluje se projektům vytvořeným registrovanými uživateli AMCR a po schválení projektu (pokud projekt ještě nemá stálou identitu)

* Logika složení je: region (M anebo C) + "-" + rok + číslo sekvence z tabulky `projekt_sekvence` doplněné nulami na 5 číslic

* Příklad: "M-202100034"

* Při překročení maximálního pořadového čísla (99999) se uživateli na webu zobrazí chybové hlášení.

* Kód: https://github.com/ARUP-CAS/aiscr-webamcr/blob/dev/webclient/projekt/models.py#L484 `set_permanent_ident_cely`

Projektová akce
----------------

* Je určena pro archeologickou dokumentaci projektu

* Logika složení je: ident_cely projektu + písmeno abecedy v pořadí od A do Z
  
* Příklad: "M-202100034A"

* Pokud je překročen maximální počet akcí pro projekt (26), zobrazí se na webu chybová zpráva

* Kód: https://github.com/ARUP-CAS/aiscr-webamcr/blob/dev/webclient/core/ident_cely.py#L55 `get_project_event_ident`

========
Dokument
========
Dočasný ident
--------------

* Přiřazení k vytvořeným dokumentům a 3D modelům
  
* Logika složení je: "X-" + region (M anebo C) + "-" + rada (TX/DD/3D...) + "-" + devítimístné číslo (id ze sekvence `dokument_xident_seq` doplněno na 9 čísel nulami)

* Příklad: "X-M-TX-000000034"
  
* Kód: https://github.com/ARUP-CAS/aiscr-webamcr/blob/dev/webclient/core/ident_cely.py#L103 `get_temp_dokument_ident`

Permanentní ident
------------------

* Přiřazení k dokumentům při archivaci. platí také pro potomky (soubory, části dokumentu a soubory)
  
* Logika složení je: region- (M/C) + rada (TX/DD/3D) + "-" + rok + číslo sekvence z tabulky `dokument_sekvence` doplněno na 5 čísel nulami

* Tabulka `dokument_sekvence` se automaticky doplňuje o nové sekvence

* Příklad: "M-DD-202100034"

* Při překročení maximálního pořadového čísla (99999) je uživateli vrácena chybová zpráva
  
* Kód: https://github.com/ARUP-CAS/aiscr-webamcr/blob/dev/webclient/dokument/models.py#L366 `set_permanent_ident_cely`

===============
Část Dokumentu
===============

* Přiděluje se pro části dokumentů

* Logika složení je: ident_cely dokumentu + "-D" + pořadové číslo části na dokument, doplněné nulami na 3 číslice

* Příklad: "M-DD-202100034-D001"

* Při překročení maximální části dokumentu (999) se na webu zobrazí chybové hlášení

* Kód: https://github.com/ARUP-CAS/aiscr-webamcr/blob/dev/webclient/core/ident_cely.py#L117 `get_cast_dokumentu_ident`

=====================
Dokumentační jednotka
=====================

* Přiděluje se pro dokumentační jednotku archeologického záznamu

* Logika složení je: ident_cely arch záznamu + "-D" + pořadové číslo DJ na arch záznam doplněné na 2 číslice s nulami

* Příklad: "M-202100034A-D01"

* Při překročení maximálního počtu DJ arch záznamu (99) se na webu zobrazí chybové hlášení

* Kód: https://github.com/ARUP-CAS/aiscr-webamcr/blob/dev/webclient/core/ident_cely.py#L141 `get_dj_ident`

================================
Komponenta dokumentační jednotky
================================

* Přiděluje se pro komponentu dokumentační jednotky

* Logika složení je: ident_cely arch záznamu + "-K" + pořadové číslo komponenty per arch záznam doplněné na 3 číslice s nulami

* Příklad: "M-202100034A-K001"

* Pokud je překročeno maximum komponent arch záznamu pod DJ (999), zobrazí se na webu chybové hlášení

* Kód: https://github.com/ARUP-CAS/aiscr-webamcr/blob/dev/webclient/core/ident_cely.py#L164 `get_komponenta_ident`

====================
Komponenta dokumentu
====================

* Přiděluje se pro komponentu dokumentu

* Logika složení je: ident_cely dokumentu + "-K" + pořadové číslo komponenty per arch záznam (pod DJ) doplněné na 3 číslice s nulami

* Příklad: "M-DD-202100034-K001"

* Pokud je překročeno maximum komponent u dokumentu (999), zobrazí se na webu chybové hlášení

* Kód: https://github.com/ARUP-CAS/aiscr-webamcr/blob/dev/webclient/core/ident_cely.py#L164 `get_komponenta_ident`

====
Pian
====
Dočasný ident
-------------

* Přiděluje se pro vytvořené piany

* Logika složení je: "N-" + číslo zm50 (bez "-") + "-" + devítimístné číslo (id ze sekvence `pian_xident_seq` doplněno na 9 čísel nulami)

* Příklad: "N-1224-000001234"

* Kód: https://github.com/ARUP-CAS/aiscr-webamcr/blob/dev/webclient/core/ident_cely.py#L215 `get_temporary_pian_ident`

Permanentní ident
------------------

* Přiděluje se pro potvrzené piany

* Logika složení je: "P-" + číslo zm50 (bez "-") + "-" + číslo sekvence z tabulky `pian_sekvence` (podle zm50 a katastru) doplněno na 6 čísel nulami

* Příklad: "P-1224-100321"

* Pokud je překročeno maximum sekvence (899999), zobrazí se na webu chybové hlášení

* Podkud jde o PIAN katastru, používá se odlišná řada začínající číslicí 9 (s maximem na 999999).

* Kód: https://github.com/ARUP-CAS/aiscr-webamcr/blob/dev/webclient/pian/models.py#L180 `set_permanent_ident_cely`

================
Samostatný nález
================

* Přiděluje se pro samostatný nález

* Logika složení je: ident_cely projektu + "-N" + pořadové číslo SN per projekt doplněno na 5 čísel nulami

* Příklad: "M-202100034A-N00001"

* Pokud je překročeno maximum SN u projektu (99999), zobrazí se na webu chybové hlášení

* Kód: https://github.com/ARUP-CAS/aiscr-webamcr/blob/dev/webclient/core/ident_cely.py#L227 `get_sn_ident`

===
ADB
===

* Přiděluje se pro ADB

* Logika složení je: "ADB-" + mapno pro sm5 + "-" + číslo sekvence z tabulky `adb_sekvence` (podle kladysm5) doplněno na 6 čísel nulami

* Příklad: "ADB-PRAH43-000012"

* Pri překročení maxima sekvence u ADB (999999) se vráti uživateli na web chybová hláška.

* Kód: https://github.com/ARUP-CAS/aiscr-webamcr/blob/dev/webclient/core/ident_cely.py#L251 `get_adb_ident`

============
Výškové body
============

* Přiděluje se pro Výškový bod 

* Logika složení je: ident_cely ADB + "-V" + pořadové číslo výškového bodu per ADB doplněno na 4 čísel nulami

* Příklad: "ADB-PRAH43-000012-V0001"

* Pri překročení maxima VB u ADB (9999) se vráti uživateli na web chybová hláška

* Kód: https://github.com/ARUP-CAS/aiscr-webamcr/blob/dev/webclient/adb/models.py#L117 `get_vyskovy_bod`

========
Uživatel
========
Permanentní ident
-----------------

* Logika složení je: "U-" + šestimístné číslo ze sekvence `auth_user_ident_seq` doplněno na 6 číslic.

* Příklad: "U-012345"

* Kód: https://github.com/ARUP-CAS/aiscr-webamcr/blob/dev/webclient/core/ident_cely.py#L339 `get_uzivatel_ident`

==========
Organizace
==========
Permanentní ident
-----------------

* Logika složení je: "ORG-" + šestimístné číslo ze sekvence `organizace_ident_seq` doplněno na 6 číslic.

* Příklad: "ORG-012345"

* Kód: https://github.com/ARUP-CAS/aiscr-webamcr/blob/dev/webclient/core/ident_cely.py#L345 `get_organizace_ident`

======
Osoba
======
Permanentní ident
-----------------

* Logika složení je: "OS-" + šestimístné číslo ze sekvence `osoba_ident_seq` doplněno na 6 číslic.

* Příklad: "OS-012345"

* Kód: https://github.com/ARUP-CAS/aiscr-webamcr/blob/dev/webclient/core/ident_cely.py#L351 `get_osoba_ident`

=========
Lokalita
=========
Dočasný ident
-------------

* Přiděluje se pro vytvořené lokality

* Logika složení je: "X-" + region (M anebo C) + "-" + typ + devítimístné číslo ze sekvence `lokalita_xident_seq` doplněno na 9 číslic.

* Příklad: "X-M-L000123456"

* Kód: https://github.com/ARUP-CAS/aiscr-webamcr/blob/dev/webclient/core/ident_cely.py#L298 `get_temp_lokalita_ident`

Permanentní ident
------------------

* Přiděluje se pro archivované lokality

* Logika složení je: region (M anebo C) + "-" + typ + sedmimístné číslo ze sekvence `lokalita_xident_seq` doplňeno na 7 číslic.

* Příklad: "C-K9000904"

* Pri překročení maxima čísla sekvence (9999999) se vráti uživateli na web chybová hláška

* Kód: https://github.com/ARUP-CAS/aiscr-webamcr/blob/dev/webclient/arch_z/models.py#L296 `set_lokalita_permanent_ident_cely`

================
Samostatná akce
================
Dočasný ident
-------------

* Přiděluje se pro vytvořené samostatné akce

* Logika složení je: "X-" + region (M anebo C) + "-9" + devítimístné číslo ze sekvence `akce_xident_seq` doplněno na 9 číslic + "A".

* Příklad: "X-M-9000123456A"

* Kód: https://github.com/ARUP-CAS/aiscr-webamcr/blob/dev/webclient/core/ident_cely.py#L310 `get_temp_akce_ident`

Permanentní ident
------------------

* Přiděluje se pro archivované samostatné akce

* Logika složení je: region (M anebo C) + "-9" + typ + číslo sekvence z tabulky `akce_sekvence` doplněno na 6 čísel nulami + "A".

* Příklad: "M-9123456A"

* Při překročení maxima čísla sekvence (999999) se vráti uživateli na web chybová hláška

* Kód: https://github.com/ARUP-CAS/aiscr-webamcr/blob/dev/webclient/arch_z/models.py#L655 `get_akce_ident`


================
Externí zdroj
================
Dočasný ident
-------------

* Přiděluje se pro vytvořené externí zdroje

* Logika složení je: "X-BIB" + devítimístné číslo ze sekvence `externi_zdroj_xident_seq` doplněno na 9 číslic.

* Příklad: "X-BIB-000123456"

* Kód: https://github.com/ARUP-CAS/aiscr-webamcr/blob/dev/webclient/core/ident_cely.py#L321 `get_temp_ez_ident`

Permanentní ident
------------------

* Přiděluje se pro archivované externí zdroje

* Logika složení je: "BIB" + číslo sekvence z tabulky `externi_zdroj_sekvence` doplněno na 7 čísel nulami.

* Příklad: "BIB-1234567"

* Pri překročení maxima čísla sekvence (9999999) se vráti uživateli na web chybová hláška

* Kód: https://github.com/ARUP-CAS/aiscr-webamcr/blob/dev/webclient/ez/models.py#L214 `get_perm_ez_ident`
