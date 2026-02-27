from django.db import migrations, models

def add_notifikace_typ(apps, schema_editor):
    """Zajišťuje logiku funkce ``add_notifikace_typ``.
    
    :param apps: Vstupní hodnota parametru ``apps`` použitého při zpracování.
    :param schema_editor: Vstupní hodnota parametru ``schema_editor`` použitého při zpracování.
    :return: Návratová hodnota funkce po zpracování vstupních dat.
    """
    NotifikaceTyp = apps.get_model('uzivatel', 'UserNotificationType')
    NotifikaceTyp.objects.create(ident_cely='E-U-07')

class Migration(migrations.Migration):

    """Zapouzdřuje chování třídy ``Migration`` pro modul ``webclient.uzivatel.migrations.0026_add_notifikace_typ_E-U-07``."""
    dependencies = [
        ("uzivatel", "0025_organizace_web"),
    ]

    operations = [
        migrations.RunPython(add_notifikace_typ),
    ]