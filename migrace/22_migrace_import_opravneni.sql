-- Import pre Badatele
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/adb/detail/<str:ident_cely>', 1)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'VLASTNI',
        null,
        null,
        null,
        (
            select id
            from opr
        )
    ),
    (
        'STAV',
        'operator.eq',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/adb/smazat/<str:ident_cely>', 1)
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'VLASTNI',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        1,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/adb/zapsat/<str:dj_ident_cely>', 1)
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'VLASTNI',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        1,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/arch_z/archivovat/<str:ident_cely>', 1)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'NIC',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/arch_z/detail/<str:ident_cely>', 1)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'VLASTNI',
        null,
        null,
        null,
        (
            select id
            from opr
        )
    ),
    (
        'STAV',
        'operator.eq',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/arch_z/edit/<str:ident_cely>', 1)
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'VLASTNI',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        1,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/arch_z/odeslat/<str:ident_cely>', 1)
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'VLASTNI',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        1,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES (
            '/arch_z/odpojit/dokument/<str:ident_cely>/<str:arch_z_ident_cely>',
            1
        )
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'VLASTNI',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        1,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES (
            '/arch_z/pripojit/dokument/<str:arch_z_ident_cely>',
            1
        )
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'VLASTNI',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        1,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES (
            '/arch_z/pripojit/dokument/<str:arch_z_ident_cely>/<str:proj_ident_cely>',
            1
        )
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'NIC',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/arch_z/smazat/<str:ident_cely>', 1)
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'VLASTNI',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        1,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/arch_z/vratit/<str:ident_cely>', 1)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'NIC',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/arch_z/zapsat/<str:projekt_ident_cely>', 1)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'NIC',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dj/detail/<str:ident_cely>', 1)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'VLASTNI',
        null,
        null,
        null,
        (
            select id
            from opr
        )
    ),
    (
        'STAV',
        'operator.eq',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dj/smazat/<str:ident_cely>', 1)
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'VLASTNI',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        1,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dj/zapsat/<str:arch_z_ident_cely>', 1)
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'VLASTNI',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        1,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dokument/archivovat/<str:ident_cely>', 1)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'NIC',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dokument/detail/<str:ident_cely>', 1)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'VLASTNI',
        null,
        null,
        null,
        (
            select id
            from opr
        )
    ),
    (
        'STAV',
        'operator.eq',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dokument/dokumenty/', 1)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'VLASTNI',
        null,
        null,
        null,
        (
            select id
            from opr
        )
    ),
    (
        'STAV',
        'operator.eq',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dokument/edit/<str:ident_cely>', 1)
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'VLASTNI',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'X-ID',
        null,
        null,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dokument/odeslat/<str:ident_cely>', 1)
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'VLASTNI',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'X-ID',
        null,
        null,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dokument/smazat/<str:ident_cely>', 1)
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'VLASTNI',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'X-ID',
        null,
        null,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dokument/vratit/<str:ident_cely>', 1)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'NIC',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dokument/zapsat/<str:arch_z_ident_cely>', 1)
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'VLASTNI',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        1,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/heslar/katastry/', 1)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/historie/arch_z/<str:ident_cely>', 1)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'VLASTNI',
        null,
        null,
        null,
        (
            select id
            from opr
        )
    ),
    (
        'STAV',
        'operator.eq',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/historie/dokument/<str:ident_cely>', 1)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'VLASTNI',
        null,
        null,
        null,
        (
            select id
            from opr
        )
    ),
    (
        'STAV',
        'operator.eq',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/historie/projekt/<str:ident_cely>', 1)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'NIC',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/komponenta/detail/<str:ident_cely>', 1)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'VLASTNI',
        null,
        null,
        null,
        (
            select id
            from opr
        )
    ),
    (
        'STAV',
        'operator.eq',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/komponenta/smazat/<str:ident_cely>', 1)
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'VLASTNI',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        1,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/komponenta/zapsat/<str:dj_ident_cely>', 1)
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'VLASTNI',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        1,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/nalez/edit-objekt/<str:komp_ident_cely>', 1)
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'VLASTNI',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        1,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/nalez/edit-predmet/<str:komp_ident_cely>', 1)
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'VLASTNI',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        1,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/oznameni/', 1)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/oznameni/get-katastr-from-point', 1)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/', 1)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'NIC',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/archivovat/<str:ident_cely>', 1)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'NIC',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/create', 1)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'NIC',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/detail/<str:ident_cely>', 1)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'NIC',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/get-points-arround-point', 1)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'NIC',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/list', 1)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'NIC',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES (
            '/projekt/navrhnout-ke-zruseni/<str:ident_cely>',
            1
        )
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'NIC',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/prihlasit/<str:ident_cely>', 1)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'NIC',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/schvalit/<str:ident_cely>', 1)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'NIC',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/smazat/<str:ident_cely>', 1)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'NIC',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/ukoncit-v-terenu/<str:ident_cely>', 1)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'NIC',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/uzavrit/<str:ident_cely>', 1)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'NIC',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES (
            '/projekt/vratit-navrh-zruseni/<str:ident_cely>',
            1
        )
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'NIC',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/vratit/<str:ident_cely>', 1)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'NIC',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/zahajit-v-terenu/<str:ident_cely>', 1)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'NIC',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/zrusit/<str:ident_cely>', 1)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'NIC',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/upload-file/post', 1)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/upload_file/dokument/<str:ident_cely>', 1)
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'VLASTNI',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'X-ID',
        null,
        null,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/upload_file/projekt/<str:ident_cely>', 1)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'NIC',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/uzivatel/osoba/create', 1)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/uzivatel/osoby/', 1)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
