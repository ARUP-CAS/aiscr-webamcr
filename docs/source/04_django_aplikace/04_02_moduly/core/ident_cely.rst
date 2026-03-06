CORE ident_cely
===============

Modul ident_cely.

Funkce
------

.. py:function:: get_next_sequence(sequence_name)

   Vrací next sequence.

   :param sequence_name: Textový název nebo klíč ``sequence_name`` používaný v rámci operace.
   :return: Načtená data odpovídající zadaným vstupům.

.. py:function:: get_temporary_project_ident(region)

   Metoda pro výpočet dočasného identu projektu. Přiděluje se pro projekty vytvoření v rámci oznámení.

   Logika složení je: "X-" + region (M nebo C) + "-" + 9místné číslo (id ze sequence projekt_xident_seq doplněno na 9 čísel nulama)
   Příklad: "X-M-000001234"

   :param region: Parametr ``region`` vstupuje do návratové hodnoty.
   :return: Vrací výsledek operace.

.. py:function:: get_project_event_ident(project)

   Metoda pro výpočet identu projektové akce.

   Logika složení je: ident_cely projektu + písmeno abecedy v posloupnosti od A po Z
   Při překročení maxima čísla sekvence (99999) se uživateli na web vrátí chybová hláška.
   Příklad: "M-202100034A"

   :param project: Parametr ``project`` pracuje se s atributy ``ident_cely``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :return: Vrací výsledek operace.

   :raises MaximalEventCount: Vyvolá se při splnění podmínky ``len(idents) < MAXIMAL_PROJECT_EVENTS``.

.. py:function:: get_dokument_rada(typ, material)

   Metoda pro získaní rady dokumentu podle typu a materiálu dokumentu.

   :param typ: Parametr ``typ`` předává se do volání ``filter()``, ``error()``, pracuje se s atributy ``id``.
   :param material: Parametr ``material`` se předává do volání ``filter()``, ``error()``, pracuje se s atributy ``id``.

   :return: Vrací atribut objektu.
   :raises NelzeZjistitRaduError: Vyvolá se při splnění podmínky ``len(instances) == 1``.

.. py:function:: get_temp_dokument_ident(rada, region)

   Metoda pro výpočet dočasného identu dokumentu.

   Logika složení je: "X-" + region (M nebo C) + "-" + řada (TX/DD/3D) + "-" 9místné číslo (ID ze sekvence dokument_xident_seq doplněné na 9 číslic nulami)
   Příklad: "X-M-TX-000000034"

   :param rada: Parametr ``rada`` se předává do volání ``str()``.
   :param region: Parametr ``region`` se předává do volání ``str()``.

   :return: Vrací hodnotu podle větve zpracování.

.. py:function:: get_cast_dokumentu_ident(dokument)

   Metoda pro výpočet identu části dokumentu.

   Logika složení je: ident_cely dokumentu + "-D" + pořadové číslo části per dokument doplněno na 3 číslice nulami.
   Při překročení maxima DJ u dokumentu (999) se uživateli na web vrátí chybová hláška.
   Příklad: "M-DD-202100034-D001"

   :param dokument: Parametr ``dokument`` pracuje se s atributy ``casti``, ``ident_cely``.
   :return: Vrací výsledek operace.

   :raises MaximalIdentNumberError: Vyvolá se při splnění podmínky ``max_count < MAXIMUM``.

.. py:function:: get_dj_ident(event)

   Metoda pro výpočet identu dokumentační jednotky akce.

   Logika složení je: ident_cely arch záznamu + "-D" + pořadové číslo DJ per arch záznam doplněno na 2 číslice nulami.
   Při překročení maxima DJ u archeologického záznamu (99) se uživateli na web vrátí chybová hláška.
   Příklad: "M-202100034A-D01"

   :param event: Parametr ``event`` pracuje se s atributy ``dokumentacni_jednotky_akce``, ``ident_cely``.
   :return: Vrací výsledek operace.

   :raises MaximalIdentNumberError: Vyvolá se při splnění podmínky ``max_count < MAXIMAL_EVENT_DJS``.

.. py:function:: get_komponenta_ident(zaznam, fedora_transaction)

   Metoda pro výpočet identu komponenty DJ a dokument části.

   Logika složení je: ident_cely arch záznamu nebo dokumentu + "-D" + pořadové číslo komponenty per záznam doplněno na 3 číslice nulami.
   Při překročení maxima komponent u záznamu (999) se uživateli na web vrátí chybová hláška.
   Příklad: "M-202100034A-K001", "M-DD-202100034-K001"

   :param zaznam: Parametr ``zaznam`` předává se do volání ``isinstance()``, pracuje se s atributy ``dokumentacni_jednotky_akce``, ``casti``, ovlivňuje větvení podmínek.
   :param fedora_transaction: Parametr ``fedora_transaction`` slouží jako vstup pro logiku funkce ``get_komponenta_ident``.
   :return: Vrací výsledek operace.

   :raises MaximalIdentNumberError: Vyvolá se při splnění podmínky ``max_count < MAXIMAL_KOMPONENTAS``.

