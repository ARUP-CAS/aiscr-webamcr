from django.db import migrations, models

def add_notifikace_typ(apps, schema_editor):
    NotifikaceTyp = apps.get_model('uzivatel', 'UserNotificationType')
    NotifikaceTyp.objects.get_or_create(ident_cely='zpravodaj')

class Migration(migrations.Migration):

    dependencies = [
        ("uzivatel", "0021_add_notifikace_typ"),
    ]

    operations = [
        migrations.RunPython(add_notifikace_typ),
    ]