from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone
from uzivatel.managers import CustomUserManager


class AuthUser(AbstractBaseUser, PermissionsMixin):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField(default=False)
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254, unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    # osoba = models.ForeignKey('Osoba', models.DO_NOTHING, db_column='osoba', blank=True, null=True)
    auth_level = models.IntegerField(blank=True, null=True)
    # organizace = models.ForeignKey('Organizace', models.DO_NOTHING, db_column='organizace')
    # historie = models.ForeignKey('HistorieVazby', models.DO_NOTHING, db_column='historie', blank=True, null=True)
    email_potvrzen = models.TextField(blank=True, null=True)
    jazyk = models.CharField(max_length=15, blank=True, null=True)
    sha_1 = models.TextField(blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    class Meta:
        db_table = "auth_user"
