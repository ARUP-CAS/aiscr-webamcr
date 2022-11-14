ALTER TABLE public.heslar_datace DROP COLUMN region;
ALTER TABLE public.heslar_datace ADD COLUMN poznamka text COLLATE pg_catalog."default";
