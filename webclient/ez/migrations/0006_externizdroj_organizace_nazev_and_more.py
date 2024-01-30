# Generated by Django 4.2.7 on 2024-01-30 20:44

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ez", "0005_change_organizace_field_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="externizdroj",
            name="organizace_nazev",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="externizdroj",
            name="stav",
            field=models.SmallIntegerField(
                choices=[
                    (1, "ez.models.externiZdroj.states.zapsany.label"),
                    (2, "ez.models.externiZdroj.states.odeslany.label"),
                    (3, "ez.models.externiZdroj.states.potvrzeny.label"),
                ]
            ),
        ),
    ]