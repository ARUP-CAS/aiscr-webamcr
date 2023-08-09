from django.db import migrations


class Migration(migrations.Migration):

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
