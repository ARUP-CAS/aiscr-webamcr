# Generated by Django 3.1.3 on 2021-04-06 18:32

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('projekt', '0001_initial'),
        ('heslar', '0001_initial'),
        ('uzivatel', '0001_initial'),
        ('core', '0002_soubor_vlastnik'),
        ('pas', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='samostatnynalez',
            name='nalezce',
            field=models.ForeignKey(blank=True, db_column='nalezce', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='uzivatel.osoba'),
        ),
        migrations.AddField(
            model_name='samostatnynalez',
            name='obdobi',
            field=models.ForeignKey(blank=True, db_column='obdobi', limit_choices_to={'nazev_heslare': 15}, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='samostatne_nalezy_obdobi', to='heslar.heslar'),
        ),
        migrations.AddField(
            model_name='samostatnynalez',
            name='okolnosti',
            field=models.ForeignKey(blank=True, db_column='okolnosti', limit_choices_to={'nazev_heslare': 14}, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='samostatne_nalezy_okolnosti', to='heslar.heslar'),
        ),
        migrations.AddField(
            model_name='samostatnynalez',
            name='predano_organizace',
            field=models.ForeignKey(blank=True, db_column='predano_organizace', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='uzivatel.organizace'),
        ),
        migrations.AddField(
            model_name='samostatnynalez',
            name='pristupnost',
            field=models.ForeignKey(db_column='pristupnost', on_delete=django.db.models.deletion.DO_NOTHING, to='heslar.heslar'),
        ),
        migrations.AddField(
            model_name='samostatnynalez',
            name='projekt',
            field=models.ForeignKey(db_column='projekt', on_delete=django.db.models.deletion.DO_NOTHING, related_name='samostatne_nalezy', to='projekt.projekt'),
        ),
        migrations.AddField(
            model_name='samostatnynalez',
            name='soubory',
            field=models.ForeignKey(blank=True, db_column='soubory', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='core.souborvazby'),
        ),
        migrations.AddField(
            model_name='samostatnynalez',
            name='specifikace',
            field=models.ForeignKey(blank=True, db_column='specifikace', limit_choices_to={'nazev_heslare': 30}, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='samostatne_nalezy_specifikace', to='heslar.heslar'),
        ),
    ]