--import pre arccheologa
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/adb/detail/<str:ident_cely>', 2)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'ORGANIZACE',
        null,
        null,
        null,
        (
            select id
            from opr
        )
    ),
    (
        'STAV',
        'operator.eq',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/adb/smazat/<str:ident_cely>', 2)
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'ORGANIZACE',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        1,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/adb/zapsat/<str:dj_ident_cely>', 2)
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'ORGANIZACE',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        1,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/arch_z/archivovat/<str:ident_cely>', 2)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'NIC',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/arch_z/detail/<str:ident_cely>', 2)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'ORGANIZACE',
        null,
        null,
        null,
        (
            select id
            from opr
        )
    ),
    (
        'STAV',
        'operator.eq',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/arch_z/edit/<str:ident_cely>', 2)
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'ORGANIZACE',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        1,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/arch_z/odeslat/<str:ident_cely>', 2)
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'ORGANIZACE',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        1,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES (
            '/arch_z/odpojit/dokument/<str:ident_cely>/<str:arch_z_ident_cely>',
            2
        )
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'ORGANIZACE',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        1,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES (
            '/arch_z/pripojit/dokument/<str:arch_z_ident_cely>',
            2
        )
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'ORGANIZACE',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        1,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES (
            '/arch_z/pripojit/dokument/<str:arch_z_ident_cely>/<str:proj_ident_cely>',
            2
        )
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'ORGANIZACE',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        1,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/arch_z/smazat/<str:ident_cely>', 2)
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'ORGANIZACE',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        1,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/arch_z/vratit/<str:ident_cely>', 2)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'NIC',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/arch_z/zapsat/<str:projekt_ident_cely>', 2)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'ORGANIZACE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dj/detail/<str:ident_cely>', 2)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'ORGANIZACE',
        null,
        null,
        null,
        (
            select id
            from opr
        )
    ),
    (
        'STAV',
        'operator.eq',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dj/smazat/<str:ident_cely>', 2)
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'ORGANIZACE',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        1,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dj/zapsat/<str:arch_z_ident_cely>', 2)
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'ORGANIZACE',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        1,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dokument/archivovat/<str:ident_cely>', 2)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'NIC',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dokument/detail/<str:ident_cely>', 2)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'ORGANIZACE',
        null,
        null,
        null,
        (
            select id
            from opr
        )
    ),
    (
        'STAV',
        'operator.eq',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dokument/dokumenty/', 2)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'ORGANIZACE',
        null,
        null,
        null,
        (
            select id
            from opr
        )
    ),
    (
        'STAV',
        'operator.eq',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dokument/edit/<str:ident_cely>', 2)
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'ORGANIZACE',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'X-ID',
        null,
        null,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dokument/odeslat/<str:ident_cely>', 2)
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'ORGANIZACE',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'X-ID',
        null,
        null,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dokument/smazat/<str:ident_cely>', 2)
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'ORGANIZACE',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'X-ID',
        null,
        null,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dokument/vratit/<str:ident_cely>', 2)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'NIC',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dokument/zapsat/<str:arch_z_ident_cely>', 2)
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'ORGANIZACE',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        1,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/heslar/katastry/', 2)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/historie/arch_z/<str:ident_cely>', 2)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'ORGANIZACE',
        null,
        null,
        null,
        (
            select id
            from opr
        )
    ),
    (
        'STAV',
        'operator.eq',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/historie/dokument/<str:ident_cely>', 2)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'ORGANIZACE',
        null,
        null,
        null,
        (
            select id
            from opr
        )
    ),
    (
        'STAV',
        'operator.eq',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/historie/projekt/<str:ident_cely>', 2)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/komponenta/detail/<str:ident_cely>', 2)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'ORGANIZACE',
        null,
        null,
        null,
        (
            select id
            from opr
        )
    ),
    (
        'STAV',
        'operator.eq',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/komponenta/smazat/<str:ident_cely>', 2)
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'ORGANIZACE',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        1,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/komponenta/zapsat/<str:dj_ident_cely>', 2)
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'ORGANIZACE',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        1,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/nalez/edit-objekt/<str:komp_ident_cely>', 2)
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'ORGANIZACE',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        1,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/nalez/edit-predmet/<str:komp_ident_cely>', 2)
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'ORGANIZACE',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        1,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/oznameni/', 2)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/oznameni/get-katastr-from-point', 2)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/', 2)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/archivovat/<str:ident_cely>', 2)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'NIC',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/create', 2)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/detail/<str:ident_cely>', 2)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/get-points-arround-point', 2)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/list', 2)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/prihlasit/<str:ident_cely>', 2)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        1,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/schvalit/<str:ident_cely>', 2)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'NIC',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/smazat/<str:ident_cely>', 2)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'NIC',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/ukoncit-v-terenu/<str:ident_cely>', 2)
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'ORGANIZACE',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        3,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/uzavrit/<str:ident_cely>', 2)
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'ORGANIZACE',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        4,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES (
            '/projekt/vratit-navrh-zruseni/<str:ident_cely>',
            2
        )
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'NIC',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/vratit/<str:ident_cely>', 2)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'NIC',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/zahajit-v-terenu/<str:ident_cely>', 2)
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'ORGANIZACE',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        2,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/zrusit/<str:ident_cely>', 2)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'NIC',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/upload-file/post', 2)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/upload_file/dokument/<str:ident_cely>', 2)
    returning id
),
kon_opr as (
    INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
    VALUES (
            'ORGANIZACE',
            (
                select id
                from opr
            )
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'X-ID',
        null,
        null,
(
            select id
            from kon_opr
        ),
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/uzivatel/osoba/create', 2)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/uzivatel/osoby/', 2)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
--import pre archivare
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/adb/detail/<str:ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/adb/smazat/<str:ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.lt',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/adb/zapsat/<str:dj_ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.lt',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/arch_z/archivovat/<str:ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        2,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/arch_z/detail/<str:ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/arch_z/edit/<str:ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.lt',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/arch_z/odeslat/<str:ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        1,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES (
            '/arch_z/odpojit/dokument/<str:ident_cely>/<str:arch_z_ident_cely>',
            3
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.lt',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES (
            '/arch_z/pripojit/dokument/<str:arch_z_ident_cely>',
            3
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.lt',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES (
            '/arch_z/pripojit/dokument/<str:arch_z_ident_cely>/<str:proj_ident_cely>',
            3
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.lt',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/arch_z/smazat/<str:ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/arch_z/vratit/<str:ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.gt',
        1,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/arch_z/zapsat/<str:projekt_ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dj/detail/<str:ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dj/smazat/<str:ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.lt',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dj/zapsat/<str:arch_z_ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.lt',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dokument/archivovat/<str:ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        2,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dokument/detail/<str:ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dokument/dokumenty/', 3)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dokument/edit/<str:ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.lt',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dokument/odeslat/<str:ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        2,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dokument/smazat/<str:ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dokument/vratit/<str:ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.gt',
        1,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dokument/zapsat/<str:arch_z_ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.lt',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/heslar/katastry/', 3)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/historie/arch_z/<str:ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/historie/dokument/<str:ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/historie/projekt/<str:ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/komponenta/detail/<str:ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/komponenta/smazat/<str:ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.lt',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/komponenta/zapsat/<str:dj_ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.lt',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/nalez/edit-objekt/<str:komp_ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.lt',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/nalez/edit-predmet/<str:komp_ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.lt',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/oznameni/', 3)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/oznameni/get-katastr-from-point', 3)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/', 3)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/archivovat/<str:ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        5,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/create', 3)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/detail/<str:ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/get-points-arround-point', 3)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/list', 3)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES (
            '/projekt/navrhnout-ke-zruseni/<str:ident_cely>',
            3
        )
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/prihlasit/<str:ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        1,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/schvalit/<str:ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        0,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/smazat/<str:ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/ukoncit-v-terenu/<str:ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/uzavrit/<str:ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        4,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES (
            '/projekt/vratit-navrh-zruseni/<str:ident_cely>',
            3
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        7,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/zahajit-v-terenu/<str:ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        2,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/zrusit/<str:ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        7,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/upload-file/post', 3)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/upload_file/dokument/<str:ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.lt',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/upload_file/projekt/<str:ident_cely>', 3)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/uzivatel/osoba/create', 3)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/uzivatel/osoby/', 3)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
--import pre admina
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/adb/detail/<str:ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/adb/smazat/<str:ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.lt',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/adb/zapsat/<str:dj_ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.lt',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/arch_z/archivovat/<str:ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        2,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/arch_z/detail/<str:ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/arch_z/edit/<str:ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.lt',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/arch_z/odeslat/<str:ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        1,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES (
            '/arch_z/odpojit/dokument/<str:ident_cely>/<str:arch_z_ident_cely>',
            4
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.lt',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES (
            '/arch_z/pripojit/dokument/<str:arch_z_ident_cely>',
            4
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.lt',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES (
            '/arch_z/pripojit/dokument/<str:arch_z_ident_cely>/<str:proj_ident_cely>',
            4
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.lt',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/arch_z/smazat/<str:ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/arch_z/vratit/<str:ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.gt',
        1,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/arch_z/zapsat/<str:projekt_ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dj/detail/<str:ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dj/smazat/<str:ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.lt',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dj/zapsat/<str:arch_z_ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.lt',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dokument/archivovat/<str:ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        2,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dokument/detail/<str:ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dokument/dokumenty/', 4)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dokument/edit/<str:ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.lt',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dokument/odeslat/<str:ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        2,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dokument/smazat/<str:ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dokument/vratit/<str:ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.gt',
        1,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/dokument/zapsat/<str:arch_z_ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.lt',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/heslar/katastry/', 4)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/historie/arch_z/<str:ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/historie/dokument/<str:ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/historie/projekt/<str:ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/komponenta/detail/<str:ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/komponenta/smazat/<str:ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.lt',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/komponenta/zapsat/<str:dj_ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.lt',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/nalez/edit-objekt/<str:komp_ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.lt',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/nalez/edit-predmet/<str:komp_ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.lt',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/oznameni/', 4)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/oznameni/get-katastr-from-point', 4)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/', 4)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/archivovat/<str:ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        5,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/create', 4)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/detail/<str:ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/get-points-arround-point', 4)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/list', 4)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES (
            '/projekt/navrhnout-ke-zruseni/<str:ident_cely>',
            4
        )
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/prihlasit/<str:ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        1,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/schvalit/<str:ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        0,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/smazat/<str:ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/ukoncit-v-terenu/<str:ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/uzavrit/<str:ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        4,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES (
            '/projekt/vratit-navrh-zruseni/<str:ident_cely>',
            4
        )
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        7,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/zahajit-v-terenu/<str:ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        2,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/projekt/zrusit/<str:ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.eq',
        7,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/upload-file/post', 4)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/upload_file/dokument/<str:ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(
        druh_opravneni,
        porovnani_stavu,
        stav,
        vazba_na_konkretni_opravneni,
        parent_opravneni
    )
VALUES (
        'STAV',
        'operator.lt',
        3,
        null,
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/upload_file/projekt/<str:ident_cely>', 4)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/uzivatel/osoba/create', 4)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );
With opr as (
    INSERT INTO OPRAVNENI (adresa_v_aplikaci, role)
    VALUES ('/uzivatel/osoby/', 4)
    returning id
)
INSERT INTO opravneni_konkretni(druh_opravneni, parent_opravneni)
VALUES (
        'VSE',
        (
            select id
            from opr
        )
    );