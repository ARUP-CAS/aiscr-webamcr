CREATE SEQUENCE public.uzivatel_historicaluser_history_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

CREATE TABLE public.uzivatel_historicaluser
(
    id integer NOT NULL,
    password character varying(128) COLLATE pg_catalog."default" NOT NULL,
    last_login timestamp with time zone,
    is_superuser boolean NOT NULL,
    ident_cely character varying(150) COLLATE pg_catalog."default" NOT NULL,
    first_name character varying(150) COLLATE pg_catalog."default" NOT NULL,
    last_name character varying(150) COLLATE pg_catalog."default" NOT NULL,
    email character varying(254) COLLATE pg_catalog."default" NOT NULL,
    is_staff boolean NOT NULL,
    is_active boolean NOT NULL,
    date_joined timestamp with time zone NOT NULL,
    osoba integer,
    organizace integer NOT NULL,
    historie integer,
    jazyk character varying(15) COLLATE pg_catalog."default",
    sha_1 text COLLATE pg_catalog."default",
    telefon character varying(100) COLLATE pg_catalog."default",
    history_id integer NOT NULL DEFAULT nextval('uzivatel_historicaluser_history_id_seq'::regclass) PRIMARY KEY,
    history_date timestamp without time zone NOT NULL,
    history_type character varying(1) COLLATE pg_catalog."default" NOT NULL,
    history_user_id integer,
    history_change_reason character varying(254) COLLATE pg_catalog."default",
    CONSTRAINT uzivatel_historicaluser_history_user_id_fkey FOREIGN KEY (history_user_id)
        REFERENCES public.auth_user (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);
