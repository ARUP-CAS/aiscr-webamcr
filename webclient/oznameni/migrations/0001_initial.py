# Generated by Django 3.2.11 on 2023-02-06 20:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('projekt', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Oznamovatel',
            fields=[
                ('projekt', models.OneToOneField(db_column='projekt', on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='oznamovatel', serialize=False, to='projekt.projekt')),
                ('email', models.TextField()),
                ('adresa', models.TextField()),
                ('odpovedna_osoba', models.TextField()),
                ('oznamovatel', models.TextField()),
                ('telefon', models.TextField()),
            ],
            options={
                'verbose_name': 'oznamovatele',
                'db_table': 'oznamovatel',
            },
        ),
    ]
