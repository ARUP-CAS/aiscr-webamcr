# Generated by Django 3.2.11 on 2023-02-06 20:20

import core.mixins
import core.validators
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.fields.related
import django.db.models.functions.comparison
import django.utils.timezone
import simple_history.models
import uzivatel.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('historie', '0001_initial'),
        ('heslar', '0002_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128)),
                ('last_login', models.DateTimeField(blank=True, null=True)),
                ('is_superuser', models.BooleanField(default=False, verbose_name='Globální administrátor')),
                ('ident_cely', models.CharField(max_length=150, unique=True)),
                ('first_name', models.CharField(max_length=150, verbose_name='Jméno')),
                ('last_name', models.CharField(max_length=150, verbose_name='Příjmení')),
                ('email', models.CharField(max_length=254, unique=True)),
                ('is_staff', models.BooleanField(default=False, verbose_name='Přístup do admin. rozhraní')),
                ('is_active', models.BooleanField(default=False, verbose_name='Aktivní')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now)),
                ('auth_level', models.IntegerField(blank=True, null=True)),
                ('email_potvrzen', models.TextField(blank=True, null=True)),
                ('jazyk', models.CharField(choices=[('cs', 'Česky'), ('en', 'Anglicky')], default='cs', max_length=15)),
                ('sha_1', models.TextField(blank=True, null=True)),
                ('telefon', models.TextField(blank=True, null=True, validators=[core.validators.validate_phone_number])),
            ],
            options={
                'verbose_name': 'Uživatel',
                'verbose_name_plural': 'Uživatelé',
                'db_table': 'auth_user',
            },
        ),
        migrations.CreateModel(
            name='HistoricalUser',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('password', models.CharField(max_length=128)),
                ('last_login', models.DateTimeField(blank=True, null=True)),
                ('is_superuser', models.BooleanField(default=False, verbose_name='Globální administrátor')),
                ('ident_cely', models.CharField(db_index=True, max_length=150)),
                ('first_name', models.CharField(max_length=150, verbose_name='Jméno')),
                ('last_name', models.CharField(max_length=150, verbose_name='Příjmení')),
                ('email', models.CharField(db_index=True, max_length=254)),
                ('is_staff', models.BooleanField(default=False, verbose_name='Přístup do admin. rozhraní')),
                ('is_active', models.BooleanField(default=False, verbose_name='Aktivní')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now)),
                ('auth_level', models.IntegerField(blank=True, null=True)),
                ('email_potvrzen', models.TextField(blank=True, null=True)),
                ('jazyk', models.CharField(choices=[('cs', 'Česky'), ('en', 'Anglicky')], default='cs', max_length=15)),
                ('sha_1', models.TextField(blank=True, null=True)),
                ('telefon', models.TextField(blank=True, null=True, validators=[core.validators.validate_phone_number])),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
            ],
            options={
                'verbose_name': 'historical Uživatel',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='NotificationsLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.PositiveIntegerField()),
                ('created_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'notifikace_log',
            },
        ),
        migrations.CreateModel(
            name='Organizace',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nazev', models.TextField(verbose_name='uzivatel.models.Organizace.nazev')),
                ('nazev_zkraceny', models.TextField(verbose_name='uzivatel.models.Organizace.nazev_zkraceny')),
                ('oao', models.BooleanField(default=False, verbose_name='uzivatel.models.Organizace.oao')),
                ('mesicu_do_zverejneni', models.IntegerField(default=36, verbose_name='uzivatel.models.Organizace.mesicu_do_zverejneni')),
                ('nazev_zkraceny_en', models.TextField(blank=True, null=True, verbose_name='uzivatel.models.Organizace.nazev_zkraceny_en')),
                ('email', models.TextField(blank=True, null=True, verbose_name='uzivatel.models.Organizace.email')),
                ('telefon', models.TextField(blank=True, null=True, verbose_name='uzivatel.models.Organizace.telefon')),
                ('adresa', models.TextField(blank=True, null=True, verbose_name='uzivatel.models.Organizace.adresa')),
                ('ico', models.TextField(blank=True, null=True, verbose_name='uzivatel.models.Organizace.ico')),
                ('nazev_en', models.TextField(blank=True, null=True, verbose_name='uzivatel.models.Organizace.nazev_en')),
                ('zanikla', models.BooleanField(blank=True, default=None, null=True, verbose_name='uzivatel.models.Organizace.zanikla')),
                ('ident_cely', models.CharField(max_length=10, unique=True)),
            ],
            options={
                'verbose_name': 'Organizace',
                'verbose_name_plural': 'Organizace',
                'db_table': 'organizace',
                'ordering': [django.db.models.functions.comparison.Collate('nazev_zkraceny', 'cs-CZ-x-icu')],
            },
            bases=(models.Model, core.mixins.ManyToManyRestrictedClassMixin),
        ),
        migrations.CreateModel(
            name='Osoba',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('jmeno', models.TextField(verbose_name='uzivatel.models.Osoba.jmeno')),
                ('prijmeni', models.TextField(verbose_name='uzivatel.models.Osoba.prijmeni')),
                ('vypis', models.TextField(verbose_name='uzivatel.models.Osoba.vypis')),
                ('vypis_cely', models.TextField(verbose_name='uzivatel.models.Osoba.vypis_cely')),
                ('rok_narozeni', models.IntegerField(blank=True, null=True, verbose_name='uzivatel.models.Osoba.rok_narozeni')),
                ('rok_umrti', models.IntegerField(blank=True, null=True, verbose_name='uzivatel.models.Osoba.rok_umrti')),
                ('rodne_prijmeni', models.TextField(blank=True, null=True, verbose_name='uzivatel.models.Osoba.rodne_prijmeni')),
                ('ident_cely', models.CharField(max_length=20, unique=True)),
            ],
            options={
                'verbose_name': 'Osoba',
                'verbose_name_plural': 'Osoby',
                'db_table': 'osoba',
                'ordering': ['vypis_cely'],
            },
            bases=(models.Model, core.mixins.ManyToManyRestrictedClassMixin),
        ),
        migrations.CreateModel(
            name='UserNotificationType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ident_cely', models.TextField(unique=True)),
                ('zasilat_neaktivnim', models.BooleanField(default=False)),
                ('predmet', models.TextField()),
                ('cesta_sablony', models.TextField(blank=True)),
            ],
            options={
                'db_table': 'notifikace_typ',
            },
        ),
        migrations.AddConstraint(
            model_name='osoba',
            constraint=models.UniqueConstraint(fields=('jmeno', 'prijmeni'), name='unique jmeno a prijmeni'),
        ),
        migrations.AddField(
            model_name='organizace',
            name='soucast',
            field=models.ForeignKey(blank=True, db_column='soucast', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='uzivatel.organizace'),
        ),
        migrations.AddField(
            model_name='organizace',
            name='typ_organizace',
            field=models.ForeignKey(db_column='typ_organizace', limit_choices_to={'nazev_heslare': 39}, on_delete=django.db.models.deletion.DO_NOTHING, related_name='typy_organizaci', to='heslar.heslar', verbose_name='uzivatel.models.Organizace.typ_organizace'),
        ),
        migrations.AddField(
            model_name='organizace',
            name='zverejneni_pristupnost',
            field=models.ForeignKey(db_column='zverejneni_pristupnost', limit_choices_to={'nazev_heslare': 25}, on_delete=django.db.models.deletion.DO_NOTHING, related_name='organizace_pristupnosti', to='heslar.heslar', verbose_name='uzivatel.models.Organizace.zverejneni_pristupnost'),
        ),
        migrations.AddField(
            model_name='notificationslog',
            name='content_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype'),
        ),
        migrations.AddField(
            model_name='notificationslog',
            name='notification_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='uzivatel.usernotificationtype'),
        ),
        migrations.AddField(
            model_name='historicaluser',
            name='history_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historicaluser',
            name='history_vazba',
            field=models.ForeignKey(blank=True, db_column='historie', db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='historie.historievazby'),
        ),
        migrations.AddField(
            model_name='historicaluser',
            name='organizace',
            field=models.ForeignKey(blank=True, db_column='organizace', db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='uzivatel.organizace'),
        ),
        migrations.AddField(
            model_name='historicaluser',
            name='osoba',
            field=models.ForeignKey(blank=True, db_column='osoba', db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='uzivatel.osoba'),
        ),
        migrations.AddField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups'),
        ),
        migrations.AddField(
            model_name='user',
            name='history_vazba',
            field=models.ForeignKey(db_column='historie', null=True, on_delete=django.db.models.fields.related.ForeignKey, related_name='uzivatelhistorievazba', to='historie.historievazby'),
        ),
        migrations.AddField(
            model_name='user',
            name='notification_types',
            field=models.ManyToManyField(blank=True, db_table='auth_user_notifikace_typ', default=uzivatel.models.only_notification_groups, limit_choices_to={'ident_cely__icontains': 'S-E-'}, related_name='user', to='uzivatel.UserNotificationType'),
        ),
        migrations.AddField(
            model_name='user',
            name='organizace',
            field=models.ForeignKey(db_column='organizace', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='uzivatel.organizace'),
        ),
        migrations.AddField(
            model_name='user',
            name='osoba',
            field=models.ForeignKey(blank=True, db_column='osoba', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='uzivatel.osoba'),
        ),
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions'),
        ),
        migrations.AddIndex(
            model_name='notificationslog',
            index=models.Index(fields=['content_type', 'object_id'], name='notifikace__content_009350_idx'),
        ),
    ]
