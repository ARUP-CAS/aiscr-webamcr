-- public.django_celery_results_chordcounter definition
-- Drop table
-- DROP TABLE django_celery_results_chordcounter;
CREATE TABLE django_celery_results_chordcounter (
    id serial4 NOT NULL,
    group_id varchar(255) NOT NULL,
    sub_tasks text NOT NULL,
    count int4 NOT NULL,
    CONSTRAINT django_celery_results_chordcounter_count_check CHECK ((count >= 0)),
    CONSTRAINT django_celery_results_chordcounter_group_id_key UNIQUE (group_id),
    CONSTRAINT django_celery_results_chordcounter_pkey PRIMARY KEY (id)
);
CREATE INDEX django_celery_results_chordcounter_group_id_1f70858c_like ON public.django_celery_results_chordcounter USING btree (group_id varchar_pattern_ops);
-- public.django_celery_results_groupresult definition
-- Drop table
-- DROP TABLE django_celery_results_groupresult;
CREATE TABLE django_celery_results_groupresult (
    id serial4 NOT NULL,
    group_id varchar(255) NOT NULL,
    date_created timestamptz NOT NULL,
    date_done timestamptz NOT NULL,
    content_type varchar(128) NOT NULL,
    content_encoding varchar(64) NOT NULL,
    "result" text NULL,
    CONSTRAINT django_celery_results_groupresult_group_id_key UNIQUE (group_id),
    CONSTRAINT django_celery_results_groupresult_pkey PRIMARY KEY (id)
);
CREATE INDEX django_cele_date_cr_bd6c1d_idx ON public.django_celery_results_groupresult USING btree (date_created);
CREATE INDEX django_cele_date_do_caae0e_idx ON public.django_celery_results_groupresult USING btree (date_done);
CREATE INDEX django_celery_results_groupresult_group_id_a085f1a9_like ON public.django_celery_results_groupresult USING btree (group_id varchar_pattern_ops);
-- public.django_celery_results_taskresult definition
-- Drop table
-- DROP TABLE django_celery_results_taskresult;
CREATE TABLE django_celery_results_taskresult (
    id serial4 NOT NULL,
    task_id varchar(255) NOT NULL,
    status varchar(50) NOT NULL,
    content_type varchar(128) NOT NULL,
    content_encoding varchar(64) NOT NULL,
    "result" text NULL,
    date_done timestamptz NOT NULL,
    traceback text NULL,
    meta text NULL,
    task_args text NULL,
    task_kwargs text NULL,
    task_name varchar(255) NULL,
    worker varchar(100) NULL,
    date_created timestamptz NOT NULL,
    periodic_task_name varchar(255) NULL,
    CONSTRAINT django_celery_results_taskresult_pkey PRIMARY KEY (id),
    CONSTRAINT django_celery_results_taskresult_task_id_key UNIQUE (task_id)
);
CREATE INDEX django_cele_date_cr_f04a50_idx ON public.django_celery_results_taskresult USING btree (date_created);
CREATE INDEX django_cele_date_do_f59aad_idx ON public.django_celery_results_taskresult USING btree (date_done);
CREATE INDEX django_cele_status_9b6201_idx ON public.django_celery_results_taskresult USING btree (status);
CREATE INDEX django_cele_task_na_08aec9_idx ON public.django_celery_results_taskresult USING btree (task_name);
CREATE INDEX django_cele_worker_d54dd8_idx ON public.django_celery_results_taskresult USING btree (worker);
CREATE INDEX django_celery_results_taskresult_task_id_de0d95bf_like ON public.django_celery_results_taskresult USING btree (task_id varchar_pattern_ops);