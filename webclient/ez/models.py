import logging
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from core.connectors import RedisConnector
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
from django.core.exceptions import ObjectDoesNotExist
from django_prometheus.models import ExportModelOperationsMixin

from xml_generator.models import ModelWithMetadata

logger = logging.getLogger(__name__)


class ExterniZdroj(ExportModelOperationsMixin("externi_zdroj"), ModelWithMetadata):
    """
    Class pro db model externí zdroj.
    """
    STATES = (
        (EZ_STAV_ZAPSANY, _("ez.models.externiZdroj.states.zapsany.label")),
        (EZ_STAV_ODESLANY, _("ez.models.externiZdroj.states.odeslany.label")),
        (EZ_STAV_POTVRZENY, _("ez.models.externiZdroj.states.potvrzeny.label")),
    )

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
    organizace = models.CharField(max_length=255, blank=True, null=True)
    rok_vydani_vzniku = models.TextField(blank=True, null=True)
    paginace_titulu = models.TextField(blank=True, null=True)
    isbn = models.TextField(blank=True, null=True)
    issn = models.TextField(blank=True, null=True)
    link = models.TextField(blank=True, null=True)
    datum_rd = models.DateField(blank=True, null=True)
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
    autori_snapshot = models.CharField(max_length=5000, null=True, blank=True)
    editori_snapshot = models.CharField(max_length=5000, null=True, blank=True)

    class Meta:
        db_table = "externi_zdroj"

    def get_absolute_url(self):
        """
        Metóda pro získaní absolut url záznamu podle identu.
        """
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
        """
        Metóda pro nastavení stavu odeslaný a uložení změny do historie pro externí zdroj.
        """
        self.stav = EZ_STAV_ODESLANY
        historie_poznamka=self.check_set_permanent_ident()
        Historie(
            typ_zmeny=ODESLANI_EXT_ZD,
            uzivatel=user,
            vazba=self.historie,
            poznamka = historie_poznamka,
        ).save()
        self.close_active_transaction_when_finished = True
        self.save()

    def set_vraceny(self, user, new_state, poznamka):
        """
        Metóda pro vrácení o jeden stav méně a uložení změny do historie pro externí zdroj.
        """
        self.stav = new_state
        Historie(
            typ_zmeny=VRACENI_EXT_ZD,
            uzivatel=user,
            poznamka=poznamka,
            vazba=self.historie,
        ).save()
        self.save()

    def set_potvrzeny(self, user):
        """
        Metóda pro nastavení stavu potvrzená a uložení změny do historie pro externí zdroj.
        Pokud je ident dočasný nahrazení identem stálým.
        """
        self.stav = EZ_STAV_POTVRZENY
        historie_poznamka=self.check_set_permanent_ident()
        Historie(
            typ_zmeny=POTVRZENI_EXT_ZD,
            uzivatel=user,
            vazba=self.historie,
            poznamka = historie_poznamka,
        ).save()
        self.save()
        self.close_active_transaction_when_finished = True
        self.save()

    def set_zapsany(self, user):
        """
        Metóda pro nastavení stavu zapsaný a uložení změny do historie pro externí zdroj.
        """
        self.stav = EZ_STAV_ZAPSANY
        Historie(
            typ_zmeny=ZAPSANI_EXT_ZD,
            uzivatel=user,
            vazba=self.historie,
        ).save()
        self.save()

    def get_permission_object(self):
        return self
    
    def get_create_user(self):
        try:
            return (self.historie.historie_set.filter(typ_zmeny=ZAPSANI_EXT_ZD)[0].uzivatel,)
        except Exception as e:
            logger.debug(e)
            return ()

    def get_create_org(self):
        try:
            return (self.get_create_user()[0].organizace,)
        except Exception as e:
            logger.debug(e)
            return ()

    def set_snapshots(self):
        if not self.externizdrojautor_set.all():
            self.autori_snapshot = None
        else:
            self.autori_snapshot = "; ".join([x.autor.vypis_cely
                                          for x in self.externizdrojautor_set.order_by("poradi").all()])
        if not self.externizdrojeditor_set.all():
            self.editori_snapshot = None
        else:
            self.editori_snapshot = "; ".join([x.editor.vypis_cely
                                          for x in self.externizdrojeditor_set.order_by("poradi").all()])

    @property
    def redis_snapshot_id(self):
        from ez.views import ExterniZdrojListView
        return f"{ExterniZdrojListView.redis_snapshot_prefix}_{self.ident_cely}"

    def generate_redis_snapshot(self):
        from ez.tables import ExterniZdrojTable
        data = ExterniZdroj.objects.filter(pk=self.pk)
        table = ExterniZdrojTable(data=data)
        data = RedisConnector.prepare_model_for_redis(table)
        return self.redis_snapshot_id, data
    
    def check_set_permanent_ident(self):
        historie_poznamka = None
        if self.ident_cely.startswith(IDENTIFIKATOR_DOCASNY_PREFIX):
            old_ident = self.ident_cely
            self.ident_cely = get_perm_ez_ident()
            historie_poznamka = f"{old_ident} -> {self.ident_cely}"
            self.save_metadata()
            self.record_ident_change(old_ident)
        return historie_poznamka

