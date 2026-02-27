from django.db import migrations
from django_add_default_value import AddDefaultValue


class Migration(migrations.Migration):
    """Zapouzdřuje chování třídy ``Migration`` pro modul ``webclient.pas.migrations.0003_default``."""
    initial = True

    dependencies = [
        ('pas', '0002_initial'),
    ]

    operations = [
        AddDefaultValue(
            model_name='SamostatnyNalez',
            name='geom_system',
            value="wgs84"
        ),
        AddDefaultValue(
            model_name='SamostatnyNalez',
            name='predano',
            value=False
        ),
    ]
