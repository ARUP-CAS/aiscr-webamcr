from django.db import migrations
from django_add_default_value import AddDefaultValue

from core.constants import PIAN_NEPOTVRZEN


class Migration(migrations.Migration):
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
