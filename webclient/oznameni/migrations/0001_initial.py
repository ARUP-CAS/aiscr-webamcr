# Generated by Django 3.1.3 on 2021-05-20 07:24

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Oznamovatel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
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
