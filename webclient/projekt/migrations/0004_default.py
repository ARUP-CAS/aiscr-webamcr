from django.db import migrations
from django_add_default_value import AddDefaultValue

from core.constants import  PROJEKT_STAV_OZNAMENY


class Migration(migrations.Migration):
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
