-- Replace SET_SOURCE_DATABASE_NAME and SET_DATABASE_NAME by database names before running the script

SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = 'SET_SOURCE_DATABASE_NAME' -- ← change this to your DB
  AND pid <> pg_backend_pid();

drop database if exists SET_DATABASE_NAME;

CREATE DATABASE SET_DATABASE_NAME
    WITH
    OWNER = cz_archeologickamapa_api
    TEMPLATE = SET_SOURCE_DATABASE_NAME
    ENCODING = 'UTF8';
