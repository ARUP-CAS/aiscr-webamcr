# Migration to update Meta options from literal strings to gettext_lazy msgids
# This migration updates verbose_name and verbose_name_plural for User, Organizace, and Osoba models
# that previously had literal strings.

from django.db import migrations, models
import django.db.models.functions.comparison


class Migration(migrations.Migration):

    dependencies = [
        ('uzivatel', '0034_backfill_notificationslog_zaznam_ident_cely'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={
                'verbose_name': 'uzivatel.model.User.modelTitle.label',
                'verbose_name_plural': 'uzivatel.model.User.modelTitles.label',
                'db_table': 'auth_user',
            },
        ),
        migrations.AlterModelOptions(
            name='organizace',
            options={
                'verbose_name': 'uzivatel.model.Organizace.modelTitle.label',
                'verbose_name_plural': 'uzivatel.model.Organizace.modelTitles.label',
                'db_table': 'organizace',
                'ordering': [django.db.models.functions.comparison.Collate('nazev_zkraceny', 'cs-CZ-x-icu')],
            },
        ),
        migrations.AlterModelOptions(
            name='osoba',
            options={
                'verbose_name': 'uzivatel.model.Osoba.modelTitle.label',
                'verbose_name_plural': 'uzivatel.model.Osoba.modelTitles.label',
                'db_table': 'osoba',
                'ordering': ['vypis_cely'],
            },
        ),
    ]


