notification_settings = {
    "E-U-01": {
        "zasilat_neaktivnim": True,
        "predmet": "AMČR: potvrďte svůj email pro registraci",
        "cesta_sablony": "X"
    },
    "S-E-A-XX": {
        "zasilat_neaktivnim": False,
        "predmet": "",
        "cesta_sablony": ""
    },
    "S-E-N-01": {
        "zasilat_neaktivnim": False,
        "predmet": "",
        "cesta_sablony": ""
    },
    "S-E-N-02": {
        "zasilat_neaktivnim": False,
        "predmet": "",
        "cesta_sablony": ""
    },
    "S-E-N-05": {
        "zasilat_neaktivnim": False,
        "predmet": "",
        "cesta_sablony": ""
    },
    "S-E-K-01": {
        "zasilat_neaktivnim": False,
        "predmet": "",
        "cesta_sablony": ""
    },
    "E-U-02": {
        "zasilat_neaktivnim": True,
        "predmet": "AMČR: uživatelský účet zaregistrován",
        "cesta_sablony": "emails/E-U-02.html"
    },
    "E-U-03": {
        "zasilat_neaktivnim": True,
        "predmet": "AMČR: uživatelský účet deaktivován nebo zrušen",
        "cesta_sablony": "emails/E-U-03.html"
    },
    "E-U-04": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR: uživatelský účet čeká na aktivaci",
        "cesta_sablony": "emails/E-U-04.html"
    },
    "E-U-05": {
        # This notification is handeled by Django authentization system
        "zasilat_neaktivnim": True,
        # Change in templates/registration/password_reset_subject.txt
        "predmet": None,
        # The path is set by system, do not change it
        "cesta_sablony": "registration/password_reset_email.html"
    },
    "E-U-06": {
        "zasilat_neaktivnim": True,
        "predmet": "AMČR: nová uživatelská role či oprávnění",
        "cesta_sablony": "emails/E-U-06.html"
    },
    "E-NZ-01": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR: projekt {ident_cely} - blíží se lhůta pro odevzdání NZ",
        "cesta_sablony": "emails/E-NZ-01.html"
    },
    "E-NZ-02": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR: projekt {ident_cely} - vypršela lhůta pro odevzdání NZ",
        "cesta_sablony": "emails/E-NZ-02.html"
    },
    "E-V-01": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR: akce {ident_cely} - vrácena k doplnění",
        "cesta_sablony": "emails/E-V-01.html"
    },
    "E-A-01": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR: projekt {ident_cely} - archivován",
        "cesta_sablony": "emails/E-A-01.html"
    },
    "E-A-02": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR: akce {ident_cely} - archivována",
        "cesta_sablony": "emails/E-A-02.html"
    },
    "E-O-01": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR: potvrzení o přijetí oznámení {ident_cely}",
        "cesta_sablony": "emails/E-O-01.html"
    },
    "E-O-02": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR: potvrzení o přijetí oznámení {ident_cely}",
        "cesta_sablony": "emails/E-O-02.html"
    },
    "E-P-01a": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR: potvrzení o schválení oznámení {ident_cely}",
        "cesta_sablony": "emails/E-P-01a.html"
    },
    "E-P-01b": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR: potvrzení o schválení oznámení {ident_cely}",
        "cesta_sablony": "emails/E-P-01b.html"
    },
    "E-P-02": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR: zapsán nový projekt {ident_cely}",
        "cesta_sablony": "emails/E-P-02.html"
    },
    "E-P-03a": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR: registrace terénního zásahu {ident_cely}",
        "cesta_sablony": "emails/E-P-03a.html"
    },
    "E-P-03b": {
        "zasilat_neaktivnim": False,
        "predmet": "IS AMČR: registrace terénního zásahu {ident_cely}",
        "cesta_sablony": "emails/E-P-03b.html"
    },
    "E-P-07": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR: projekt {ident_cely} - žádost o odhlášení",
        "cesta_sablony": "emails/E-P-07.html"
    },
    "E-P-04": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR: projekt {ident_cely} - zrušen",
        "cesta_sablony": "emails/E-P-04.html"
    },
    "E-P-05": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR: projekt {ident_cely} - opětovně zapsán",
        "cesta_sablony": "emails/E-P-05.html"
    },
    "E-P-06a": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR: zrušení projektu {ident_cely}",
        "cesta_sablony": "emails/E-P-06a.html"
    },
    "E-P-06b": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR: zrušení projektu {ident_cely}",
        "cesta_sablony": "emails/E-P-06b.html"
    },
    "E-N-01": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR-PAS: nové samostatné nálezy ke schválení",
        "cesta_sablony": "emails/E-N-01.html"
    },
    "E-N-02": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR-PAS: nálezy byly archivovány",
        "cesta_sablony": "emails/E-N-02.html"
    },
    "E-N-03": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR-PAS: samostatný nález {ident_cely} vrácen k doplnění",
        "cesta_sablony": "emails/E-N-03.html"
    },
    "E-N-04": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR-PAS: samostatný nález {ident_cely} vrácen k doplnění",
        "cesta_sablony": "emails/E-N-03.html"
    },
    "E-N-05": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR-PAS: nový spolupracovník",
        "cesta_sablony": "emails/E-N-05.html"
    },
    "E-N-06": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR-PAS: spolupráce potvrzena",
        "cesta_sablony": "emails/E-N-06.html"
    },
    "E-K-01": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR - Knihovna 3D: dokument {ident_cely} byl archivován",
        "cesta_sablony": "emails/E-K-01.html"
    },
    "E-K-02": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR - Knihovna 3D: dokument {ident_cely} byl vrácen k doplnění",
        "cesta_sablony": "emails/E-K-02.html"
    }
}
