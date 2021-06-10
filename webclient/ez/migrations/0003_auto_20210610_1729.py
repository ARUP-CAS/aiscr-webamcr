# Generated by Django 3.1.3 on 2021-06-10 15:29

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('ez', '0002_auto_20210610_1729'),
        ('uzivatel', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='externizdrojeditor',
            name='editor',
            field=models.ForeignKey(db_column='editor', on_delete=django.db.models.deletion.DO_NOTHING, to='uzivatel.osoba'),
        ),
        migrations.AddField(
            model_name='externizdrojautor',
            name='autor',
            field=models.ForeignKey(db_column='autor', on_delete=django.db.models.deletion.DO_NOTHING, to='uzivatel.osoba'),
        ),
        migrations.AlterUniqueTogether(
            name='externizdrojeditor',
            unique_together={('externi_zdroj', 'editor'), ('poradi', 'externi_zdroj')},
        ),
        migrations.AlterUniqueTogether(
            name='externizdrojautor',
            unique_together={('externi_zdroj', 'autor')},
        ),
    ]
