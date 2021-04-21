# Generated by Django 3.1.3 on 2021-04-21 09:44

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Historie',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datum_zmeny', models.DateTimeField(auto_now_add=True)),
                ('typ_zmeny', models.TextField(choices=[('PX0', 'Oznámení projektu'), ('P01', 'Schválení oznámení projektu'), ('PX1', 'Zapsání projektu'), ('P12', 'Přihlášení projektu'), ('P23', 'Zahájení v terénu projektu'), ('P34', 'Ukončení v terénu projektu'), ('P45', 'Uzavření projektu'), ('P56', 'Archivace projektu'), ('P*7', 'Navržení ke zrušení projektu'), ('P78', 'Rušení projektu'), ('P-1', 'Vrácení projektu'), ('AZ01', 'Zápis archeologického záznamu'), ('AZ12', 'Odeslání archeologického záznamu'), ('AZ23', 'Archivace archeologického záznamu'), ('AZ-1', 'Vrácení archeologického záznamu'), ('D01', 'Zápis dokumentu'), ('D12', 'Odeslání dokumentu'), ('D23', 'Archivace dokumentu'), ('D-1', 'Vrácení dokumentu'), ('SN01', 'Zápis samostatného nálezu'), ('SN12', 'Odeslání samostatného nálezu'), ('SN23', 'Potvrzení samostatného nálezu'), ('SN34', 'Archivace samostatného nálezu'), ('SN-1', 'Vrácení samostatného nálezu'), ('PI01', 'Zápis pian'), ('PI12', 'Potvrzení pian'), ('EZ01', 'Import externí zdroj'), ('EZ12', 'Zápis externí zdroj'), ('EZ23', 'Potvrzení externí zdroj'), ('EZ-1', 'Vrácení externí zdroj')])),
                ('poznamka', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'historie',
                'db_table': 'historie',
            },
        ),
        migrations.CreateModel(
            name='HistorieVazby',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('typ_vazby', models.TextField(choices=[('projekt', 'Projekt'), ('dokument', 'Dokument'), ('samostatny_nalez', 'Samostatný nález'), ('uzivatel', 'Uživatel'), ('pian', 'Pian'), ('uzivatel_spoluprace', 'Uživatel spolupráce'), ('externi_zdroj', 'Externí zdroj'), ('archeologicky_zaznam', 'Archeologický záznam')], max_length=24)),
            ],
            options={
                'verbose_name': 'historie_vazby',
                'db_table': 'historie_vazby',
            },
        ),
    ]
