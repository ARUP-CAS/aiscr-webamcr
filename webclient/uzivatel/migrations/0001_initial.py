# Generated by Django 3.1.3 on 2021-10-15 09:50

import core.validators
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import simple_history.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('heslar', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128)),
                ('last_login', models.DateTimeField(blank=True, null=True)),
                ('is_superuser', models.BooleanField(default=False)),
                ('ident_cely', models.CharField(max_length=150, unique=True)),
                ('first_name', models.CharField(max_length=150)),
                ('last_name', models.CharField(max_length=150)),
                ('email', models.CharField(max_length=254, unique=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=False)),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now)),
                ('auth_level', models.IntegerField(blank=True, null=True)),
                ('email_potvrzen', models.TextField(blank=True, null=True)),
                ('jazyk', models.CharField(choices=[('cs', 'Česky'), ('en', 'Anglicky')], default='cs', max_length=15)),
                ('sha_1', models.TextField(blank=True, null=True)),
                ('telefon', models.TextField(blank=True, null=True, validators=[core.validators.validate_phone_number])),
            ],
            options={
                'db_table': 'auth_user',
            },
        ),
        migrations.CreateModel(
            name='HistoricalUser',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('password', models.CharField(max_length=128)),
                ('last_login', models.DateTimeField(blank=True, null=True)),
                ('is_superuser', models.BooleanField(default=False)),
                ('ident_cely', models.CharField(db_index=True, max_length=150)),
                ('first_name', models.CharField(max_length=150)),
                ('last_name', models.CharField(max_length=150)),
                ('email', models.CharField(db_index=True, max_length=254)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=False)),
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
                'verbose_name': 'historical user',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='Organizace',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nazev', models.TextField()),
                ('nazev_zkraceny', models.TextField()),
                ('oao', models.BooleanField(default=False)),
                ('mesicu_do_zverejneni', models.IntegerField(default=36)),
                ('nazev_zkraceny_en', models.TextField(blank=True, null=True)),
                ('email', models.TextField(blank=True, null=True)),
                ('telefon', models.TextField(blank=True, null=True)),
                ('adresa', models.TextField(blank=True, null=True)),
                ('ico', models.TextField(blank=True, null=True)),
                ('nazev_en', models.TextField(blank=True, null=True)),
                ('zanikla', models.BooleanField(blank=True, null=True)),
            ],
            options={
                'db_table': 'organizace',
                'ordering': ['nazev_zkraceny'],
            },
        ),
        migrations.CreateModel(
            name='Osoba',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('jmeno', models.TextField()),
                ('prijmeni', models.TextField()),
                ('vypis', models.TextField()),
                ('vypis_cely', models.TextField()),
                ('rok_narozeni', models.IntegerField(blank=True, null=True)),
                ('rok_umrti', models.IntegerField(blank=True, null=True)),
                ('rodne_prijmeni', models.TextField(blank=True, null=True)),
            ],
            options={
                'db_table': 'osoba',
                'ordering': ['vypis_cely'],
            },
        ),
        migrations.AddConstraint(
            model_name='osoba',
            constraint=models.UniqueConstraint(fields=('jmeno', 'prijmeni'), name='unique jmeno a prijmeni'),
        ),
        migrations.AddField(
            model_name='organizace',
            name='typ_organizace',
            field=models.ForeignKey(db_column='typ_organizace', on_delete=django.db.models.deletion.DO_NOTHING, related_name='typy_organizaci', to='heslar.heslar'),
        ),
        migrations.AddField(
            model_name='organizace',
            name='zverejneni_pristupnost',
            field=models.ForeignKey(db_column='zverejneni_pristupnost', on_delete=django.db.models.deletion.DO_NOTHING, related_name='organizace_pristupnosti', to='heslar.heslar'),
        ),
        migrations.AddField(
            model_name='historicaluser',
            name='history_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historicaluser',
            name='hlavni_role',
            field=models.ForeignKey(blank=True, db_column='hlavni_role', db_constraint=False, default=5, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='auth.group'),
        ),
        migrations.AddField(
            model_name='historicaluser',
            name='organizace',
            field=models.ForeignKey(blank=True, db_column='organizace', db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='uzivatel.organizace'),
        ),
        migrations.AddField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups'),
        ),
        migrations.AddField(
            model_name='user',
            name='hlavni_role',
            field=models.ForeignKey(db_column='hlavni_role', default=5, on_delete=django.db.models.deletion.DO_NOTHING, related_name='uzivatele', to='auth.group'),
        ),
        migrations.AddField(
            model_name='user',
            name='organizace',
            field=models.ForeignKey(db_column='organizace', on_delete=django.db.models.deletion.DO_NOTHING, to='uzivatel.organizace'),
        ),
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions'),
        ),
    ]
