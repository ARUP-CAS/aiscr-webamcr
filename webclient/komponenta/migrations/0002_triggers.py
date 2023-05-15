# Generated by Django 3.2.11 on 2023-02-13 15:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("komponenta", "0001_initial"),
        ("nalez", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE FUNCTION public.delete_connected_komponenta_vazby_relations()
                RETURNS trigger
                LANGUAGE 'plpgsql'
                COST 100
                VOLATILE NOT LEAKPROOF
            AS $BODY$
                    BEGIN
                        DELETE FROM komponenta AS k
                        WHERE k.komponenta_vazby  = old.id
                        ;
                        return OLD
                        ;
                    END;   
            $BODY$;
            """,
            reverse_sql="DROP FUNCTION public.delete_connected_komponenta_vazby_relations;",
        ),
        migrations.RunSQL(
            sql="""
            CREATE TRIGGER delete_connected_komponenta_vazby_relations
                BEFORE DELETE
                ON public.komponenta_vazby
                FOR EACH ROW
                EXECUTE FUNCTION public.delete_connected_komponenta_vazby_relations();
        """,
            reverse_sql="DROP TRIGGER public.delete_connected_komponenta_vazby_relations;",
        ),
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE FUNCTION public.delete_connected_komponenty_relations()
                RETURNS trigger
                LANGUAGE 'plpgsql'
                COST 100
                VOLATILE NOT LEAKPROOF
            AS $BODY$
                BEGIN
                    DELETE FROM komponenta_aktivita AS ka
                    WHERE ka.komponenta = old.id
                    ;
                    DELETE FROM nalez_predmet AS np
                    WHERE np.komponenta = old.id
                    ;
                    DELETE FROM nalez_objekt AS nob
                    WHERE nob.komponenta = old.id
                    ;
                    return OLD
                    ;
                END;    
            $BODY$;
            """,
            reverse_sql="DROP FUNCTION public.delete_connected_komponenty_relations;",
        ),
        migrations.RunSQL(
            sql="""
            CREATE TRIGGER delete_connected_komponenty_relations
                BEFORE DELETE
                ON public.komponenta
                FOR EACH ROW
                EXECUTE FUNCTION public.delete_connected_komponenty_relations();
            """,
            reverse_sql="DROP TRIGGER public.delete_connected_komponenty_relations;",
        ),
    ]
