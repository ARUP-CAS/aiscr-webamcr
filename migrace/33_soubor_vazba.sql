alter table public.soubor
ADD COLUMN historie integer REFERENCES public.historie_vazby (id) ON DELETE SET NULL;
