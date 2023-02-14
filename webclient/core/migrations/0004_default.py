from django.db import migrations, models
import django.db.models.deletion
from django_add_default_value import AddDefaultValue


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('core', '0003_geom_functions'),
    ]

    operations = [
        AddDefaultValue(
            model_name='OdstavkaSystemu',
            name='status',
            value=True
        ),
        AddDefaultValue(
            model_name='GeomMigrationJob',
            name='count_selected_wgs84',
            value=0
        ),
        AddDefaultValue(
            model_name='GeomMigrationJob',
            name='count_selected_sjtsk',
            value=0
        ),
        AddDefaultValue(
            model_name='GeomMigrationJob',
            name='count_updated_wgs84',
            value=0
        ),
        AddDefaultValue(
            model_name='GeomMigrationJob',
            name='count_updated_sjtsk',
            value=0
        ),
        AddDefaultValue(
            model_name='GeomMigrationJob',
            name='count_selected_wgs84',
            value=0
        ),
        AddDefaultValue(
            model_name='GeomMigrationJob',
            name='count_error_sjtsk',
            value=0
        ),
    ]