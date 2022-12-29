DROP TRIGGER IF EXISTS prevent_project_deletion on projekt;
DROP TRIGGER IF EXISTS delete_unconfirmed_pian on dokumentacni_jednotka;
DROP TRIGGER IF EXISTS delete_connected_documents on archeologicky_zaznam;
DROP TRIGGER IF EXISTS delete_connected_documents_1 on archeologicky_zaznam;
DROP TRIGGER IF EXISTS delete_connected_documents_2 on archeologicky_zaznam;

-- Vychází z https://github.com/ARUP-CAS/aiscr-webamcr/issues/48#issuecomment-873176957
--  1 - Projekt nejde smazat, dokud neodstraním projektovou dokumentaci (je to speciální jen kvůli tomu, že je tam ta obrácená vazba, jinak by to byl klasický RESTRICT).
CREATE OR REPLACE FUNCTION prevent_project_deletion() RETURNS trigger LANGUAGE plpgsql AS $prevent_project_deletion$
        BEGIN
            IF EXISTS (SELECT FROM soubor_vazby AS sv inner join soubor AS s ON s.vazba = sv.id WHERE s.projekt = OLD.id) THEN
                RAISE EXCEPTION 'Nelze smazat projekt s projektovou dokumentací!';
            END IF;
            RETURN OLD;
        END;
    $prevent_project_deletion$;

    CREATE TRIGGER prevent_project_deletion BEFORE DELETE ON projekt
        FOR EACH ROW EXECUTE PROCEDURE prevent_project_deletion();

-- 2 - Pokud mažu dokumentacni_jednotka a ta má vazbu na nepotvrzený PIAN, smazat i tento PIAN (pokud nemá jinou vazbu na DJ).
CREATE OR REPLACE FUNCTION delete_unconfirmed_pian() RETURNS trigger LANGUAGE plpgsql AS $delete_unconfirmed_pian$
    BEGIN
        DELETE FROM pian
        WHERE pian.id = old.pian AND pian.ident_cely NOT LIKE 'N-%'
        AND NOT EXISTS (
            SELECT FROM dokumentacni_jednotka
            WHERE pian.id = dokumentacni_jednotka.pian
        );
        RETURN NEW;
    END;
    $delete_unconfirmed_pian$; 

    CREATE TRIGGER delete_unconfirmed_pian AFTER DELETE ON dokumentacni_jednotka
        FOR EACH ROW EXECUTE PROCEDURE delete_unconfirmed_pian();

-- 3 - Pokud mažu archeologicky_zaznam, tak:
-- 3a - pokud je navázaný dokument nepotvrzený a nemá žádnou další vazbu na archeologicky_zaznam, smazat také dokument (cascade se zde aplikuji standardně v databázi)
CREATE OR REPLACE FUNCTION delete_connected_documents() RETURNS trigger LANGUAGE plpgsql AS $delete_connected_documents$
        BEGIN
            DELETE FROM dokument AS d
			WHERE d.ident_cely NOT LIKE 'X-%'
			AND EXISTS (
				SELECT FROM dokument_cast AS dc
				WHERE dc.dokument = d.id AND dc.archeologicky_zaznam = old.id AND NOT EXISTS (
					SELECT FROM dokument_cast AS dci
					WHERE dci.dokument = d.id AND dci.archeologicky_zaznam != old.id
				)
			);
			RETURN NEW;
        END;
    $delete_connected_documents$;

    CREATE TRIGGER delete_connected_documents AFTER DELETE ON archeologicky_zaznam
        FOR EACH ROW EXECUTE PROCEDURE delete_connected_documents();

-- 3b - pokud je navázaný dokument_cast bez vazeb na neident_akce a komponenta_vazby, smazat také dokument_cast (cascade se zde aplikuji standardně v databázi)
CREATE OR REPLACE FUNCTION delete_connected_document_cast() RETURNS trigger LANGUAGE plpgsql AS $delete_connected_document_cast$
        BEGIN
			DELETE FROM dokument_cast AS dc
			WHERE dc.archeologicky_zaznam = old.id AND NOT EXISTS (SELECT FROM neident_akce AS na WHERE dc.id = na.dokument_cast)
			AND NOT EXISTS (SELECT FROM komponenta AS k WHERE k.komponenta_vazby = dc.komponenty);
			RETURN NEW;
        END;
    $delete_connected_document_cast$;

    CREATE TRIGGER delete_connected_document_cast AFTER DELETE ON archeologicky_zaznam
        FOR EACH ROW EXECUTE PROCEDURE delete_connected_document_cast();

