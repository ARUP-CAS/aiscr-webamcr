alter table public.soubor
ADD column if not exists projekt integer REFERENCES public.projekt (id) ON DELETE
SET NULL;
CREATE OR REPLACE FUNCTION public.delete_connected_documents_to_casts() RETURNS trigger LANGUAGE plpgsql AS $function$ BEGIN
DELETE FROM dokument AS d
WHERE old.dokument = d.id
	AND d.stav = 1;
RETURN NEW;
END;
$function$;
CREATE OR REPLACE FUNCTION public.prevent_project_deletion() RETURNS trigger LANGUAGE plpgsql AS $function$ BEGIN IF EXISTS (
		SELECT
		FROM soubor_vazby AS sv
			inner join soubor AS s on s.vazba = sv.id
		WHERE s.projekt = OLD.id
	) THEN RAISE EXCEPTION 'Nelze smazat projekt s projektovou dokumentací!';
END IF;
RETURN OLD;
END;
$function$;