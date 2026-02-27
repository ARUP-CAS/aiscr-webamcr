from django.db import migrations, models

def add_notifikace_typ(apps, schema_editor):
    NotifikaceTyp = apps.get_model('uzivatel', 'UserNotificationType')
    NotifikaceTyp.objects.get_or_create(ident_cely='S-E-P-02c')
    NotifikaceTyp.objects.get_or_create(ident_cely='S-E-P-02b')
    NotifikaceTyp.objects.get_or_create(ident_cely='S-E-P-02a')

class Migration(migrations.Migration):

    dependencies = [
        ("uzivatel", "0020_add_notifikace_typ_E-N-07"),
    ]

    operations = [
        migrations.RunPython(add_notifikace_typ),
    ]