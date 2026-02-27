from django.db import migrations
from django_add_default_value import AddDefaultValue

from core.constants import  PROJEKT_STAV_OZNAMENY


class Migration(migrations.Migration):
    """Třída `Migration` v modulu `webclient.projekt.migrations.0004_default`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    initial = True

    dependencies = [
        ('projekt', '0003_triggers'),
    ]

    operations = [
        AddDefaultValue(
            model_name='Projekt',
            name='stav',
            value=PROJEKT_STAV_OZNAMENY
        ),
    ]
