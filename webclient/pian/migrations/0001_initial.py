# Generated by Django 3.2.11 on 2023-02-14 19:39

import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('historie', '0001_initial'),
        ('heslar', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Kladyzm',
            fields=[
                ('gid', models.AutoField(primary_key=True, serialize=False)),
                ('objectid', models.IntegerField(unique=True)),
                ('kategorie', models.IntegerField(choices=[(1, '1:10 000'), (2, '1:25 000'), (3, '1:50 000'), (4, '1:100 000'), (5, '1:200 000')])),
                ('cislo', models.CharField(max_length=8, unique=True)),
                ('natoceni', models.DecimalField(decimal_places=11, max_digits=12)),
                ('shape_leng', models.DecimalField(decimal_places=6, max_digits=12)),
                ('shape_area', models.DecimalField(decimal_places=2, max_digits=12)),
                ('the_geom', django.contrib.gis.db.models.fields.PolygonField(srid=5514)),
            ],
            options={
                'db_table': 'kladyzm',
            },
        ),
        migrations.CreateModel(
            name='PianSekvence',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sekvence', models.IntegerField()),
                ('katastr', models.BooleanField()),
                ('kladyzm50', models.ForeignKey(db_column='kladyzm_id', on_delete=django.db.models.deletion.RESTRICT, to='pian.kladyzm')),
            ],
            options={
                'db_table': 'pian_sekvence',
            },
        ),
        migrations.CreateModel(
            name='Pian',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('geom', django.contrib.gis.db.models.fields.GeometryField(srid=4326)),
                ('geom_sjtsk', django.contrib.gis.db.models.fields.GeometryField(blank=True, null=True, srid=5514)),
                ('geom_system', models.CharField(default="4326", max_length=6)),
                ('ident_cely', models.CharField(unique=True, max_length=13)),
                ('stav', models.SmallIntegerField(choices=[(1, "pian.models.pian.states.nepotvrzen"), (2, "pian.models.pian.states.potvrzen")], default=1)),
                ('historie', models.OneToOneField(null=True, db_column='historie', on_delete=django.db.models.deletion.SET_NULL, related_name='pian_historie', to='historie.historievazby')),
                ('presnost', models.ForeignKey(db_column='presnost', limit_choices_to=models.Q(('nazev_heslare', 24), ('zkratka__lt', '4')), on_delete=django.db.models.deletion.RESTRICT, related_name='piany_presnosti', to='heslar.heslar')),
                ('typ', models.ForeignKey(db_column='typ', limit_choices_to={'nazev_heslare': 40}, on_delete=django.db.models.deletion.RESTRICT, related_name='piany_typu', to='heslar.heslar')),
                ('zm10', models.ForeignKey(db_column='zm10', on_delete=django.db.models.deletion.RESTRICT, related_name='pian_zm10', to='pian.kladyzm')),
                ('zm50', models.ForeignKey(db_column='zm50', on_delete=django.db.models.deletion.RESTRICT, related_name='pian_zm50', to='pian.kladyzm')),
                ('geom_updated_at', models.DateTimeField(blank=True, null=True)),
                ('geom_sjtsk_updated_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'db_table': 'pian',
            },
        ),
        migrations.AddConstraint(
            model_name="pian",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(("geom_system", "5514"), ("geom_sjtsk__isnull", False)),
                    models.Q(("geom_system", "4326"), ("geom__isnull", False)),
                    models.Q(("geom_sjtsk__isnull", True), ("geom__isnull", True)),
                    _connector="OR",
                ),
                name="pian_geom_check",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="piansekvence",
            unique_together={("kladyzm50", "sekvence", "katastr")},
        ),
    ]
