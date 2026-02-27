from django.db import migrations, models

def add_notifikace_typ(apps, schema_editor):
    """Funkce `add_notifikace_typ` v modulu `webclient.uzivatel.migrations.0021_add_notifikace_typ`.
    
    Zajišťuje dílčí aplikační logiku pro tento modul.
    
    :param apps: Vstupní hodnota používaná při zpracování.
    :param schema_editor: Vstupní hodnota používaná při zpracování.
    :return: Výsledek odpovídající účelu volání.
    """
    NotifikaceTyp = apps.get_model('uzivatel', 'UserNotificationType')
    NotifikaceTyp.objects.get_or_create(ident_cely='S-E-P-02c')
    NotifikaceTyp.objects.get_or_create(ident_cely='S-E-P-02b')
    NotifikaceTyp.objects.get_or_create(ident_cely='S-E-P-02a')

class Migration(migrations.Migration):

    """Třída `Migration` v modulu `webclient.uzivatel.migrations.0021_add_notifikace_typ`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    dependencies = [
        ("uzivatel", "0020_add_notifikace_typ_E-N-07"),
    ]

    operations = [
        migrations.RunPython(add_notifikace_typ),
    ]