ALTER TABLE public.archeologicky_zaznam
	DROP CONSTRAINT archeologicky_zaznam_historie_fkey,
    ADD CONSTRAINT archeologicky_zaznam_historie_fkey FOREIGN KEY (historie)
    REFERENCES public.historie_vazby (id) MATCH SIMPLE
    ON UPDATE CASCADE
    ON DELETE CASCADE;

-- Zaznamenání smazání záznamu do historie
-- archeologicky_zaznam, auth_user, dokument, externi_zdroj, pian, projekt, samostatny_nalez
CREATE OR REPLACE FUNCTION deleted_records_history() RETURNS trigger LANGUAGE plpgsql AS $deleted_records_history$
    BEGIN
        INSERT INTO historie (datum_zmeny, uzivatel, poznamka, vazba, typ_zmeny) SELECT NOW(), (SELECT id FROM auth_user WHERE email = 'amcr@arup.cas.cz'), ident_cely, historie, 'DEL' FROM old;
        RETURN NEW;
    END;
    $deleted_records_history$; 

    CREATE TRIGGER deleted_records_history AFTER DELETE ON archeologicky_zaznam, auth_user, dokument, externi_zdroj, pian, projekt, samostatny_nalez
        FOR EACH ROW EXECUTE PROCEDURE deleted_records_history();
	
-- soubor
CREATE OR REPLACE FUNCTION deleted_soubor_history() RETURNS trigger LANGUAGE plpgsql AS $deleted_soubor_history$
    BEGIN
        INSERT INTO historie (datum_zmeny, uzivatel, poznamka, vazba, typ_zmeny) SELECT NOW(), (SELECT id FROM auth_user WHERE email = 'amcr@arup.cas.cz'), nazev, historie, 'DEL' FROM old;
        RETURN NEW;
    END;
    $deleted_soubor_history$; 

    CREATE TRIGGER deleted_soubor_history AFTER DELETE ON soubor
        FOR EACH ROW EXECUTE PROCEDURE deleted_soubor_history();

-- Triggery pro odstranění sirotků tam, kde mohou zůstávat kvůli otočené vazbě přes pomocnou tabulku (historie_vazby, komponenta_vazby, soubor_vazby)
-- uzivatel_spoluprace
CREATE OR REPLACE FUNCTION delete_history_spoluprace() RETURNS trigger LANGUAGE plpgsql AS $delete_history_spoluprace$
    BEGIN
        DELETE FROM historie_vazby WHERE historie_vazby.id = old.historie;
        RETURN NEW;
    END;
    $delete_history_spoluprace$; 

    CREATE TRIGGER delete_history_spoluprace AFTER DELETE ON uzivatel_spoluprace
        FOR EACH ROW EXECUTE PROCEDURE delete_history_spoluprace();

-- komponenta_vazby
CREATE OR REPLACE FUNCTION delete_related_komponenta() RETURNS trigger LANGUAGE plpgsql AS $delete_related_komponenta$
    BEGIN
        DELETE FROM komponenta_vazby WHERE komponenta_vazby.id = old.komponenty;
        RETURN NEW;
    END;
    $delete_related_komponenta$; 

    CREATE TRIGGER delete_related_komponenta AFTER DELETE ON dokument_cast, dokumentacni_jednotka
        FOR EACH ROW EXECUTE PROCEDURE delete_related_komponenta();
	
-- soubor_vazby
CREATE OR REPLACE FUNCTION delete_related_soubor() RETURNS trigger LANGUAGE plpgsql AS $delete_related_soubor$
    BEGIN
        DELETE FROM soubor_vazby WHERE soubor_vazby.id = old.soubory;
        RETURN NEW;
    END;
    $delete_related_soubor$; 

    CREATE TRIGGER delete_related_soubor AFTER DELETE ON dokument, projekt, samostatny_nalez
        FOR EACH ROW EXECUTE PROCEDURE delete_related_soubor();
	
