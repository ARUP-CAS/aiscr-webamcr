# Generated by Django 3.2.11 on 2023-03-28 14:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('neidentakce', '0002_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='neidentakce',
            name='id',
        ),
        migrations.AlterField(
            model_name='neidentakce',
            name='dokument_cast',
            field=models.OneToOneField(db_column='dokument_cast', on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='neident_akce', serialize=False, to='dokument.dokumentcast'),
        ),
    ]
