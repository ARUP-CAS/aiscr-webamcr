create table public.odstavky_systemu (
    id serial4 not NULL,
    info_od date not NULL,
    datum_odstavky date not NULL,
    cas_odstavky time not NULL,
    text_en text not NULL,
    text_cs text not NULL
)