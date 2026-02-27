from django.db import migrations, models


class Migration(migrations.Migration):

    """Třída `Migration` v modulu `webclient.ez.migrations.0005_change_organizace_field_type`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    dependencies = [
        ('ez', '0004_externizdrojsekvence_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name="externizdroj",
            name="organizace_nazev",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
