from django.db import migrations

try:
    from core.setting_models import CustomAdminSettings
except ImportError:
    from core.models import CustomAdminSettings


def insert_customadminsettings_heslar_group(apps, schema_editor):
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
    dependencies = [
        ('core', '0017_insert_customadminsettings'),
    ]

    operations = [
        migrations.RunPython(insert_customadminsettings_heslar_group),
    ]
