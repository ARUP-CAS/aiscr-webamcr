create table public.odstavky_systemu (
    id serial4 not NULL,
    info_od date not NULL,
    datum_odstavky date not NULL,
    cas_odstavky time not NULL,
    status boolean not NULL
);
