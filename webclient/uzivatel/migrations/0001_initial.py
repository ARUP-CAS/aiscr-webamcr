# Generated by Django 3.2.11 on 2023-02-14 19:39

import core.mixins
import core.validators
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.fields.related
import django.db.models.functions.comparison
import django.utils.timezone
import uzivatel.models
import django.core.validators

from core.constants import ORGANIZACE_MESICU_DO_ZVEREJNENI_MAX


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('historie', '0001_initial'),
        ('heslar', '0002_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
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
                ('jazyk', models.CharField(choices=[('cs', 'Česky'), ('en', 'Anglicky')], default='cs', max_length=15)),
                ('sha_1', models.TextField(blank=True, null=True)),
                ('telefon', models.CharField(max_length=100, blank=True, null=True, validators=[core.validators.validate_phone_number])),
            ],
            options={
                'verbose_name': 'Uživatel',
                'verbose_name_plural': 'Uživatelé',
                'db_table': 'auth_user',
            },
        ),
        migrations.CreateModel(
            name='NotificationsLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('receiver_address', models.CharField(max_length=254)),
            ],
            options={
                'db_table': 'notifikace_log',
            },
        ),
        migrations.CreateModel(
            name='Organizace',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nazev', models.CharField(max_length=255, verbose_name='uzivatel.models.Organizace.nazev')),
                ('nazev_zkraceny', models.CharField(max_length=255, verbose_name='uzivatel.models.Organizace.nazev_zkraceny', unique=True)),
                ('oao', models.BooleanField(default=False, verbose_name='uzivatel.models.Organizace.oao')),
                ('mesicu_do_zverejneni', models.PositiveIntegerField(default=36, validators=[django.core.validators.MaxValueValidator(1200)], verbose_name='uzivatel.models.Organizace.mesicu_do_zverejneni')),
                ('nazev_zkraceny_en', models.CharField(max_length=255, verbose_name='uzivatel.models.Organizace.nazev_zkraceny_en')),
                ('email', models.CharField(blank=True, max_length=100, null=True, verbose_name='uzivatel.models.Organizace.email')),
                ('telefon', models.CharField(blank=True, max_length=100, null=True, verbose_name='uzivatel.models.Organizace.telefon')),
                ('adresa', models.CharField(blank=True, max_length=255, null=True, verbose_name='uzivatel.models.Organizace.adresa')),
                ('ico', models.CharField(blank=True, max_length=100, null=True, verbose_name='uzivatel.models.Organizace.ico')),
                ('nazev_en', models.CharField(blank=True, max_length=255, null=True, verbose_name='uzivatel.models.Organizace.nazev_en')),
                ('zanikla', models.BooleanField(default=False, verbose_name='uzivatel.models.Organizace.zanikla')),
                ('ident_cely', models.CharField(max_length=20, unique=True)),
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
                ('jmeno', models.CharField(max_length=100, verbose_name='uzivatel.models.Osoba.jmeno')),
                ('prijmeni', models.CharField(max_length=100, verbose_name='uzivatel.models.Osoba.prijmeni')),
                ('vypis', models.CharField(max_length=200, verbose_name='uzivatel.models.Osoba.vypis')),
                ('vypis_cely', models.CharField(max_length=200, verbose_name='uzivatel.models.Osoba.vypis_cely')),
                ('rok_narozeni', models.IntegerField(blank=True, null=True, verbose_name='uzivatel.models.Osoba.rok_narozeni')),
                ('rok_umrti', models.IntegerField(blank=True, null=True, verbose_name='uzivatel.models.Osoba.rok_umrti')),
                ('rodne_prijmeni', models.CharField(blank=True, max_length=100, null=True, verbose_name='uzivatel.models.Osoba.rodne_prijmeni')),
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
            ],
            options={
                'db_table': 'notifikace_typ',
            },
        ),
        migrations.AddConstraint(
            model_name='osoba',
            constraint=models.UniqueConstraint(fields=('jmeno', 'prijmeni'), name='osoba_jmeno_prijmeni_key'),
        ),
        migrations.AddField(
            model_name='organizace',
            name='soucast',
            field=models.ForeignKey(blank=True, db_column='soucast', null=True, on_delete=django.db.models.deletion.RESTRICT, to='uzivatel.organizace'),
        ),
        migrations.AddField(
            model_name='organizace',
            name='typ_organizace',
            field=models.ForeignKey(db_column='typ_organizace', limit_choices_to={'nazev_heslare': 39}, on_delete=django.db.models.deletion.RESTRICT, related_name='typy_organizaci', to='heslar.heslar', verbose_name='uzivatel.models.Organizace.typ_organizace'),
        ),
        migrations.AddField(
            model_name='organizace',
            name='zverejneni_pristupnost',
            field=models.ForeignKey(db_column='zverejneni_pristupnost', limit_choices_to={'nazev_heslare': 25}, on_delete=django.db.models.deletion.RESTRICT, related_name='organizace_pristupnosti', to='heslar.heslar', verbose_name='uzivatel.models.Organizace.zverejneni_pristupnost'),
        ),
        migrations.AddField(
            model_name='notificationslog',
            name='notification_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='uzivatel.usernotificationtype'),
        ),
        migrations.AddField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups'),
        ),
        migrations.AddField(
            model_name='user',
            name='history_vazba',
            field=models.OneToOneField(db_column='historie', null=True, on_delete=django.db.models.fields.related.ForeignKey, related_name='uzivatelhistorievazba', to='historie.historievazby'),
        ),
        migrations.AddField(
            model_name='user',
            name='notification_types',
            field=models.ManyToManyField(blank=True, db_table='auth_user_notifikace_typ', default=uzivatel.models.only_notification_groups, limit_choices_to={'ident_cely__icontains': 'S-E-'}, related_name='user', to='uzivatel.UserNotificationType'),
        ),
        migrations.AddField(
            model_name='user',
            name='organizace',
            field=models.ForeignKey(db_column='organizace', on_delete=django.db.models.deletion.RESTRICT, to='uzivatel.organizace'),
        ),
        migrations.AddField(
            model_name='user',
            name='osoba',
            field=models.ForeignKey(blank=True, db_column='osoba', null=True, on_delete=django.db.models.deletion.RESTRICT, to='uzivatel.osoba'),
        ),
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions'),
        ),
        migrations.AddConstraint(
            model_name="organizace",
            constraint=models.CheckConstraint(
                check=models.Q(("mesicu_do_zverejneni__lte", ORGANIZACE_MESICU_DO_ZVEREJNENI_MAX)),
                name="organizace_mesicu_do_zverejneni_max_value_check",
            ),
        ),
        migrations.AddField(
            model_name="notificationslog",
            name="user",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
            ),
        )
    ]
