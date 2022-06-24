alter table public.soubor
ADD column if not exists projekt integer REFERENCES public.projekt (id) ON DELETE SET NULL;

CREATE OR REPLACE FUNCTION public.delete_connected_documents_to_casts()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
		BEGIN
            DELETE FROM dokument AS d WHERE old.dokument = d.id
			AND d.stav = 1;
			RETURN NEW;
		END;
	$function$
;