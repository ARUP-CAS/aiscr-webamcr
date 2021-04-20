from django.contrib.gis.db import models as pgmodels
from django.db import models
from heslar.hesla import (
    HESLAR_DOKUMENT_MATERIAL,
    HESLAR_DOKUMENT_RADA,
    HESLAR_DOKUMENT_TYP,
)


class Heslar(models.Model):
    ident_cely = models.TextField(unique=True, blank=True, null=True)
    nazev_heslare = models.ForeignKey(
        "HeslarNazev", models.DO_NOTHING, db_column="nazev_heslare"
    )
    heslo = models.TextField(blank=True, null=True)
    popis = models.TextField(blank=True, null=True)
    zkratka = models.TextField(blank=True, null=True)
    heslo_en = models.TextField()
    popis_en = models.TextField(blank=True, null=True)
    zkratka_en = models.TextField(blank=True, null=True)
    razeni = models.IntegerField(blank=True, null=True)
    puvodni_id = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = "heslar"
        unique_together = (
            ("nazev_heslare", "zkratka"),
            ("nazev_heslare", "zkratka_en"),
        )
        ordering = ["razeni"]

    def __str__(self):
        if self.heslo:
            return self.heslo
        else:
            return ""


class HeslarDatace(models.Model):
    obdobi = models.OneToOneField(
        Heslar,
        models.DO_NOTHING,
        db_column="obdobi",
        primary_key=True,
        related_name="datace_obdobi",
    )
    rok_od_min = models.IntegerField()
    rok_od_max = models.IntegerField()
    rok_do_min = models.IntegerField()
    rok_do_max = models.IntegerField()
    region = models.OneToOneField(
        Heslar,
        models.DO_NOTHING,
        db_column="region",
        blank=True,
        null=True,
        related_name="datace_region",
    )

    class Meta:
        db_table = "heslar_datace"


class HeslarDokumentTypMaterialRada(models.Model):
    dokument_rada = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="dokument_rada",
        related_name="rada",
        limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_RADA},
    )
    dokument_typ = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="dokument_typ",
        related_name="typ",
        limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_TYP},
    )
    dokument_material = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="dokument_material",
        related_name="material",
        limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_MATERIAL},
    )
    validated = models.SmallIntegerField()

    class Meta:
        db_table = "heslar_dokument_typ_material_rada"
        unique_together = (
            ("dokument_rada", "dokument_typ", "dokument_material"),
            ("dokument_typ", "dokument_material"),
        )


class HeslarHierarchie(models.Model):
    heslo_podrazene = models.OneToOneField(
        Heslar,
        models.DO_NOTHING,
        db_column="heslo_podrazene",
        primary_key=True,
        related_name="hierarchie",
    )
    heslo_nadrazene = models.ForeignKey(
        Heslar, models.DO_NOTHING, db_column="heslo_nadrazene", related_name="nadrazene"
    )
    typ = models.TextField()

    class Meta:
        db_table = "heslar_hierarchie"
        unique_together = (("heslo_podrazene", "heslo_nadrazene", "typ"),)


class HeslarNazev(models.Model):
    nazev = models.TextField(unique=True)
    povolit_zmeny = models.BooleanField(default=True)

    class Meta:
        db_table = "heslar_nazev"


class HeslarOdkaz(models.Model):
    heslo = models.ForeignKey(Heslar, models.DO_NOTHING, db_column="heslo")
    zdroj = models.TextField()
    nazev_kodu = models.TextField()
    kod = models.TextField()
    uri = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "heslar_odkaz"


class RuianKatastr(models.Model):
    okres = models.ForeignKey("RuianOkres", models.DO_NOTHING, db_column="okres")
    aktualni = models.BooleanField()
    nazev = models.TextField()
    kod = models.IntegerField()
    definicni_bod = pgmodels.GeometryField(null=False)
    hranice = pgmodels.GeometryField(null=True)
    nazev_stary = models.TextField(blank=True, null=True)
    poznamka = models.TextField(blank=True, null=True)
    pian = models.IntegerField()  # TODO
    soucasny = models.ForeignKey(
        "self", models.DO_NOTHING, db_column="soucasny", blank=True, null=True
    )

    class Meta:
        db_table = "ruian_katastr"

    def __str__(self):
        return self.nazev


class RuianKraj(models.Model):
    nazev = models.TextField(unique=True)
    kod = models.IntegerField(unique=True)
    rada_id = models.CharField(max_length=1)
    definicni_bod = pgmodels.PointField(blank=True, null=True)
    # hranice = models.TextField(blank=True, null=True)  # This field type is a guess.
    aktualni = models.BooleanField(blank=True, null=True)

    class Meta:
        db_table = "ruian_kraj"

    def __str__(self):
        return self.nazev


class RuianOkres(models.Model):
    nazev = models.TextField()
    kraj = models.ForeignKey(RuianKraj, models.DO_NOTHING, db_column="kraj")
    spz = models.CharField(max_length=3)
    kod = models.IntegerField()
    nazev_en = models.TextField(blank=True, null=True)
    # hranice = models.TextField(blank=True, null=True)  # This field type is a guess.
    # definicni_bod = models.TextField(blank=True, null=True)  # This field type is a guess.
    aktualni = models.BooleanField(blank=True, null=True)

    class Meta:
        db_table = "ruian_okres"

    def __str__(self):
        return self.nazev
