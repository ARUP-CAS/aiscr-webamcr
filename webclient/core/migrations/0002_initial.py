# Generated by Django 3.2.11 on 2023-02-14 19:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('pian', '0001_initial'),
        ('historie', '0001_initial'),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='soubor',
            name='historie',
            field=models.OneToOneField(db_column='historie', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='soubor_historie', to='historie.historievazby'),
        ),
        migrations.AddField(
            model_name='soubor',
            name='vazba',
            field=models.ForeignKey(db_column='vazba', on_delete=django.db.models.deletion.CASCADE, related_name='soubory', to='core.souborvazby'),
        ),
        migrations.AddField(
            model_name='geommigrationjobwgs84error',
            name='pian',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pian.pian'),
        ),
        migrations.AddField(
            model_name='geommigrationjobsjtskerror',
            name='pian',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pian.pian'),
        ),
    ]
