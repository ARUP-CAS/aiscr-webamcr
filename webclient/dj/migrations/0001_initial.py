# Generated by Django 3.2.11 on 2023-02-14 19:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('arch_z', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DokumentacniJednotka',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nazev', models.TextField(blank=True, null=True)),
                ('negativni_jednotka', models.BooleanField(default=False)),
                ('ident_cely', models.TextField(unique=True)),
                ('archeologicky_zaznam', models.ForeignKey(db_column='archeologicky_zaznam', on_delete=django.db.models.deletion.CASCADE, related_name='dokumentacni_jednotky_akce', to='arch_z.archeologickyzaznam')),
            ],
            options={
                'db_table': 'dokumentacni_jednotka',
                'ordering': ['ident_cely'],
            },
        ),
    ]
