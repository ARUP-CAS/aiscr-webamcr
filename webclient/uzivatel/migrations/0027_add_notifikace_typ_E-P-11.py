from django.db import migrations, models

def add_notifikace_typ(apps, schema_editor):
    """Provádí funkci ``add_notifikace_typ`` v rámci modulu ``webclient.uzivatel.migrations.0027_add_notifikace_typ_E-P-11``."""
    NotifikaceTyp = apps.get_model('uzivatel', 'UserNotificationType')
    NotifikaceTyp.objects.create(ident_cely='E-P-11')

class Migration(migrations.Migration):

    """Zapouzdřuje chování třídy ``Migration`` pro modul ``webclient.uzivatel.migrations.0027_add_notifikace_typ_E-P-11``."""
    dependencies = [
        ("uzivatel", "0026_add_notifikace_typ_E-U-07"),
    ]

    operations = [
        migrations.RunPython(add_notifikace_typ),
    ]