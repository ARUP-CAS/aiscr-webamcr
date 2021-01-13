from django.db import models
from uzivatel.models import AuthUser


class Historie(models.Model):
    datum_zmeny = models.DateTimeField()
    typ_zmeny = models.IntegerField()
    uzivatel = models.ForeignKey(
        AuthUser, on_delete=models.CASCADE, db_column="uzivatel"
    )
    poznamka = models.TextField(blank=True, null=True)
    vazba = models.ForeignKey(
        "HistorieVazby", on_delete=models.CASCADE, db_column="vazba"
    )

    class Meta:
        db_table = "historie"


class HistorieVazby(models.Model):
    typ_vazby = models.TextField()

    class Meta:
        db_table = "historie_vazby"
