# Generated by Django 3.2.11 on 2023-02-09 21:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arch_z', '0005_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='externiodkaz',
            name='paginace',
            field=models.TextField(null=True),
        ),
    ]