def get_perm_ez_ident():
    """
    Funkce pro výpočet ident celý pro externí zdroj.
    Funkce vráti pro permanentní ident id podle sekvence externího zdroje.
    """
    MAXIMUM: int = 9999999
    prefix = "BIB-"
    try:
        sequence = ExterniZdrojSekvence.objects.get(id=1)
        if sequence.sekvence >= MAXIMUM:
            raise MaximalIdentNumberError(MAXIMUM)
        sequence.sekvence += 1
    except ObjectDoesNotExist:
        sequence = ExterniZdrojSekvence.objects.create(sekvence=1)
    finally:
        ezs = ExterniZdroj.objects.filter(ident_cely__startswith=f"{prefix}").order_by("-ident_cely")
        if ezs.filter(ident_cely__startswith=f"{prefix}{sequence.sekvence:07}").count()>0:
            #number from empty spaces
            idents = list(ezs.values_list("ident_cely", flat=True).order_by("ident_cely"))
            idents = [sub.replace(prefix, "") for sub in idents]
            idents = [sub.lstrip("0") for sub in idents]
            idents = [eval(i) for i in idents]
            missing = sorted(set(range(sequence.sekvence, MAXIMUM + 1)).difference(idents))
            logger.debug("arch_z.models.get_akce_ident.missing", extra={"missing": missing[0]})
            logger.debug(missing[0])
            if missing[0] >= MAXIMUM:
                logger.error("arch_z.models.get_akce_ident.maximum_error", extra={"maximum": str(MAXIMUM)})
                raise MaximalIdentNumberError(MAXIMUM)
            sequence.sekvence=missing[0]
    sequence.save()
    return (
        prefix + f"{sequence.sekvence:07}"
    )


class ExterniZdrojAutor(ExportModelOperationsMixin("externi_zdroj_autor"), models.Model):
    """
    Class pro db model autora externího zdroje, zohledňuje pořadí zadání.
    """
    externi_zdroj = models.ForeignKey(
        ExterniZdroj, models.CASCADE, db_column="externi_zdroj")
    autor = models.ForeignKey(Osoba, models.RESTRICT, db_column="autor")
    poradi = models.IntegerField()

    def get_osoba(self):
        return self.autor.vypis_cely

    class Meta:
        db_table = "externi_zdroj_autor"
        unique_together = (("externi_zdroj", "autor"), ("externi_zdroj", "poradi"))


class ExterniZdrojEditor(ExportModelOperationsMixin("externi_zdroj_editor"), models.Model):
    """
    Class pro db model editora externího zdroje, zohledňuje pořadí zadání.
    """
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

class ExterniZdrojSekvence(models.Model):
    """
    Model pro tabulku se sekvencemi externích zdrojů.
    """
    id = models.SmallIntegerField(default=1,primary_key=True)
    sekvence = models.IntegerField()

    class Meta:
        db_table = "externi_zdroj_sekvence"
        constraints = [
            models.CheckConstraint(
                name="constraint_only_one_sekvence",
                check=models.Q(id=1)
            )
        ]
