# Generated by Django 3.2.11 on 2022-12-02 11:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('uzivatel', '0001_initial'),
        ('projekt', '0001_initial'),
        ('heslar', '0001_initial'),
        ('core', '0003_soubor_vlastnik'),
    ]

    operations = [
        migrations.AddField(
            model_name='projekt',
            name='organizace',
            field=models.ForeignKey(blank=True, db_column='organizace', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='uzivatel.organizace'),
        ),
        migrations.AddField(
            model_name='projekt',
            name='soubory',
            field=models.OneToOneField(blank=True, db_column='soubory', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='projekt_souboru', to='core.souborvazby'),
        ),
        migrations.AddField(
            model_name='projekt',
            name='typ_projektu',
            field=models.ForeignKey(db_column='typ_projektu', limit_choices_to={'nazev_heslare': 41}, on_delete=django.db.models.deletion.DO_NOTHING, related_name='projekty_typu', to='heslar.heslar', verbose_name='Typ projektů'),
        ),
        migrations.AddField(
            model_name='projekt',
            name='vedouci_projektu',
            field=models.ForeignKey(blank=True, db_column='vedouci_projektu', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='uzivatel.osoba', verbose_name='Vedoucí projektů'),
        ),
        migrations.AlterUniqueTogether(
            name='projektkatastr',
            unique_together={('projekt', 'katastr')},
        ),
    ]
