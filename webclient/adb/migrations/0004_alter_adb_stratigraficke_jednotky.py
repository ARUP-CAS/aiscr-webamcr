# Generated by Django 3.2.11 on 2022-11-18 17:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adb', '0003_alter_adb_podnet'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adb',
            name='stratigraficke_jednotky',
            field=models.TextField(null=True),
        ),
    ]
