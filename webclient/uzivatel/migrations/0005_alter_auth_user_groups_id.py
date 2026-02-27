from django.db import migrations


class Migration(migrations.Migration):

    """Zapouzdřuje chování třídy ``Migration`` pro modul ``webclient.uzivatel.migrations.0005_alter_auth_user_groups_id``."""
    dependencies = [
        ('uzivatel', '0004_alter_osoba_vypis_cely'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            SELECT setval(pg_get_serial_sequence('auth_user_groups', 'id'), (select max(id) from auth_user_groups));
            """,
            reverse_sql="""
            SELECT setval(pg_get_serial_sequence('auth_user_groups', 'id'), 1);
            """
        ),
        migrations.RunSQL(
            sql="""
            SELECT setval(pg_get_serial_sequence('auth_user_notifikace_typ', 'id'), (select max(id) from auth_user_notifikace_typ));
            """,
            reverse_sql="""
            SELECT setval(pg_get_serial_sequence('auth_user_notifikace_typ', 'id'), 1);
            """
        ),
    ]
