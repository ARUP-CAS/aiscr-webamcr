from django.db import connection


def my_custom_sql(self):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            DO
            $do$
            BEGIN
                IF EXISTS (
                  SELECT FROM pg_catalog.pg_roles
                  WHERE  rolname = 'cz_archeologickamapa_api_view') THEN
                  RAISE NOTICE 'Role "my_user" already exists. Skipping.';
                ELSE
                  CREATE ROLE cz_archeologickamapa_api_view LOGIN PASSWORD 'never_used_password';
                END IF;
            END
            $do$;
            GRANT SELECT
            ON ALL TABLES
            IN SCHEMA "public"
            TO cz_archeologickamapa_api_view;
        """
        )
