# Generated by Django 3.2.11 on 2023-02-13 15:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("dokument", "0003_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE FUNCTION public.delete_related_komponenta()
                RETURNS trigger
                LANGUAGE 'plpgsql'
                COST 100
                VOLATILE NOT LEAKPROOF
            AS $BODY$
                BEGIN
                    DELETE FROM komponenta_vazby WHERE komponenta_vazby.id = old.komponenty;
                    RETURN NEW;
                END;    
            $BODY$;
            """,
            reverse_sql="DROP FUNCTION public.delete_related_komponenta;",
        ),
        migrations.RunSQL(
            sql="""
            CREATE TRIGGER delete_related_komponenta_dokument_cast
                AFTER DELETE
                ON dokument_cast
                FOR EACH ROW
                EXECUTE FUNCTION delete_related_komponenta();
            """,
            reverse_sql="DROP TRIGGER public.delete_related_komponenta;",
        ),
        migrations.RunSQL(
            sql="""
            CREATE TRIGGER delete_related_komponenta_dokumentacni_jednotka
                AFTER DELETE
                ON dokumentacni_jednotka
                FOR EACH ROW
                EXECUTE FUNCTION delete_related_komponenta();
            """,
            reverse_sql="DROP TRIGGER public.delete_related_komponenta_dokumentacni_jednotka;",
        ),
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE FUNCTION public.delete_related_neident_dokument_cast()
                RETURNS trigger
                LANGUAGE 'plpgsql'
                COST 100
                VOLATILE NOT LEAKPROOF
            AS $BODY$
                BEGIN
                    DELETE FROM neident_akce AS na
                    WHERE na.dokument_cast = old.id
                    ;
                    DELETE FROM neident_akce_vedouci AS nav
                    WHERE nav.neident_akce = old.id
                    ;
                    return null
                    ;
                END;    
            $BODY$;
            """,
            reverse_sql="DROP FUNCTION public.delete_related_neident_dokument_cast;",
        ),
        migrations.RunSQL(
            sql="""
            CREATE TRIGGER delete_related_neident_dokument_cast
                BEFORE DELETE
                ON dokument_cast
                FOR EACH ROW
                EXECUTE FUNCTION delete_related_neident_dokument_cast();
            """,
            reverse_sql="DROP TRIGGER public.delete_related_neident_dokument_cast;",
        ),
    ]
