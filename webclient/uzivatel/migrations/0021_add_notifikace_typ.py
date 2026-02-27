from django.db import migrations, models

def add_notifikace_typ(apps, schema_editor):
    """Provádí funkci ``add_notifikace_typ`` v rámci modulu ``webclient.uzivatel.migrations.0021_add_notifikace_typ``."""
    NotifikaceTyp = apps.get_model('uzivatel', 'UserNotificationType')
    NotifikaceTyp.objects.get_or_create(ident_cely='S-E-P-02c')
    NotifikaceTyp.objects.get_or_create(ident_cely='S-E-P-02b')
    NotifikaceTyp.objects.get_or_create(ident_cely='S-E-P-02a')

class Migration(migrations.Migration):

    """Zapouzdřuje chování třídy ``Migration`` pro modul ``webclient.uzivatel.migrations.0021_add_notifikace_typ``."""
    dependencies = [
        ("uzivatel", "0020_add_notifikace_typ_E-N-07"),
    ]

    operations = [
        migrations.RunPython(add_notifikace_typ),
    ]