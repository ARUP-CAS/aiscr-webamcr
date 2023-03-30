from django.db import migrations


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('dj', '0003_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE FUNCTION public.delete_unconfirmed_pian()
                RETURNS trigger
                LANGUAGE 'plpgsql'
                COST 100
                VOLATILE NOT LEAKPROOF
            AS $BODY$
                BEGIN
                    DELETE FROM pian
                    WHERE pian.id = old.pian AND pian.ident_cely NOT LIKE 'N-%'
                    AND NOT EXISTS (
                        SELECT FROM dokumentacni_jednotka
                        WHERE pian.id = dokumentacni_jednotka.pian
                    );
                    RETURN NEW;
                END;
            $BODY$;
            """,
            reverse_sql="DROP FUNCTION public.delete_unconfirmed_pian;"
        ),
        migrations.RunSQL(
            sql="""
            CREATE TRIGGER delete_unconfirmed_pian
                AFTER DELETE
                ON dokumentacni_jednotka
                FOR EACH ROW
                EXECUTE FUNCTION delete_unconfirmed_pian();
            """,
            reverse_sql="DROP TRIGGER public.delete_unconfirmed_pian;"
        ),
    ]
