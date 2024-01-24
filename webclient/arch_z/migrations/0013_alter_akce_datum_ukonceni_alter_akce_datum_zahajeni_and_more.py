# Generated by Django 4.2.8 on 2024-01-24 16:57

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("arch_z", "0012_akce_vedouci_snapshot_alter_archeologickyzaznam_stav"),
    ]

    operations = [
        migrations.AlterField(
            model_name="akce",
            name="datum_ukonceni",
            field=models.DateField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name="akce",
            name="datum_zahajeni",
            field=models.DateField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name="archeologickyzaznam",
            name="stav",
            field=models.SmallIntegerField(
                choices=[
                    (1, "arch_z.models.ArcheologickyZaznam.states.AZ1"),
                    (2, "arch_z.models.ArcheologickyZaznam.states.AZ2"),
                    (3, "arch_z.models.ArcheologickyZaznam.states.AZ3"),
                ],
                db_index=True,
            ),
        ),
    ]
