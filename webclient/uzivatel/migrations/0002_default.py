from django.db import migrations
from django_add_default_value import AddDefaultValue

from core.constants import PROJEKT_STAV_OZNAMENY, CESKY, ORGANIZACE_MESICU_DO_ZVEREJNENI_DEFAULT


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('uzivatel', '0001_initial'),
    ]

    operations = [
        AddDefaultValue(
            model_name='User',
            name='is_superuser',
            value=False
        ),
        AddDefaultValue(
            model_name='User',
            name='is_staff',
            value=False
        ),
        AddDefaultValue(
            model_name='User',
            name='is_active',
            value=False
        ),
        AddDefaultValue(
            model_name='User',
            name='jazyk',
            value=CESKY
        ),
        AddDefaultValue(
            model_name='Organizace',
            name='oao',
            value=False
        ),
        AddDefaultValue(
            model_name='Organizace',
            name='mesicu_do_zverejneni',
            value=ORGANIZACE_MESICU_DO_ZVEREJNENI_DEFAULT
        ),
        AddDefaultValue(
            model_name='UserNotificationType',
            name='zasilat_neaktivnim',
            value=False
        ),
    ]
