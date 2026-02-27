from django.db import migrations, models

def add_notifikace_typ(apps, schema_editor):
    """Provádí funkci ``add_notifikace_typ`` v rámci modulu ``webclient.uzivatel.migrations.0022_add_notifikace_typ_zpravodaj``."""
    NotifikaceTyp = apps.get_model('uzivatel', 'UserNotificationType')
    NotifikaceTyp.objects.get_or_create(ident_cely='zpravodaj')

class Migration(migrations.Migration):

    """Zapouzdřuje chování třídy ``Migration`` pro modul ``webclient.uzivatel.migrations.0022_add_notifikace_typ_zpravodaj``."""
    dependencies = [
        ("uzivatel", "0021_add_notifikace_typ"),
    ]

    operations = [
        migrations.RunPython(add_notifikace_typ),
    ]