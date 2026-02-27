from django.db import migrations, models

def add_notifikace_typ(apps, schema_editor):
    NotifikaceTyp = apps.get_model('uzivatel', 'UserNotificationType')
    NotifikaceTyp.objects.create(ident_cely='E-P-11')

class Migration(migrations.Migration):

    dependencies = [
        ("uzivatel", "0026_add_notifikace_typ_E-U-07"),
    ]

    operations = [
        migrations.RunPython(add_notifikace_typ),
    ]