from django.db import migrations
from django_add_default_value import AddDefaultValue

from core.constants import  PROJEKT_STAV_OZNAMENY


class Migration(migrations.Migration):
    """Zapouzdřuje chování třídy ``Migration`` pro modul ``webclient.projekt.migrations.0004_default``."""
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
