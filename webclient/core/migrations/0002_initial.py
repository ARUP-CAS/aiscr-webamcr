# Generated by Django 3.2.11 on 2022-12-13 14:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('historie', '0001_initial'),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='soubor',
            name='historie',
            field=models.OneToOneField(db_column='historie', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='soubor_historie', to='historie.historievazby'),
        ),
        migrations.AddField(
            model_name='soubor',
            name='vazba',
            field=models.ForeignKey(db_column='vazba', on_delete=django.db.models.deletion.CASCADE, related_name='soubory', to='core.souborvazby'),
        ),
    ]
