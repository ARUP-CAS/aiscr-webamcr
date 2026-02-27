from django.db import migrations
from django_add_default_value import AddDefaultValue

from core.constants import PIAN_NEPOTVRZEN


class Migration(migrations.Migration):
    """Třída `Migration` v modulu `webclient.pian.migrations.0002_default`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    initial = True

    dependencies = [
        ('pian', '0001_initial'),
    ]

    operations = [
        AddDefaultValue(
            model_name='Pian',
            name='stav',
            value=PIAN_NEPOTVRZEN
        ),
        AddDefaultValue(
            model_name='Pian',
            name='geom_system',
            value='wgs84'
        ),
    ]
