# Generated by Django 4.2.7 on 2024-01-30 21:03

from django.db import migrations


def populate_organizace_nazev(apps, schema_editor):
    ExterniZdroj = apps.get_model('ez', 'ExterniZdroj')
    for instance in ExterniZdroj.objects.all(organizace__isnull=False):
        instance.save()


class Migration(migrations.Migration):
    dependencies = [
        ("ez", "0007_remove_externizdroj_organizace_nazev_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="externizdroj",
            old_name="organizace_nazev",
            new_name="organizace",
        ),
        migrations.RunPython(populate_organizace_nazev),
    ]
