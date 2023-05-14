# Generated by Django 3.2.11 on 2023-02-13 15:20

from django.db import migrations, models
import django.db.models.deletion

from django_add_default_value import AddDefaultValue

from heslar.hesla import PRISTUPNOST_ANONYM_ID


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("arch_z", "0005_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE FUNCTION public.delete_connected_documents()
                RETURNS trigger
                LANGUAGE 'plpgsql'
                COST 100
                VOLATILE NOT LEAKPROOF
            AS $BODY$
                    BEGIN
                        DELETE FROM dokument_cast AS dc
                        WHERE dc.archeologicky_zaznam = old.id
                        AND EXISTS (
                            SELECT FROM komponenta_vazby kv
                            WHERE kv.id = dc.komponenty AND EXISTS (
                                SELECT from komponenta k 
                                WHERE k.komponenta_vazby = kv.id))
                        AND NOT EXISTS (
                                SELECT from neident_akce na 
                                WHERE na.dokument_cast = dc.id);
                        
                        DELETE FROM dokument AS d
                        WHERE d.ident_cely NOT LIKE 'X-%'
                        AND EXISTS (
                            SELECT FROM dokument_cast AS dc
                            WHERE dc.dokument = d.id AND dc.archeologicky_zaznam = old.id AND NOT EXISTS (
                                SELECT FROM dokument_cast AS dci
                                WHERE dci.dokument = d.id AND dci.archeologicky_zaznam != old.id
                            )
                        );
                        RETURN NEW;
                    END;   
            $BODY$;
            """,
            reverse_sql="DROP FUNCTION public.delete_connected_documents;",
        ),
        migrations.RunSQL(
            sql="""
            CREATE TRIGGER delete_connected_documents
                BEFORE DELETE
                ON archeologicky_zaznam
                FOR EACH ROW
                EXECUTE FUNCTION delete_connected_documents();
            """,
            reverse_sql="DROP TRIGGER public.delete_connected_documents;",
        ),
    ]
