notification_settings = {
    "E-U-01": {
        "zasilat_neaktivnim": True,
        "predmet": "AMČR: potvrďte svůj email | AMCR: confirm your email",
        "cesta_sablony": "django_registration/activation_email_body.txt",
    },
    "S-E-A-XX": {"zasilat_neaktivnim": False, "predmet": "", "cesta_sablony": ""},
    "S-E-N-01": {"zasilat_neaktivnim": False, "predmet": "", "cesta_sablony": ""},
    "S-E-N-02": {"zasilat_neaktivnim": False, "predmet": "", "cesta_sablony": ""},
    "S-E-N-05": {"zasilat_neaktivnim": False, "predmet": "", "cesta_sablony": ""},
    "S-E-K-01": {"zasilat_neaktivnim": False, "predmet": "", "cesta_sablony": ""},
    "E-U-02": {
        "zasilat_neaktivnim": True,
        "predmet": "AMČR: uživatelský účet zaregistrován | AMCR: user account registered",
        "cesta_sablony": "emails/E-U-02.html",
    },
    "E-U-03": {
        "zasilat_neaktivnim": True,
        "predmet": "AMČR: uživatelský účet deaktivován nebo smazán | AMCR: user account deactivated or deleted",
        "cesta_sablony": "emails/E-U-03.html",
    },
    "E-U-04": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR: uživatelský účet čeká na aktivaci | AMCR: user account waiting for activation",
        "cesta_sablony": "emails/E-U-04.html",
    },
    "E-U-05": {
        # This notification is handeled by Django authentization system
        "zasilat_neaktivnim": True,
        # Change in templates/registration/password_reset_subject.txt
        "predmet": None,
        # The path is set by system, do not change it
        "cesta_sablony": "registration/password_reset_email.html",
    },
    "E-U-06": {
        "zasilat_neaktivnim": True,
        "predmet": "AMČR: nová uživatelská role či oprávnění | AMCR: new user role or permissions",
        "cesta_sablony": "emails/E-U-06.html",
    },
    "E-NZ-01": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR: projekt {ident_cely} - blíží se lhůta pro odevzdání NZ | AMCR: project {ident_cely} - report submission deadline approaching",
        "cesta_sablony": "emails/E-NZ-01.html",
    },
    "E-NZ-02": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR: projekt {ident_cely} - vypršela lhůta pro odevzdání NZ | AMCR: project {ident_cely} - report submission deadline passed",
        "cesta_sablony": "emails/E-NZ-02.html",
    },
    "E-V-01": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR: záznam {ident_cely} - vrácen k doplnění | AMCR: record {ident_cely} - returned for completion",
        "cesta_sablony": "emails/E-V-01.html",
    },
    "E-A-01": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR: projekt {ident_cely} - archivován | AMCR: project {ident_cely} - archived",
        "cesta_sablony": "emails/E-A-01.html",
    },
    "E-A-02": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR: zánam {ident_cely} - archivován | AMCR: record {ident_cely} - archived",
        "cesta_sablony": "emails/E-A-02.html",
    },
    "E-O-01": {
        "zasilat_neaktivnim": True,
        "predmet": "AMČR: přijetí oznámení {ident_cely} | AMCR: receipt of notification {ident_cely}",
        "cesta_sablony": "emails/E-O-01.html",
    },
    "E-O-02": {
        "zasilat_neaktivnim": True,
        "predmet": "AMČR: přijetí oznámení {ident_cely} | AMCR: receipt of notification {ident_cely}",
        "cesta_sablony": "emails/E-O-02.html",
    },
    "E-P-01a": {
        "zasilat_neaktivnim": True,
        "predmet": "AMČR: oznámení {ident_cely} schváleno | AMCR: notification {ident_cely} accepted",
        "cesta_sablony": "emails/E-P-01a.html",
    },
    "E-P-01b": {
        "zasilat_neaktivnim": True,
        "predmet": "AMČR: oznámení {ident_cely} schváleno | AMCR: notification {ident_cely} accepted",
        "cesta_sablony": "emails/E-P-01b.html",
    },
    "E-P-02": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR: zapsán nový projekt {ident_cely} | AMCR: new project {ident_cely} available",
        "cesta_sablony": "emails/E-P-02.html",
    },
    "E-P-03a": {
        "zasilat_neaktivnim": True,
        "predmet": "AMČR: registrace terénního zásahu {ident_cely} | AMCR: registration of field intervention {ident_cely}",
        "cesta_sablony": "emails/E-P-03a.html",
    },
    "E-P-03b": {
        "zasilat_neaktivnim": True,
        "predmet": "AMČR: registrace terénního zásahu {ident_cely} | AMCR: registration of field intervention {ident_cely}",
        "cesta_sablony": "emails/E-P-03b.html",
    },
    "E-P-07": {
        "zasilat_neaktivnim": True,
        "predmet": "AMČR: projekt {ident_cely} - žádost o odhlášení | AMCR: project {ident_cely} - request for deregistration",
        "cesta_sablony": "emails/E-P-07.html",
    },
    "E-P-04": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR: projekt {ident_cely} - zrušen | AMCR: project {ident_cely} - cancelled",
        "cesta_sablony": "emails/E-P-04.html",
    },
    "E-P-05": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR: projekt {ident_cely} - opětovně zapsán | AMCR: project {ident_cely} - re-recorded",
        "cesta_sablony": "emails/E-P-05.html",
    },
    "E-P-06a": {
        "zasilat_neaktivnim": True,
        "predmet": "AMČR: zrušení projektu {ident_cely} | AMCR: cancellation of project {ident_cely}",
        "cesta_sablony": "emails/E-P-06a.html",
    },
    "E-P-06b": {
        "zasilat_neaktivnim": True,
        "predmet": "AMČR: zrušení projektu {ident_cely} | AMCR: cancellation of project {ident_cely}",
        "cesta_sablony": "emails/E-P-06b.html",
    },
    "E-N-01": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR-PAS: nové samostatné nálezy ke schválení | AMCR-PAS: new individual finds for approval",
        "cesta_sablony": "emails/E-N-01.html",
    },
    "E-N-02": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR-PAS: nálezy archivovány | AMCR-PAS: finds archived",
        "cesta_sablony": "emails/E-N-02.html",
    },
    "E-N-03": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR-PAS: samostatný nález {ident_cely} vrácen k doplnění | AMCR-PAS: individual find {ident_cely} returned for completion",
        "cesta_sablony": "emails/E-N-03.html",
    },
    "E-N-04": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR-PAS: samostatný nález {ident_cely} vrácen k doplnění | AMCR-PAS: individual find {ident_cely} returned for completion",
        "cesta_sablony": "emails/E-N-03.html",
    },
    "E-N-05": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR-PAS: nový spolupracovník | AMCR-PAS: new collaborator",
        "cesta_sablony": "emails/E-N-05.html",
    },
    "E-N-06": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR-PAS: spolupráce potvrzena | AMCR-PAS: collaboration confirmed",
        "cesta_sablony": "emails/E-N-06.html",
    },
    "E-K-01": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR - Knihovna 3D: dokument {ident_cely} archivován | AMCR - 3D Library: document {ident_cely} archived",
        "cesta_sablony": "emails/E-K-01.html",
    },
    "E-K-02": {
        "zasilat_neaktivnim": False,
        "predmet": "AMČR - Knihovna 3D: dokument {ident_cely} vrácen k doplnění | AMCR - 3D Library: document {ident_cely} returned for completion",
        "cesta_sablony": "emails/E-K-02.html",
    },
    "E-P-08": {
        "zasilat_neaktivnim": True,
        "predmet": "AMČR: projekt {ident_cely} - žádost o údaje oznamovatele | AMCR: project {ident_cely} - request for announcer data",
        "cesta_sablony": "emails/E-P-08.html",
    },
}
