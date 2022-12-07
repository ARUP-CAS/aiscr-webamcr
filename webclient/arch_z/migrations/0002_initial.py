# Generated by Django 3.2.11 on 2022-12-02 11:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('ez', '0001_initial'),
        ('arch_z', '0001_initial'),
        ('heslar', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='externiodkaz',
            name='externi_zdroj',
            field=models.ForeignKey(blank=True, db_column='externi_zdroj', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='externi_odkazy_zdroje', to='ez.externizdroj'),
        ),
        migrations.AddField(
            model_name='archeologickyzaznamkatastr',
            name='archeologicky_zaznam',
            field=models.ForeignKey(db_column='archeologicky_zaznam_id', on_delete=django.db.models.deletion.CASCADE, to='arch_z.archeologickyzaznam'),
        ),
        migrations.AddField(
            model_name='archeologickyzaznamkatastr',
            name='katastr',
            field=models.ForeignKey(db_column='katastr_id', on_delete=django.db.models.deletion.CASCADE, to='heslar.ruiankatastr'),
        ),
    ]
