ALTER TABLE auth_user_notification_types
    RENAME TO auth_user_notifikace_typ;

ALTER TABLE uzivatel_notifikace_typ
    RENAME TO notifikace_typ;

UPDATE notifikace_typ
SET ident_cely = 'S-E-A-XX'
WHERE ident_cely = 'AMČR: archivace záznamů';

UPDATE notifikace_typ
SET ident_cely = 'S-E-N-01'
WHERE ident_cely = 'AMČR-PAS: nové nálezy k potvrzení';

UPDATE notifikace_typ
SET ident_cely = 'S-E-N-02'
WHERE ident_cely = 'AMČR-PAS: archivace záznamů';

UPDATE notifikace_typ
SET ident_cely = 'S-E-N-05'
WHERE ident_cely = 'AMČR-PAS: nová žádost o spolupráci';

UPDATE notifikace_typ
SET ident_cely = 'S-E-K-01'
WHERE ident_cely = 'AMČR - Knihovna 3D: archivace záznamů';

ALTER TABLE auth_user_notifikace_typ
    ALTER COLUMN usernotificationtype_id SET NOT NULL;

ALTER TABLE auth_user_notifikace_typ
    ALTER COLUMN user_id SET NOT NULL;

ALTER TABLE auth_user_notifikace_typ
    ADD UNIQUE (usernotificationtype_id, user_id);

ALTER TABLE auth_user_notifikace_typ
    DROP CONSTRAINT uzivatel_notifikace__usernotificationtype_fk_uzivatel_;

ALTER TABLE auth_user_notifikace_typ
    ADD CONSTRAINT auth_user_notifikace_typ_usernotificationtype_id_fkey
        FOREIGN KEY (usernotificationtype_id)
            REFERENCES notifikace_typ (id)
            ON UPDATE CASCADE
            ON DELETE CASCADE;

ALTER TABLE auth_user_notifikace_typ
    DROP CONSTRAINT uzivatel_notifikace_typ_user_user_id_fk_auth_user_id;

ALTER TABLE auth_user_notifikace_typ
    ADD CONSTRAINT auth_user_notifikace_typ_user_id_fkey
        FOREIGN KEY (user_id)
            REFERENCES auth_user (id)
            ON UPDATE CASCADE
            ON DELETE CASCADE;