.. py:function:: get_sm_from_point(point)

   Metoda pro získání kladu sm5 pro pian z bodu.

   :param point: Parametr ``point`` předává se do volání ``filter()``, ``PianNotInKladysm5Error()``.

   :return: Vrací proměnná ``mapovy_list``.
   :raises PianNotInKladysm5Error: Vyvolá se při splnění podmínky ``mapovy_list.count() == 1``.

.. py:function:: get_temporary_pian_ident(zm50)

   Metoda pro výpočet dočasného identu pianu.

   Logika složení je: "N-" + číslo zm50 (bez "-") + "-" + 9 místní číslo ze sekvence pian_xident_seq doplněno na 9 číslic.
   Příklad: "N-1224-000123456"

   :param zm50: Parametr ``zm50`` se předává do volání ``str()``, pracuje se s atributy ``cislo``.
   :return: Vrací výsledek operace.

.. py:function:: get_sn_ident(projekt)

   Metoda pro výpočet identu samostatního nálezu projektu.

   Logika složení je: ident_cely projektu + "-N" + pořadové číslo SN per projekt doplněno na 5 číslic nulami.
   Při překročení maxima SN u projektu (99999) se uživateli na web vrátí chybová hláška.
   Příklad: "M-202100034A-N00001"

   :param projekt: Parametr ``projekt`` předává se do volání ``filter()``, pracuje se s atributy ``ident_cely``.
   :return: Vrací výsledek operace.

   :raises MaximalIdentNumberError: Vyvolá se při splnění podmínky ``max_count < MAXIMAL_FINDS``.

.. py:function:: get_adb_ident(pian)

   Metoda pro výpočet identu ADB.

   Logika složení je: "ADB-" + mapno pro sm5 + "-" + číslo sekvence z tabulky 'adb_sekvence' (podle kladysm5) doplněno na 6 číslic nulami.
   Při překročení maxima sekvence u ADB (999999) se uživateli na web vrátí chybová hláška.
   Příklad: "ADB-PRAH43-000012"

   :param pian: Parametr ``pian`` předává se do volání ``isinstance()``, ``Centroid()``, pracuje se s atributy ``geom``, ovlivňuje větvení podmínek.
   :return: Vrací výsledek operace.

   :raises NeznamaGeometrieError: Vyvolá se při splnění podmínky ``isinstance(pian.geom, Polygon)``.
   :raises MaximalIdentNumberError: Vyvolá se při splnění podmínky ``sequence.sekvence < MAXIMAL_ADBS``.

.. py:function:: get_temp_lokalita_ident(typ, region)

   Metoda pro výpočet dočasného identu lokality.

   Logika složení je: "X-" + region (M nebo C) + "-" + typ + 9místné číslo ze sekvence lokalita_xident_seq doplněné na 9 číslic.

   Příklad: "X-M-L000123456"

   :param typ: Parametr ``typ`` předává se do volání ``str()``.
   :param region: Parametr ``region`` se předává do volání ``str()``.

   :return: Vrací hodnotu podle větve zpracování.

.. py:function:: get_temp_akce_ident(region)

   Metoda pro výpočet dočasného identu samostatný akce.

   Logika složení je: "X-" + region (M nebo C) + "-9" + 9místné číslo ze sekvence akce_xident_seq doplněné na 9 číslic a suffix „-A“.

   Příklad: "X-M-9000123456A"

   :param region: Parametr ``region`` se předává do volání ``str()``, vstupuje do návratové hodnoty.

   :return: Vrací výsledek volání ``str()``.

.. py:function:: get_temp_ez_ident()

   Metoda pro výpočet dočasného identu externího zdroje.

   Logika složení je: "X-BIB" + 9 místní číslo ze sekvence externi_zdroj_xident_seq doplněno na 9 číslic.

   Příklad: "X-BIB-000123456"

   :return: Vrací výsledek volání ``str()``.

.. py:function:: get_next_sequence_integrity_check(object_class)

   Vrací next sequence integrity check.

   :param object_class: Parametr ``object_class`` předává se do volání ``get_next_sequence()``, pracuje se s atributy ``IDENT_PREFIX``, ``SEQUENCE_NAME``, ovlivňuje větvení podmínek.
   :return: Načtená data odpovídající zadaným vstupům.

.. py:function:: get_heslar_ident()

   Metoda pro výpočet identu hesláře.

   :return: Vrací výsledek volání ``get_next_sequence_integrity_check()``.

.. py:function:: get_uzivatel_ident()

   Metoda pro výpočet identu uživatele.

   :return: Vrací výsledek volání ``get_next_sequence_integrity_check()``.

.. py:function:: get_organizace_ident()

   Metoda pro výpočet identu organizce.

   :return: Vrací výsledek volání ``get_next_sequence_integrity_check()``.

.. py:function:: get_osoba_ident()

   Metoda pro výpočet identu osoby.

   :return: Vrací výsledek volání ``get_next_sequence_integrity_check()``.

.. py:function:: get_record_from_ident(ident_cely)

   Funkce pro získaní záznamu podle ident cely.

   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``bool()``, ``fullmatch()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``get_object_or_404()``, None.
