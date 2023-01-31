-- public.django_celery_beat_clockedschedule definition
-- Drop table
-- DROP TABLE django_celery_beat_clockedschedule;
CREATE TABLE django_celery_beat_clockedschedule (
    id serial4 NOT NULL,
    clocked_time timestamptz NOT NULL,
    CONSTRAINT django_celery_beat_clockedschedule_pkey PRIMARY KEY (id)
);
-- public.django_celery_beat_crontabschedule definition
-- Drop table
-- DROP TABLE django_celery_beat_crontabschedule;
CREATE TABLE django_celery_beat_crontabschedule (
    id serial4 NOT NULL,
    "minute" varchar(240) NOT NULL,
    "hour" varchar(96) NOT NULL,
    day_of_week varchar(64) NOT NULL,
    day_of_month varchar(124) NOT NULL,
    month_of_year varchar(64) NOT NULL,
    timezone varchar(63) NOT NULL,
    CONSTRAINT django_celery_beat_crontabschedule_pkey PRIMARY KEY (id)
);
-- public.django_celery_beat_intervalschedule definition
-- Drop table
-- DROP TABLE django_celery_beat_intervalschedule;
CREATE TABLE django_celery_beat_intervalschedule (
    id serial4 NOT NULL,
    "every" int4 NOT NULL,
    "period" varchar(24) NOT NULL,
    CONSTRAINT django_celery_beat_intervalschedule_pkey PRIMARY KEY (id)
);
-- public.django_celery_beat_periodictasks definition
-- Drop table
-- DROP TABLE django_celery_beat_periodictasks;
CREATE TABLE django_celery_beat_periodictasks (
    ident int2 NOT NULL,
    last_update timestamptz NOT NULL,
    CONSTRAINT django_celery_beat_periodictasks_pkey PRIMARY KEY (ident)
);
-- public.django_celery_beat_solarschedule definition
-- Drop table
-- DROP TABLE django_celery_beat_solarschedule;
CREATE TABLE django_celery_beat_solarschedule (
    id serial4 NOT NULL,
    "event" varchar(24) NOT NULL,
    latitude numeric(9, 6) NOT NULL,
    longitude numeric(9, 6) NOT NULL,
    CONSTRAINT django_celery_beat_solar_event_latitude_longitude_ba64999a_uniq UNIQUE (event, latitude, longitude),
    CONSTRAINT django_celery_beat_solarschedule_pkey PRIMARY KEY (id)
);
-- public.django_celery_beat_periodictask definition
-- Drop table
-- DROP TABLE django_celery_beat_periodictask;
CREATE TABLE django_celery_beat_periodictask (
    id serial4 NOT NULL,
    "name" varchar(200) NOT NULL,
    task varchar(200) NOT NULL,
    args text NOT NULL,
    kwargs text NOT NULL,
    queue varchar(200) NULL,
    exchange varchar(200) NULL,
    routing_key varchar(200) NULL,
    expires timestamptz NULL,
    enabled bool NOT NULL,
    last_run_at timestamptz NULL,
    total_run_count int4 NOT NULL,
    date_changed timestamptz NOT NULL,
    description text NOT NULL,
    crontab_id int4 NULL,
    interval_id int4 NULL,
    solar_id int4 NULL,
    one_off bool NOT NULL,
    start_time timestamptz NULL,
    priority int4 NULL,
    headers text NOT NULL,
    clocked_id int4 NULL,
    expire_seconds int4 NULL,
    CONSTRAINT django_celery_beat_periodictask_expire_seconds_check CHECK ((expire_seconds >= 0)),
    CONSTRAINT django_celery_beat_periodictask_name_key UNIQUE (name),
    CONSTRAINT django_celery_beat_periodictask_pkey PRIMARY KEY (id),
    CONSTRAINT django_celery_beat_periodictask_priority_check CHECK ((priority >= 0)),
    CONSTRAINT django_celery_beat_periodictask_total_run_count_check CHECK ((total_run_count >= 0)),
    CONSTRAINT django_celery_beat_p_clocked_id_47a69f82_fk_django_ce FOREIGN KEY (clocked_id) REFERENCES django_celery_beat_clockedschedule(id) DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT django_celery_beat_p_crontab_id_d3cba168_fk_django_ce FOREIGN KEY (crontab_id) REFERENCES django_celery_beat_crontabschedule(id) DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT django_celery_beat_p_interval_id_a8ca27da_fk_django_ce FOREIGN KEY (interval_id) REFERENCES django_celery_beat_intervalschedule(id) DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT django_celery_beat_p_solar_id_a87ce72c_fk_django_ce FOREIGN KEY (solar_id) REFERENCES django_celery_beat_solarschedule(id) DEFERRABLE INITIALLY DEFERRED
);
CREATE INDEX django_celery_beat_periodictask_clocked_id_47a69f82 ON public.django_celery_beat_periodictask USING btree (clocked_id);
CREATE INDEX django_celery_beat_periodictask_crontab_id_d3cba168 ON public.django_celery_beat_periodictask USING btree (crontab_id);
CREATE INDEX django_celery_beat_periodictask_interval_id_a8ca27da ON public.django_celery_beat_periodictask USING btree (interval_id);
CREATE INDEX django_celery_beat_periodictask_name_265a36b7_like ON public.django_celery_beat_periodictask USING btree (name varchar_pattern_ops);
CREATE INDEX django_celery_beat_periodictask_solar_id_a87ce72c ON public.django_celery_beat_periodictask USING btree (solar_id);