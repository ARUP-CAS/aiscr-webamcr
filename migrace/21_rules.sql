DROP TRIGGER IF EXISTS prevent_project_deletion on projekt;
DROP TRIGGER IF EXISTS delete_unconfirmed_pian on dokumentacni_jednotka;
DROP TRIGGER IF EXISTS delete_connected_documents on archeologicky_zaznam;
DROP TRIGGER IF EXISTS delete_connected_documents_1 on archeologicky_zaznam;
DROP TRIGGER IF EXISTS delete_connected_documents_2 on archeologicky_zaznam;

CREATE OR REPLACE FUNCTION prevent_project_deletion() RETURNS trigger AS $prevent_project_deletion$
        BEGIN
            IF EXISTS (SELECT FROM soubor_vazby AS sv inner join soubor AS s on s.vazba = sv.id WHERE s.projekt = OLD.id) THEN
                RAISE EXCEPTION 'Nelze smazat projekt s projektovou dokumentací!';
            END IF;
            RETURN NEW;

        END;
    $prevent_project_deletion$ LANGUAGE plpgsql;

    CREATE TRIGGER prevent_project_deletion BEFORE DELETE ON projekt
        FOR EACH ROW EXECUTE PROCEDURE prevent_project_deletion();

CREATE OR REPLACE FUNCTION delete_unconfirmed_pian() RETURNS trigger AS $delete_unconfirmed_pian$
        BEGIN
            DELETE FROM pian WHERE pian.id = old.pian and pian.stav = 1;
			RETURN NEW;
        END;
    $delete_unconfirmed_pian$ LANGUAGE plpgsql;

    CREATE TRIGGER delete_unconfirmed_pian AFTER DELETE ON dokumentacni_jednotka
        FOR EACH ROW EXECUTE PROCEDURE delete_unconfirmed_pian();

CREATE OR REPLACE FUNCTION delete_connected_documents_1() RETURNS trigger AS $delete_connected_documents_1$
        BEGIN
            -- Pokud je navázaný dokument nepotvrzený a nemá žádnou další vazbu na archeologicky_zaznam, smazat také dokument
            DELETE FROM dokument AS d USING dokument_cast AS dc WHERE dc.dokument = d.id AND dc.archeologicky_zaznam = old.id
			AND NOT EXISTS (SELECT FROM dokument AS di INNER JOIN dokument_cast AS dci ON dci.dokument = di.id WHERE dci.archeologicky_zaznam != old.id AND d.id = di.id)
			AND d.stav = 1;
			RETURN NEW;
        END;
    $delete_connected_documents_1$ LANGUAGE plpgsql;

    CREATE TRIGGER delete_connected_documents_1 AFTER DELETE ON archeologicky_zaznam
        FOR EACH ROW EXECUTE PROCEDURE delete_connected_documents_1();

CREATE OR REPLACE FUNCTION delete_connected_documents_2() RETURNS trigger AS $delete_connected_documents_2$
        BEGIN
            -- Pokud je navázaný dokument_cast bez vazeb na neident_akce a komponenta_vazby, smazat také dokument_cast
			DELETE FROM dokument_cast AS dc
			WHERE dc.archeologicky_zaznam = old.id AND NOT EXISTS (SELECT FROM neident_akce AS na WHERE dc.id = na.dokument_cast)
			AND NOT EXISTS (SELECT FROM komponenta_vazby AS kv WHERE kv.id = dc.komponenty)
			AND dc.komponenty IS NULL;
			RETURN NEW;
        END;
    $delete_connected_documents_2$ LANGUAGE plpgsql;

    CREATE TRIGGER delete_connected_documents_2 AFTER DELETE ON archeologicky_zaznam
        FOR EACH ROW EXECUTE PROCEDURE delete_connected_documents_2();

ALTER TABLE public.archeologicky_zaznam
	DROP CONSTRAINT archeologicky_zaznam_historie_fkey,
    ADD CONSTRAINT archeologicky_zaznam_historie_fkey FOREIGN KEY (historie)
    REFERENCES public.historie_vazby (id) MATCH SIMPLE
    ON UPDATE CASCADE
    ON DELETE CASCADE;

