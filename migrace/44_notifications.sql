CREATE TABLE IF NOT EXISTS uzivatel_notifikace_typ
(
    id                 SERIAL PRIMARY KEY,
    ident_cely         TEXT UNIQUE           NOT NULL,
    zasilat_neaktivnim BOOLEAN DEFAULT FALSE NOT NULL,
    predmet            TEXT                  NOT NULL,
    cesta_sablony      TEXT
);

INSERT INTO uzivatel_notifikace_typ(ident_cely, zasilat_neaktivnim, predmet, cesta_sablony)
VALUES ('E-U-01', True, 'AMČR: potvrďte svůj email pro registraci', null),
       ('E-U-02', True, 'AMČR: uživatelský účet zaregistrován', 'emails/account_confirmed.html'),
       ('E-U-03', True, 'AMČR: uživatelský účet deaktivován nebo zrušen', 'emails/account_removed.html'),
       ('E-U-04', False, 'AMČR: uživatelský účet čeká na aktivaci', 'emails/account_activation_request.html'),
       ('E-U-06', True, 'AMČR: nová uživatelská role či oprávnění', 'emails/account_was_updated.html'),
    ('E-NZ-01', False, 'AMČR: projekt {ident_cely} - blíží se lhůta pro odevzdání NZ', '../templates/projects/emails/project_resign_in_90.html'),
    ('E-NZ-02', False, 'AMČR: projekt {ident_cely} - vypršela lhůta pro odevzdání NZ', '../templates/projects/emails/project_resign_date_past_due.html'),
    ('E-V-01', False, 'AMČR: akce {ident_cely} - vrácena k doplnění', 'emails/akce_was_returned.html'),
    ('E-A-01', False, 'AMČR: projekt {ident_cely} - archivován', 'emails/project_was_archived.html'),
    ('E-A-02', False, 'AMČR: akce {ident_cely} - archivována', 'emails/akce_was_archived.html'),
    ('E-O-01', False, 'AMČR: potvrzení o přijetí oznámení {ident_cely}', 'emails/new_c_project.html'),
    ('E-O-02', False, 'AMČR: potvrzení o přijetí oznámení {ident_cely}', 'emails/new_m_project.html'),
 ('E-P-01a', False, 'AMČR: potvrzení o schválení oznámení {ident_cely}', 'emails/new_c_project.html'),
    ('E-P-01b', False, 'AMČR: potvrzení o schválení oznámení {ident_cely}', 'emails/new_m_project.html'),
    ('E-P-02', False, 'AMČR: zapsán nový projekt {ident_cely}', '../templates/projects/emails/observer_project_was_registered.html'),
('E-P-03a', False, 'AMČR: registrace terénního zásahu {ident_cely}', 'emails/register_c_project.html'),
    ('E-P-03b', False, 'IS AMČR: registrace terénního zásahu {ident_cely}', 'emails/register_m_project.html'),
('E-P-07', False, 'AMČR: projekt {ident_cely} - žádost o odhlášení', 'emails/project_is_cancelled.html'),
('E-P-04', False, 'AMČR: projekt {ident_cely} - zrušen', 'emails/project_is_removed.html'),
('E-P-05', False, 'AMČR: projekt {ident_cely} - opětovně zapsán', 'emails/project_registered_again.html'),
('E-P-06a', False, 'AMČR: zrušení projektu {ident_cely}', 'emails/project_c_is_cancelled_to_user.html'),
('E-P-06b', False, 'AMČR: zrušení projektu {ident_cely}', 'emails/project_m_is_cancelled_to_user.html'),
('E-N-01', False, 'AMČR-PAS: nové samostatné nálezy ke schválení', '../templates/pas/emails/projects_were_sent.html'),
('E-N-02', False, 'AMČR-PAS: nálezy byly archivovány', '../templates/pas/emails/projects_were_archived.html'),
('E-N-03', False, 'AMČR-PAS: samostatný nález {ident_cely} vrácen k doplnění', 'emails/project_was_returned.html'),
('E-N-04', False, 'AMČR-PAS: samostatný nález {ident_cely} vrácen k doplnění', 'emails/project_was_returned.html'),
('E-N-05', False, 'AMČR-PAS: nový spolupracovník', 'emails/new_cooperator.html'),
('E-N-06', False, 'AMČR-PAS: spolupráce potvrzena', 'emails/cooperation_confirmed.html'),
('E-K-01', False, 'AMČR - Knihovna 3D: dokument {ident_cely} byl archivován', 'emails/document_archived.html'),
('E-K-02', False, 'AMČR - Knihovna 3D: dokument {ident_cely} byl vrácen k doplnění', 'emails/document_was_returned.html'),
('AMČR: archivace záznamů', False, '', ''),
('AMČR-PAS: nové nálezy k potvrzení', False, '', ''),
('AMČR-PAS: archivace záznamů', False, '', ''),
('AMČR-PAS: nová žádost o spolupráci', False, '', ''),
('AMČR - Knihovna 3D: archivace záznamů', False, '', '');

CREATE TABLE IF NOT EXISTS auth_user_notification_types
(
    id                      SERIAL PRIMARY KEY,
    usernotificationtype_id INT,
    user_id                 INT,
    CONSTRAINT uzivatel_notifikace__usernotificationtype_fk_uzivatel_
        FOREIGN KEY (usernotificationtype_id)
            REFERENCES uzivatel_notifikace_typ (id)
            ON DELETE SET NULL,
    CONSTRAINT uzivatel_notifikace_typ_user_user_id_fk_auth_user_id
        FOREIGN KEY (user_id)
            REFERENCES auth_user (id)
            ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS "notifications_log"
(
    "id" bigserial NOT NULL PRIMARY KEY,
    "object_id" integer NOT NULL CHECK ("object_id" >= 0), "created_at" date NOT NULL,
    "notification_type_id" integer NOT NULL,
    "content_type_id" integer NOT NULL
    );

CREATE INDEX "notifications_log_order_content_43c3a2_idx" ON "notifications_log" ("content_type_id", "object_id");

ALTER TABLE "notifications_log" ADD CONSTRAINT "notifications_log_notification_type_id_2eefa8d4_fk_dump_notification_type_id" FOREIGN KEY ("notification_type_id") REFERENCES "uzivatel_notifikace_typ" ("id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE "notifications_log" ADD CONSTRAINT "notifications_log_content_type_id_0d88bca2_fk_django_content_type_id" FOREIGN KEY ("content_type_id") REFERENCES "django_content_type" ("id") DEFERRABLE INITIALLY DEFERRED;

CREATE INDEX "notifications_log_notification_type_id_2eefa8d4" ON "notifications_log" ("notification_type_id");

CREATE INDEX "notifications_log_content_type_id_0d88bca2" ON "notifications_log" ("content_type_id");

INSERT INTO "django_content_type" (app_label, model) VALUES ('uzivatel', 'usernotificationtype');