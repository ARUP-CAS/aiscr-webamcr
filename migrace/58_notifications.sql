CREATE TABLE IF NOT EXISTS uzivatel_notifikace_typ
(
    id                 SERIAL PRIMARY KEY,
    ident_cely         TEXT UNIQUE           NOT NULL
);

INSERT INTO uzivatel_notifikace_typ(ident_cely)
VALUES ('E-U-01'),
       ('E-U-02'),
       ('E-U-03'),
       ('E-U-04'),
       ('E-U-05'),
       ('E-U-06'),
       ('E-NZ-01'),
       ('E-NZ-02'),
       ('E-V-01'),
       ('E-A-01'),
       ('E-A-02'),
       ('E-O-01'),
       ('E-O-02'),
       ('E-P-01a'),
       ('E-P-01b'),
       ('E-P-02'),
       ('E-P-03a'),
       ('E-P-03b'),
       ('E-P-07'),
       ('E-P-04'),
       ('E-P-05'),
       ('E-P-06a'),
       ('E-P-06b'),
       ('E-N-01'),
       ('E-N-02'),
       ('E-N-03'),
       ('E-N-04'),
       ('E-N-05'),
       ('E-N-06'),
       ('E-K-01'),
       ('E-K-02'),
       ('AMČR: archivace záznamů'),
       ('AMČR-PAS: nové nálezy k potvrzení'),
       ('AMČR-PAS: archivace záznamů'),
       ('AMČR-PAS: nová žádost o spolupráci'),
       ('AMČR - Knihovna 3D: archivace záznamů');


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
