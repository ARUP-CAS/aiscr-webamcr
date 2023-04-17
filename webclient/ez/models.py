import logging
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext as _
from heslar.hesla import HESLAR_DOKUMENT_TYP, HESLAR_EXTERNI_ZDROJ_TYP
from heslar.models import Heslar
from historie.models import Historie, HistorieVazby
from uzivatel.models import Organizace, Osoba
from core.constants import (
    EZ_STAV_ODESLANY,
    EZ_STAV_POTVRZENY,
    EZ_STAV_ZAPSANY,
    IDENTIFIKATOR_DOCASNY_PREFIX,
    ODESLANI_EXT_ZD,
    POTVRZENI_EXT_ZD,
    VRACENI_EXT_ZD,
    ZAPSANI_EXT_ZD,
)
from core.exceptions import MaximalIdentNumberError

logger = logging.getLogger('python-logstash-logger')


class ExterniZdroj(models.Model):

    STATES = (
        (EZ_STAV_ZAPSANY, _("EZ1 - Zapsána")),
        (EZ_STAV_ODESLANY, _("EZ2 - Odeslána")),
        (EZ_STAV_POTVRZENY, _("EZ3 - Potvrzená")),
    )

    sysno = models.TextField(blank=True, null=True)
    typ = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="typ",
        limit_choices_to={"nazev_heslare": HESLAR_EXTERNI_ZDROJ_TYP},
        related_name="externi_zroje_typu",
    )
    nazev = models.TextField(blank=True, null=True)
    edice_rada = models.TextField(blank=True, null=True)
    sbornik_nazev = models.TextField(blank=True, null=True)
    casopis_denik_nazev = models.TextField(blank=True, null=True)
    casopis_rocnik = models.TextField(blank=True, null=True)
    misto = models.TextField(blank=True, null=True)
    vydavatel = models.TextField(blank=True, null=True)
    typ_dokumentu = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="typ_dokumentu",
        blank=True,
        null=True,
        limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_TYP},
        related_name="externi_zroje_typu_dokumentu",
    )
    organizace = models.ForeignKey(
        Organizace, models.RESTRICT, db_column="organizace", blank=True, null=True
    )
    rok_vydani_vzniku = models.TextField(blank=True, null=True)
    paginace_titulu = models.TextField(blank=True, null=True)
    isbn = models.TextField(blank=True, null=True)
    issn = models.TextField(blank=True, null=True)
    link = models.TextField(blank=True, null=True)
    datum_rd = models.TextField(blank=True, null=True)
    stav = models.SmallIntegerField(choices=STATES)
    poznamka = models.TextField(blank=True, null=True)
    ident_cely = models.TextField(unique=True)

    historie = models.OneToOneField(
        HistorieVazby, on_delete=models.SET_NULL, db_column="historie", blank=True, null=True
    )
    autori = models.ManyToManyField(
        Osoba, through="ExterniZdrojAutor", related_name="ez_autori"
    )
    editori = models.ManyToManyField(
        Osoba,
        through="ExterniZdrojEditor",
        related_name="ez_editori",
        blank=True,
    )

    class Meta:
        db_table = "externi_zdroj"

    def get_absolute_url(self):
        return reverse(
            "ez:detail",
            kwargs={"slug": self.ident_cely},
        )

    def __str__(self):
        if self.ident_cely:
            return self.ident_cely
        else:
            return "[ident_cely not yet assigned]"

    def set_odeslany(self, user):
        self.stav = EZ_STAV_ODESLANY
        Historie(
            typ_zmeny=ODESLANI_EXT_ZD,
            uzivatel=user,
            vazba=self.historie,
        ).save()
        self.save()

    def set_vraceny(self, user, new_state, poznamka):
        self.stav = new_state
        Historie(
            typ_zmeny=VRACENI_EXT_ZD,
            uzivatel=user,
            poznamka=poznamka,
            vazba=self.historie,
        ).save()
        self.save()

    def set_potvrzeny(self, user):
        self.stav = EZ_STAV_POTVRZENY
        if self.ident_cely.startswith(IDENTIFIKATOR_DOCASNY_PREFIX):
            self.ident_cely = get_ez_ident()
        Historie(
            typ_zmeny=POTVRZENI_EXT_ZD,
            uzivatel=user,
            vazba=self.historie,
        ).save()
        self.save()

    def set_zapsany(self, user):
        self.stav = EZ_STAV_ZAPSANY
        Historie(
            typ_zmeny=ZAPSANI_EXT_ZD,
            uzivatel=user,
            vazba=self.historie,
        ).save()
        self.save()


def get_ez_ident(zaznam=None):
    MAXIMAL: int = 9999999
    # [BIB]-[pořadové číslo v sedmimístném formátu]
    prefix = "X-BIB-"
    if zaznam is not None:
        id_number = "{0}".format(str(zaznam.id)).zfill(7)
        return prefix + id_number
    else:
        prefix = "BIB-"
    ez = ExterniZdroj.objects.filter(
        ident_cely__regex="^" + prefix + "\\d{7}$"
    ).order_by("-ident_cely")
    if ez.filter(ident_cely=str(prefix + "0000001")).count() == 0:
        return prefix + "0000001"
    else:
        # temp number from empty spaces
        idents = list(ez.values_list("ident_cely", flat=True).order_by("ident_cely"))
        idents = [sub.replace(prefix, "") for sub in idents]
        idents = [sub.lstrip("0") for sub in idents]
        idents = [eval(i) for i in idents]
        start = idents[0]
        end = MAXIMAL
        missing = sorted(set(range(start, end + 1)).difference(idents))
        logger.debug(missing[0])
        if missing[0] >= MAXIMAL:
            logger.error(
                "Maximal number of temporary document ident is "
                + str(MAXIMAL)
                + "for given region and rada"
            )
            raise MaximalIdentNumberError(MAXIMAL)
        sequence = str(missing[0]).zfill(7)
        return prefix + sequence


class ExterniZdrojAutor(models.Model):
    externi_zdroj = models.ForeignKey(
        ExterniZdroj, models.CASCADE, db_column="externi_zdroj")
    autor = models.ForeignKey(Osoba, models.RESTRICT, db_column="autor")
    poradi = models.IntegerField()

    def get_osoba(self):
        return self.autor.vypis_cely

    class Meta:
        db_table = "externi_zdroj_autor"
        unique_together = (("externi_zdroj", "autor"), ("externi_zdroj", "poradi"))


class ExterniZdrojEditor(models.Model):
    externi_zdroj = models.ForeignKey(
        ExterniZdroj, models.CASCADE, db_column="externi_zdroj"
    )
    editor = models.ForeignKey(Osoba, models.RESTRICT, db_column="editor")
    poradi = models.IntegerField()

    def get_osoba(self):
        return self.editor.vypis_cely

    class Meta:
        db_table = "externi_zdroj_editor"
        unique_together = (
            ("externi_zdroj", "editor"),
            ("poradi", "externi_zdroj"),
        )
