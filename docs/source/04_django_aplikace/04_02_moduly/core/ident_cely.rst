CORE ident_cely
===============

Modul ident_cely.

Funkce
------

.. py:function:: get_next_sequence(sequence_name)

   Popis není k dispozici.

.. py:function:: get_temporary_project_ident(region)

   Metoda pro výpočet dočasného identu projektu. Přiděluje se pro projekty vytvoření v rámci oznámení.

   Logika složení je: "X-" + region (M anebo C) + "-" + 9 místne číslo (id ze sequence projekt_xident_seq doplněno na 9 čísel nulama)
   Příklad: "X-M-000001234"

.. py:function:: get_project_event_ident(project)

   Metoda pro výpočet identu projektové akce.

   Logika složení je: ident_cely projektu + písmeno abecedy v posloupnosti od A po Z
   Pri překročení maxima čísla sekvence (99999) se vráti uživateli na web chybová hláška.
   Příklad: "M-202100034A"

.. py:function:: get_dokument_rada(typ, material)

   Metoda pro získaní rady dokumentu podle typu a materiálu dokumentu.

.. py:function:: get_temp_dokument_ident(rada, region)

   Metoda pro výpočet dočasného identu dokumentu.

   Logika složení je: "X-" + region (M anebo C) + "-" + řada (TX/DD/3D) + "-" 9 místní číslo (id ze sequence dokument_xident_seq doplněno na 9 čísel nulami)
   Příklad: "X-M-TX-000000034"

.. py:function:: get_cast_dokumentu_ident(dokument)

   Metoda pro výpočet identu části dokumentu.

   Logika složení je: ident_cely dokumentu + "-D" + pořadové číslo části per dokument doplněno na 3 číslice nulami.
   Pri překročení maxima DJ u dokumentu (999) se vráti uživateli na web chybová hláška.
   Příklad: "M-DD-202100034-D001"

.. py:function:: get_dj_ident(event)

   Metoda pro výpočet identu dokumentační jednotky akce.

   Logika složení je: ident_cely arch záznamu + "-D" + pořadové číslo DJ per arch záznam doplněno na 2 číslice nulami.
   Pri překročení maxima DJ u arch záznamu (99) se vráti uživateli na web chybová hláška.
   Příklad: "M-202100034A-D01"

.. py:function:: get_komponenta_ident(zaznam, fedora_transaction)

   Metoda pro výpočet identu komponenty DJ a dokument části.

   Logika složení je: ident_cely arch záznamu anebo dokumentu + "-D" + pořadové číslo komponenty per záznam doplněno na 3 číslice nulama.
   Pri prekročení maxima komponent u záznamu (999) se vráti uživateli na web chybová hláška.
   Příklad: "M-202100034A-K001", "M-DD-202100034-K001"

.. py:function:: get_sm_from_point(point)

   Metoda pro získání kladu sm5 pro pian z bodu.

.. py:function:: get_temporary_pian_ident(zm50)

   Metoda pro výpočet dočasného identu pianu.

   Logika složení je: "N-" + číslo zm50 (bez "-") + "-" + 9 místní číslo ze sekvence pian_xident_seq doplněno na 9 číslic.
   Příklad: "N-1224-000123456"

.. py:function:: get_sn_ident(projekt)

   Metoda pro výpočet identu samostatního nálezu projektu.

   Logika složení je: ident_cely projektu + "-N" + pořadové číslo SN per projekt doplněno na 5 číslic nulama.
   Pri prekročení maxima SN u projektu (99999) se vráti uživateli na web chybová hláška.
   Příklad: "M-202100034A-N00001"

.. py:function:: get_adb_ident(pian)

   Metoda pro výpočet identu ADB.

   Logika složení je: "ADB-" + mapno pro sm5 + "-" + číslo sekvence z tabulky 'adb_sekvence' (podle kladysm5) doplněno na 6 číslic nulama.
   Pri prekročení maxima sekvence u ADB (999999) se vráti uživateli na web chybová hláška.
   Příklad: "ADB-PRAH43-000012"

.. py:function:: get_temp_lokalita_ident(typ, region)

   Metoda pro výpočet dočasného identu lokality.

   Logika složení je: "X-" + region (M anebo C) + "-" + typ + 9 místní číslo ze sekvence lokalita_xident_seq doplněno na 9 číslic.

   Příklad: "X-M-L000123456"

.. py:function:: get_temp_akce_ident(region)

   Metoda pro výpočet dočasného identu samostatný akce.

   Logika složení je: "X-" + region (M anebo C) + "-9" + 9 místní číslo ze sekvence akce_xident_seq doplněno na 9 číslic -A.

   Příklad: "X-M-9000123456A"

.. py:function:: get_temp_ez_ident()

   Metoda pro výpočet dočasného identu externího zdroje.

   Logika složení je: "X-BIB" + 9 místní číslo ze sekvence externi_zdroj_xident_seq doplněno na 9 číslic.

   Příklad: "X-BIB-000123456"

.. py:function:: get_next_sequence_integrity_check(object_class)

   Popis není k dispozici.

.. py:function:: get_heslar_ident()

   Metoda pro výpočet identu hesláře.

.. py:function:: get_uzivatel_ident()

   Metoda pro výpočet identu uživatele.

.. py:function:: get_organizace_ident()

   Metoda pro výpočet identu organizce.

.. py:function:: get_osoba_ident()

   Metoda pro výpočet identu osoby.

.. py:function:: get_record_from_ident(ident_cely)

   Funkce pro získaní záznamu podle ident cely.
