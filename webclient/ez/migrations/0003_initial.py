# Generated by Django 3.2.11 on 2022-12-13 14:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('uzivatel', '0001_initial'),
        ('ez', '0002_initial'),
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
        migrations.AddField(
            model_name='externizdroj',
            name='autori',
            field=models.ManyToManyField(related_name='ez_autori', through='ez.ExterniZdrojAutor', to='uzivatel.Osoba'),
        ),
        migrations.AddField(
            model_name='externizdroj',
            name='editori',
            field=models.ManyToManyField(blank=True, related_name='ez_editori', through='ez.ExterniZdrojEditor', to='uzivatel.Osoba'),
        ),
        migrations.AlterUniqueTogether(
            name='externizdrojeditor',
            unique_together={('poradi', 'externi_zdroj'), ('externi_zdroj', 'editor')},
        ),
        migrations.AlterUniqueTogether(
            name='externizdrojautor',
            unique_together={('externi_zdroj', 'poradi')},
        ),
    ]
