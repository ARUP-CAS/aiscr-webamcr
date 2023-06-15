# Generated by Django 4.1.7 on 2023-05-27 09:22

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("arch_z", "0007_default"),
    ]

    operations = [
        migrations.AlterField(
            model_name="akce",
            name="typ",
            field=models.CharField(
                choices=[("R", "Projektova"), ("N", "Samostatna")],
                db_index=True,
                max_length=1,
            ),
        ),
    ]
