# Generated by Django 3.2.11 on 2022-11-30 14:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('arch_z', '0007_alter_akce_typ'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='archeologickyzaznam',
            name='stav_stary',
        ),
    ]
