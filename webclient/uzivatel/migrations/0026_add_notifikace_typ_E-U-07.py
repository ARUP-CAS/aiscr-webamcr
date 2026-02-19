from django.db import migrations, models

def add_notifikace_typ(apps, schema_editor):
    NotifikaceTyp = apps.get_model('uzivatel', 'UserNotificationType')
    NotifikaceTyp.objects.create(ident_cely='E-U-07')

class Migration(migrations.Migration):

    dependencies = [
        ("uzivatel", "0025_organizace_web"),
    ]

    operations = [
        migrations.RunPython(add_notifikace_typ),
    ]