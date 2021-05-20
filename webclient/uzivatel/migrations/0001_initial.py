# Generated by Django 3.1.3 on 2021-05-20 07:24

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('heslar', '0001_initial'),
    ]

    operations = [
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
                ('typ_organizace', models.ForeignKey(db_column='typ_organizace', on_delete=django.db.models.deletion.DO_NOTHING, related_name='typy_organizaci', to='heslar.heslar')),
                ('zverejneni_pristupnost', models.ForeignKey(db_column='zverejneni_pristupnost', on_delete=django.db.models.deletion.DO_NOTHING, related_name='organizace_pristupnosti', to='heslar.heslar')),
            ],
            options={
                'db_table': 'organizace',
                'ordering': ['nazev_zkraceny'],
            },
        ),
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
                ('is_active', models.BooleanField(default=True)),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now)),
                ('auth_level', models.IntegerField(blank=True, null=True)),
                ('email_potvrzen', models.TextField(blank=True, null=True)),
                ('jazyk', models.CharField(blank=True, max_length=15, null=True)),
                ('sha_1', models.TextField(blank=True, null=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('hlavni_role', models.ForeignKey(db_column='hlavni_role', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='uzivatele', to='auth.group')),
                ('organizace', models.ForeignKey(db_column='organizace', on_delete=django.db.models.deletion.DO_NOTHING, to='uzivatel.organizace')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'db_table': 'auth_user',
            },
        ),
    ]
