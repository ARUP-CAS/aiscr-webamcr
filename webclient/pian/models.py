import logging

from core.constants import (
    KLADYZM10,
    KLADYZM50,
    KLADYZM_KATEGORIE,
    PIAN_NEPOTVRZEN,
    PIAN_POTVRZEN,
    POTVRZENI_PIAN,
    ZAPSANI_PIAN,
)
from core.coordTransform import transform_geom_to_sjtsk
from core.exceptions import MaximalIdentNumberError
from django.contrib import messages
from django.contrib.gis.db import models as pgmodels
from django.contrib.gis.geos import GEOSGeometry
from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError, models
from django.db.models import CheckConstraint, Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_prometheus.models import ExportModelOperationsMixin
from heslar import hesla_dynamicka
from heslar.hesla import HESLAR_PIAN_PRESNOST, HESLAR_PIAN_TYP
from heslar.hesla_dynamicka import GEOMETRY_PLOCHA, PIAN_PRESNOST_KATASTR, PRISTUPNOST_ANONYM_ID
from heslar.models import Heslar
from historie.models import Historie, HistorieVazby
from uzivatel.models import User
from xml_generator.models import ModelWithMetadata

logger = logging.getLogger(__name__)


class Pian(ExportModelOperationsMixin("pian"), ModelWithMetadata):
    """
    Class pro db model pian.
    """

    STATES = (
        (PIAN_NEPOTVRZEN, _("pian.models.pian.states.nepotvrzen")),
        (PIAN_POTVRZEN, _("pian.models.pian.states.potvrzen")),
    )

    presnost = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="presnost",
        related_name="piany_presnosti",
        limit_choices_to=Q(nazev_heslare=HESLAR_PIAN_PRESNOST) & Q(zkratka__lt="4"),
        db_index=True,
    )
    typ = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="typ",
        related_name="piany_typu",
        limit_choices_to={"nazev_heslare": HESLAR_PIAN_TYP},
        db_index=True,
    )
    geom = pgmodels.GeometryField(null=False, srid=4326, db_index=True)
    geom_sjtsk = pgmodels.GeometryField(blank=True, null=True, srid=5514, db_index=True)
    geom_system = models.CharField(max_length=6, default="5514", db_index=True)
    zm10 = models.ForeignKey(
        "Kladyzm",
        models.RESTRICT,
        db_column="zm10",
        related_name="pian_zm10",
        db_index=True,
    )
    zm50 = models.ForeignKey(
        "Kladyzm",
        models.RESTRICT,
        db_column="zm50",
        related_name="pian_zm50",
        db_index=True,
    )
    ident_cely = models.CharField(unique=True, max_length=16)
    historie = models.OneToOneField(
        HistorieVazby,
        on_delete=models.SET_NULL,
        db_column="historie",
        related_name="pian_historie",
        null=True,
        db_index=True,
    )
    stav = models.SmallIntegerField(choices=STATES, default=PIAN_NEPOTVRZEN, db_index=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_all_azs = True

    @property
    def pristupnost_pom(self):
        try:
            dok_jednotky = self.dokumentacni_jednotky_pianu.all()
            pristupnosti_ids = set()
            for dok_jednotka in dok_jednotky:
                if (
                    dok_jednotka.archeologicky_zaznam is not None
                    and dok_jednotka.archeologicky_zaznam.pristupnost is not None
                ):
                    pristupnosti_ids.add(dok_jednotka.archeologicky_zaznam.pristupnost.id)
            if len(pristupnosti_ids) > 0:
                return Heslar.objects.filter(id__in=list(pristupnosti_ids)).order_by("razeni").first()
        except ValueError as err:
            logger.debug("pian.models.Pian.pristupnost_pom.value_error", extra={"error": err})
        return Heslar.objects.get(pk=PRISTUPNOST_ANONYM_ID)

    @property
    def pristupnost(self):
        return self.pristupnost_pom

    def evaluate_pristupnost_change(self, added_pristupnost_id=None, skip_zaznam_id=None):
        dok_jednotky = self.dokumentacni_jednotky_pianu.all()
        pristupnosti_ids = set()
        for dok_jednotka in dok_jednotky:
            if (
                dok_jednotka.archeologicky_zaznam is not None
                and dok_jednotka.archeologicky_zaznam.pristupnost is not None
                and (skip_zaznam_id is None or skip_zaznam_id != dok_jednotka.archeologicky_zaznam.id)
            ):
                pristupnosti_ids.add(dok_jednotka.archeologicky_zaznam.pristupnost.id)
        if added_pristupnost_id is not None:
            pristupnosti_ids.add(added_pristupnost_id)
        if len(pristupnosti_ids) > 0:
            return Heslar.objects.filter(id__in=list(pristupnosti_ids)).order_by("razeni").first()
        return Heslar.objects.get(pk=PRISTUPNOST_ANONYM_ID)

    class Meta:
        db_table = "pian"
        constraints = [
            CheckConstraint(
                condition=(
                    (Q(geom_system="5514") & Q(geom_sjtsk__isnull=False))
                    | (Q(geom_system="4326") & Q(geom__isnull=False))
                    | (Q(geom_sjtsk__isnull=True) & Q(geom__isnull=True))
                ),
                name="pian_geom_check",
            ),
        ]

    def __str__(self):
        return self.ident_cely + " (" + self.get_stav_display() + ")"

    def get_absolute_url(self, request=None):
        dok_jednotky = self.dokumentacni_jednotky_pianu.all()
        if dok_jednotky:
            for dok_jednotka in dok_jednotky:
                if dok_jednotka.archeologicky_zaznam is not None:
                    return dok_jednotka.get_absolute_url()
        else:
            logger.debug("pian without connection to DJ")
            if request:
                messages.error(request, _("pian.models.Pian.get_absolute_url.noDJ.message.text"))
            return reverse("core:home")

    def get_permission_object(self):
        return self

    def get_create_user(self):
        try:
            my_list = []
            dok_jednotky = self.dokumentacni_jednotky_pianu.all()
            for dok_jednotka in dok_jednotky:
                if dok_jednotka.archeologicky_zaznam is not None:
                    if dok_jednotka.archeologicky_zaznam.get_create_user():
                        my_list.append(dok_jednotka.archeologicky_zaznam.get_create_user()[0])
            if self.historie.historie_set.filter(typ_zmeny=ZAPSANI_PIAN).count() > 0:
                my_list.append(self.historie.historie_set.filter(typ_zmeny=ZAPSANI_PIAN)[0].uzivatel)
            logger.debug(my_list)
            return my_list
        except Exception as e:
            logger.debug(e)
            return ()

    def get_create_org(self):
        try:
            our_list = []
            dok_jednotky = self.dokumentacni_jednotky_pianu.all()
            for dok_jednotka in dok_jednotky:
                if dok_jednotka.archeologicky_zaznam is not None:
                    if dok_jednotka.archeologicky_zaznam.get_create_org():
                        our_list.append(dok_jednotka.archeologicky_zaznam.get_create_org()[0])
                    if dok_jednotka.archeologicky_zaznam.akce.projekt is not None:
                        our_list.append(dok_jednotka.archeologicky_zaznam.akce.projekt.organizace)
            if self.historie.historie_set.filter(typ_zmeny=ZAPSANI_PIAN).count() > 0:
                our_list.append(self.historie.historie_set.filter(typ_zmeny=ZAPSANI_PIAN)[0].uzivatel.organizace)
            logger.debug(our_list)
            return our_list
        except Exception as e:
            logger.debug(e)
            return ()

    def set_permanent_ident_cely(self):
        """
        Metóda pro nastavení permanentního ident celý pro pian.
        Metóda vráti ident podle sekvence pianu.
        """
        katastr = True if self.presnost.zkratka == "4" else False
        maximum: int = 999999 if katastr else 899999
        sequence = PianSekvence.objects.filter(kladyzm50=self.zm50).filter(katastr=katastr)[0]
        if sequence.sekvence < maximum:
            perm_ident_cely = "P-" + str(self.zm50.cislo).replace("-", "").zfill(4) + "-" + f"{sequence.sekvence:06}"
        else:
            raise MaximalIdentNumberError(maximum)
        # Loop through all of the idents that have been imported
        while True:
            if Pian.objects.filter(ident_cely=perm_ident_cely).exists():
                sequence.sekvence += 1
                logger.warning(
                    "Ident " + perm_ident_cely + " already exists, trying next number " + str(sequence.sekvence)
                )
                perm_ident_cely = (
                    "P-" + str(self.zm50.cislo).replace("-", "").zfill(4) + "-" + f"{sequence.sekvence:06}"
                )
            else:
                break
        old_ident = self.ident_cely
        self.ident_cely = perm_ident_cely
        sequence.sekvence += 1
        sequence.save(using="urgent")
        self.save()
        self.record_ident_change(old_ident, fedora_transaction=self.active_transaction)

    def set_vymezeny(self, user):
        """
        Metóda pro nastavení stavu vymezený.
        """
        self.stav = PIAN_NEPOTVRZEN
        self.zaznamenej_zapsani(user)

    def set_potvrzeny(self, user, old_ident):
        """
        Metóda pro nastavení stavu potvrzený.
        """
        self.stav = PIAN_POTVRZEN
        Historie(
            typ_zmeny=POTVRZENI_PIAN, uzivatel=user, vazba=self.historie, poznamka=f"{old_ident} -> {self.ident_cely}"
        ).save()
        self.save()

    def zaznamenej_zapsani(self, user):
        """
        Metóda pro uložení změny do historie pro pianu.
        """
        Historie(typ_zmeny=ZAPSANI_PIAN, uzivatel=user, vazba=self.historie).save()
        self.save()


class Kladyzm(ExportModelOperationsMixin("klady_zm"), models.Model):
    """
    Class pro db model klady zm.
    """

    gid = models.AutoField(primary_key=True)
    kategorie = models.IntegerField(choices=KLADYZM_KATEGORIE)
    cislo = models.CharField(unique=True, max_length=8)
    the_geom = pgmodels.PolygonField(srid=5514)

    class Meta:
        db_table = "kladyzm"


class PianSekvence(ExportModelOperationsMixin("pian_sekvence"), models.Model):
    """
    Class pro db model sekvence pianu podle klady zm 50 a katastru.
    """

    kladyzm50 = models.ForeignKey(
        "Kladyzm",
        models.RESTRICT,
        db_column="kladyzm_id",
        null=False,
    )
    sekvence = models.IntegerField()
    katastr = models.BooleanField()

    class Meta:
        db_table = "pian_sekvence"
        constraints = [
            models.UniqueConstraint(fields=["kladyzm50", "katastr"], name="unique_sekvence_pian"),
        ]


def vytvor_pian(katastr, fedora_transaction):
    """
    Funkce pro vytvoření pianu v DB podle katastru.
    """
    zm10, zm50 = get_ZM_from_point(katastr.definicni_bod)
    if zm10 is None:
        logger.error("dj.signals.create_dokumentacni_jednotka.zm10s.not_found")
        raise Exception("zm10s.not_found")
    if zm50 is None:
        logger.error("dj.signals.create_dokumentacni_jednotka.zm50s.not_found")
        raise Exception("zm50s.not_found")
    try:
        geom = katastr.hranice
        geom_jtsk, res = transform_geom_to_sjtsk(str(geom).split(";")[1])
        presnost = Heslar.objects.get(pk=PIAN_PRESNOST_KATASTR)
        typ = Heslar.objects.get(pk=GEOMETRY_PLOCHA)
        pian = Pian(
            stav=PIAN_POTVRZEN,
            zm10=zm10,
            zm50=zm50,
            typ=typ,
            presnost=presnost,
            geom=geom,
            geom_sjtsk=GEOSGeometry(geom_jtsk),
            geom_system="4326",
        )
        pian.active_transaction = fedora_transaction
        pian.set_permanent_ident_cely()
        pian.save()
        pian.zaznamenej_zapsani(User.objects.filter(pk=hesla_dynamicka.ADMIN_USER).first())
        katastr.pian = pian
        katastr.save()
        return pian
    except ObjectDoesNotExist as err:
        logger.error("dj.signals.create_dokumentacni_jednotka.ObjectDoesNotExist", extra={"error": err})
        raise ObjectDoesNotExist()


def get_ZM_from_point(point):
    try:
        zm10s = list(Kladyzm.objects.filter(kategorie=KLADYZM10).filter(the_geom__contains=point))
        zm50s = list(Kladyzm.objects.filter(kategorie=KLADYZM50).filter(the_geom__contains=point))
    except DatabaseError as e:
        zm10s = Kladyzm.objects.none()
        zm50s = Kladyzm.objects.none()
        logger.warning("pian.models.get_ZM_from_point.Kladyzm.warning", extra={"error": e, "geom": str(point)})
    if len(zm10s) == 1 and len(zm50s) == 1:
        return zm10s[0], zm50s[0]
    return None, None
