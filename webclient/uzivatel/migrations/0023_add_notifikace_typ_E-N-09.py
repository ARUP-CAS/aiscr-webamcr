from django.db import migrations, models

def add_notifikace_typ(apps, schema_editor):
    NotifikaceTyp = apps.get_model('uzivatel', 'UserNotificationType')
    NotifikaceTyp.objects.create(ident_cely='E-P-09')
    NotifikaceTyp.objects.create(ident_cely='E-P-10')

class Migration(migrations.Migration):

    dependencies = [
        ("uzivatel", "0022_add_notifikace_typ_zpravodaj"),
    ]

    operations = [
        migrations.RunPython(add_notifikace_typ),
    ]