# Generated by Django 3.2.11 on 2022-05-27 07:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arch_z', '0004_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='archeologickyzaznam',
            name='stav',
            field=models.SmallIntegerField(choices=[(1, 'A1 - Zapsána'), (2, 'A2 - Odeslána'), (3, 'A3 - Archivována')]),
        ),
    ]
