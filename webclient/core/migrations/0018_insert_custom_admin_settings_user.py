from django.db import migrations

try:
    from core.setting_models import CustomAdminSettings
except ImportError:
    from core.models import CustomAdminSettings


def insert_customadminsettings_heslar_group(apps, schema_editor):
    """Zajišťuje logiku funkce ``insert_customadminsettings_heslar_group``.
    
    :param apps: Vstupní hodnota parametru ``apps`` použitého při zpracování.
    :param schema_editor: Vstupní hodnota parametru ``schema_editor`` použitého při zpracování.
    :return: Návratová hodnota funkce po zpracování vstupních dat.
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
    """Zapouzdřuje chování třídy ``Migration`` pro modul ``webclient.core.migrations.0018_insert_custom_admin_settings_user``."""
    dependencies = [
        ('core', '0017_insert_customadminsettings'),
    ]

    operations = [
        migrations.RunPython(insert_customadminsettings_heslar_group),
    ]
