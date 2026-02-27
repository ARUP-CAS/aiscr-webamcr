from django.db import migrations

try:
    from core.setting_models import CustomAdminSettings
except ImportError:
    from core.models import CustomAdminSettings


def insert_customadminsettings_heslar_group(apps, schema_editor):
    """Provádí funkci ``insert_customadminsettings_heslar_group`` v rámci modulu ``webclient.core.migrations.0018_insert_custom_admin_settings_user``."""
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
