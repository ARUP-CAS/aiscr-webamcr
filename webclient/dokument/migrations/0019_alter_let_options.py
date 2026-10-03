# Migration to update Meta options for 'let' model from literal string to gettext_lazy msgid
# This migration updates verbose_name_plural from 'Lety' to the msgid format.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dokument', '0018_alter_dokumentextradata_pocet_variant_originalu_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='let',
            options={
                'ordering': ['ident_cely'],
                'verbose_name_plural': 'dokument.model.Let.modelTitles.label',
            },
        ),
    ]


