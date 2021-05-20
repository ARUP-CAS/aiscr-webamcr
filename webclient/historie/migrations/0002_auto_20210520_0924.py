# Generated by Django 3.1.3 on 2021-05-20 07:24

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('historie', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='historie',
            name='uzivatel',
            field=models.ForeignKey(db_column='uzivatel', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Uživatel'),
        ),
        migrations.AddField(
            model_name='historie',
            name='vazba',
            field=models.ForeignKey(db_column='vazba', on_delete=django.db.models.deletion.CASCADE, to='historie.historievazby'),
        ),
    ]
