# Generated by Django 3.2.11 on 2022-12-02 11:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('komponenta', '0001_initial'),
        ('arch_z', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DokumentacniJednotka',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nazev', models.TextField(blank=True, null=True)),
                ('negativni_jednotka', models.BooleanField()),
                ('ident_cely', models.TextField(blank=True, null=True, unique=True)),
                ('archeologicky_zaznam', models.ForeignKey(db_column='archeologicky_zaznam', on_delete=django.db.models.deletion.CASCADE, related_name='dokumentacni_jednotky_akce', to='arch_z.archeologickyzaznam')),
                ('komponenty', models.OneToOneField(blank=True, db_column='komponenty', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='dokumentacni_jednotka', to='komponenta.komponentavazby')),
            ],
            options={
                'db_table': 'dokumentacni_jednotka',
                'ordering': ['ident_cely'],
            },
        ),
    ]
