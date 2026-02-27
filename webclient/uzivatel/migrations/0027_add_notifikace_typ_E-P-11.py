from django.db import migrations, models

def add_notifikace_typ(apps, schema_editor):
    """Funkce `add_notifikace_typ` v modulu `webclient.uzivatel.migrations.0027_add_notifikace_typ_E-P-11`.
    
    Zajišťuje dílčí aplikační logiku pro tento modul.
    
    :param apps: Vstupní hodnota používaná při zpracování.
    :param schema_editor: Vstupní hodnota používaná při zpracování.
    :return: Výsledek odpovídající účelu volání.
    """
    NotifikaceTyp = apps.get_model('uzivatel', 'UserNotificationType')
    NotifikaceTyp.objects.create(ident_cely='E-P-11')

class Migration(migrations.Migration):

    """Třída `Migration` v modulu `webclient.uzivatel.migrations.0027_add_notifikace_typ_E-P-11`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    dependencies = [
        ("uzivatel", "0026_add_notifikace_typ_E-U-07"),
    ]

    operations = [
        migrations.RunPython(add_notifikace_typ),
    ]