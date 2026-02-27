from django.db import migrations, models

def add_notifikace_typ(apps, schema_editor):
    """Provádí funkci ``add_notifikace_typ`` v rámci modulu ``webclient.uzivatel.migrations.0023_add_notifikace_typ_E-N-09``."""
    NotifikaceTyp = apps.get_model('uzivatel', 'UserNotificationType')
    NotifikaceTyp.objects.create(ident_cely='E-P-09')
    NotifikaceTyp.objects.create(ident_cely='E-P-10')

class Migration(migrations.Migration):

    """Zapouzdřuje chování třídy ``Migration`` pro modul ``webclient.uzivatel.migrations.0023_add_notifikace_typ_E-N-09``."""
    dependencies = [
        ("uzivatel", "0022_add_notifikace_typ_zpravodaj"),
    ]

    operations = [
        migrations.RunPython(add_notifikace_typ),
    ]