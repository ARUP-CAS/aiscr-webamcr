from django.db import migrations
from django_add_default_value import AddDefaultValue


class Migration(migrations.Migration):
    """Třída `Migration` v modulu `webclient.dj.migrations.0005_default`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    initial = True

    dependencies = [
        ('dj', '0004_triggers'),
    ]

    operations = [
        AddDefaultValue(
            model_name='DokumentacniJednotka',
            name='negativni_jednotka',
            value=False
        ),
    ]
