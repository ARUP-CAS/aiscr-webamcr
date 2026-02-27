from django.db import migrations

try:
    from core.setting_models import CustomAdminSettings
except ImportError:
    from core.models import CustomAdminSettings


def insert_customadminsettings_heslar_group(apps, schema_editor):
    """Funkce `insert_customadminsettings_heslar_group` v modulu `webclient.core.migrations.0018_insert_custom_admin_settings_user`.
    
    Zajišťuje dílčí aplikační logiku pro tento modul.
    
    :param apps: Vstupní hodnota používaná při zpracování.
    :param schema_editor: Vstupní hodnota používaná při zpracování.
    :return: Výsledek odpovídající účelu volání.
    """
    CustomAdminSettings.objects.create(
        item_group='constants',
        item_id='user',
        value='''
        {
            "ADMIN_USER" : "U-000322"
            
        }
        '''
    )


class Migration(migrations.Migration):
    """Třída `Migration` v modulu `webclient.core.migrations.0018_insert_custom_admin_settings_user`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    dependencies = [
        ('core', '0017_insert_customadminsettings'),
    ]

    operations = [
        migrations.RunPython(insert_customadminsettings_heslar_group),
    ]
