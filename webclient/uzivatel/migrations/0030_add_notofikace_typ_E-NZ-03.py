from django.db import migrations

def add_notifikace_typ(apps, schema_editor):
    NotifikaceTyp = apps.get_model('uzivatel', 'UserNotificationType')
    NotifikaceTyp.objects.create(ident_cely='E-NZ-03')

class Migration(migrations.Migration):

    dependencies = [
        ("uzivatel", "0029_alter_notificationslog_options"),
    ]

    operations = [
        migrations.RunPython(add_notifikace_typ),
    ]