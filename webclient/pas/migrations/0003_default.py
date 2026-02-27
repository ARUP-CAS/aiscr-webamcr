from django.db import migrations
from django_add_default_value import AddDefaultValue


class Migration(migrations.Migration):
    """Třída `Migration` v modulu `webclient.pas.migrations.0003_default`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
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
