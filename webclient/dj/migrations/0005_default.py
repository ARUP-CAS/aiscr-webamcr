from django.db import migrations
from django_add_default_value import AddDefaultValue


class Migration(migrations.Migration):
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
