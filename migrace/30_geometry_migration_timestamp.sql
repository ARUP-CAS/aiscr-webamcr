ALTER TABLE public.pian ADD geom_updated_at  TIMESTAMP WITH TIME ZONE DEFAULT NULL;
ALTER TABLE public.pian ADD geom_sjtsk_updated_at  TIMESTAMP WITH TIME ZONE DEFAULT NULL;

CREATE TABLE public.amcr_geom_migrations_jobs(
    id serial primary key,
    typ text not null,
    count_selected_wgs84 integer default 0 not null,
    count_selected_sjtsk integer default 0 not null,
    count_updated_wgs84 integer default 0 not null,
    count_updated_sjtsk integer default 0 not null,
    count_error_wgs84 integer default 0 not null,
    count_error_sjtsk integer default 0 not null,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    detail text default null
)

CREATE TABLE public.amcr_geom_migrations_jobs_wgs84_errors(
    id serial primary key,
    pian_id serial
)

CREATE TABLE public.amcr_geom_migrations_jobs_sjtsk_errors(
    id serial primary key,
    pian_id serial
)
