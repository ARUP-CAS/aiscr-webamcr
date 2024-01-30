from django.db import migrations


def populate_organizace_nazev(apps, schema_editor):
    ExterniZdroj = apps.get_model('ez', 'ExterniZdroj')
    for instance in ExterniZdroj.objects.all():
        if instance.organizace:
            instance.organizace_nazev = instance.organizace.nazev
            instance.suppress_signal = True
            instance.save()


class Migration(migrations.Migration):

    dependencies = [
        ('ez', '0004_externizdrojsekvence_and_more'),
    ]

    operations = [
        migrations.RunPython(populate_organizace_nazev),
    ]
