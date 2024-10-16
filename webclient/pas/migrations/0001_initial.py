# Generated by Django 3.2.11 on 2023-02-14 19:39

import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('historie', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SamostatnyNalez',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('evidencni_cislo', models.TextField(blank=True, null=True)),
                ('lokalizace', models.TextField(blank=True, null=True)),
                ('hloubka', models.PositiveIntegerField(blank=True, null=True)),
                ('geom', django.contrib.gis.db.models.fields.PointField(blank=True, null=True, srid=4326)),
                ('geom_sjtsk', django.contrib.gis.db.models.fields.PointField(blank=True, null=True, srid=5514)),
                ('geom_system', models.TextField(default='4326')),
                ('presna_datace', models.TextField(blank=True, null=True)),
                ('poznamka', models.TextField(blank=True, null=True)),
                ('datum_nalezu', models.DateField(blank=True, null=True)),
                ('stav', models.SmallIntegerField(choices=[(1, "pas.models.samostatnyNalez.states.zapsany.label"), (2, "pas.models.samostatnyNalez.states.odeslany.label"), (3, "pas.models.samostatnyNalez.states.potvrzeny.label"), (4, "pas.models.samostatnyNalez.states.archivovany.label")])),
                ('predano', models.BooleanField(blank=True, choices=[(True, "pas.models.samostatnyNalez.predano.ano"), (False, "pas.models.samostatnyNalez.predano.ne")], default=False, null=True)),
                ('ident_cely', models.TextField(unique=True)),
                ('pocet', models.TextField(blank=True, null=True)),
                ('geom_updated_at', models.DateTimeField(blank=True, null=True)),
                ('geom_sjtsk_updated_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'db_table': 'samostatny_nalez',
            },
        ),
        migrations.CreateModel(
            name='UzivatelSpoluprace',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stav', models.SmallIntegerField(choices=[(1, "pas.models.uzivatelSpoluprace.states.neaktivni.label"), (2, "pas.models.uzivatelSpoluprace.states.aktivni.label")])),
                ('historie', models.OneToOneField(blank=True, db_column='historie', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='spoluprace_historie', to='historie.historievazby')),
            ],
            options={
                'db_table': 'uzivatel_spoluprace',
            },
        ),
        migrations.AddConstraint(
            model_name="samostatnynalez",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(("geom_system", "5514"), ("geom_sjtsk__isnull", False)),
                    models.Q(("geom_system", "5514*"), ("geom_sjtsk__isnull", False)),
                    models.Q(("geom_system", "4326"), ("geom__isnull", False)),
                    models.Q(("geom_sjtsk__isnull", True), ("geom__isnull", True)),
                    _connector="OR",
                ),
                name="samostatny_nalez_geom_check",
            ),
        ),
    ]
