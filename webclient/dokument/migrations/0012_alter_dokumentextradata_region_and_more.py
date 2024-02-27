# Generated by Django 4.2.8 on 2024-02-27 10:41

from django.db import migrations, models
import django.db.models.deletion


def clear_licence_field(apps, schema_editor):
    Dokument = apps.get_model('dokument', 'Dokument')
    for instance in Dokument.objects.all():
        instance.licence = None
        instance.save()


def copy_licence_data(apps, schema_editor):
    Dokument = apps.get_model('dokument', 'Dokument')
    for instance in Dokument.objects.all():
        instance.licence = instance.licence_new
        instance.save()


class Migration(migrations.Migration):

    dependencies = [
        ("heslar", "0006_alter_heslar_ident_cely_alter_heslardatace_obdobi_and_more"),
        ("dokument", "0011_alter_dokumentextradata_region_and_more"),
    ]

    operations = [
        migrations.RunPython(clear_licence_field),
        migrations.AlterField(
            model_name="dokument",
            name="licence",
            field=models.ForeignKey(
                limit_choices_to={"nazev_heslare": 45},
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="dokumenty_licence_temp",
                to="heslar.heslar",
            ),
        ),
        migrations.RunPython(copy_licence_data),
    ]
