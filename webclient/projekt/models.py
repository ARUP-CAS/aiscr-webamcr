import datetime
import logging
import os
import zlib

from django.contrib.gis.db import models as pgmodels
from django.contrib.postgres.fields import DateRangeField
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.db import models
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext as _

from core.constants import (
    ARCHIVACE_PROJ,
    AZ_STAV_ARCHIVOVANY,
    NAVRZENI_KE_ZRUSENI_PROJ,
    OZNAMENI_PROJ,
    PRIHLASENI_PROJ,
    PROJEKT_STAV_ARCHIVOVANY,
    PROJEKT_STAV_NAVRZEN_KE_ZRUSENI,
    PROJEKT_STAV_OZNAMENY,
    PROJEKT_STAV_PRIHLASENY,
    PROJEKT_STAV_UKONCENY_V_TERENU,
    PROJEKT_STAV_UZAVRENY,
    PROJEKT_STAV_ZAHAJENY_V_TERENU,
    PROJEKT_STAV_ZAPSANY,
    PROJEKT_STAV_ZRUSENY,
    PROJEKT_STAV_VYTVORENY,
    RUSENI_PROJ,
    SCHVALENI_OZNAMENI_PROJ,
    UKONCENI_V_TERENU_PROJ,
    UZAVRENI_PROJ,
    VRACENI_NAVRHU_ZRUSENI,
    VRACENI_PROJ,
    ZAHAJENI_V_TERENU_PROJ,
    ZAPSANI_PROJ,
    VRACENI_ZRUSENI,
)
from core.exceptions import MaximalIdentNumberError
from core.models import ProjektSekvence, Soubor, SouborVazby
from heslar.hesla import (
    HESLAR_PAMATKOVA_OCHRANA,
    HESLAR_PROJEKT_TYP,
    TYP_PROJEKTU_PRUZKUM_ID,
    TYP_PROJEKTU_ZACHRANNY_ID,
)
from heslar.models import Heslar, RuianKatastr
from historie.models import Historie, HistorieVazby
from projekt.doc_utils import OznameniPDFCreator
from projekt.rtf_utils import ExpertniListCreator
from uzivatel.models import Organizace, Osoba, User

logger = logging.getLogger(__name__)


class Projekt(models.Model):
    CHOICES = (
        (PROJEKT_STAV_OZNAMENY, "P0 - Oznámen"),
        (PROJEKT_STAV_ZAPSANY, "P1 - Zapsán"),
        (PROJEKT_STAV_PRIHLASENY, "P2 - Přihlášen"),
        (PROJEKT_STAV_ZAHAJENY_V_TERENU, "P3 - Zahájen v terénu"),
        (PROJEKT_STAV_UKONCENY_V_TERENU, "P4 - Ukončen v terénu"),
        (PROJEKT_STAV_UZAVRENY, "P5 - Uzavřen"),
        (PROJEKT_STAV_ARCHIVOVANY, "P6 - Archivován"),
        (PROJEKT_STAV_NAVRZEN_KE_ZRUSENI, "P7 - Navržen ke zrušení"),
        (PROJEKT_STAV_ZRUSENY, "P8 - Zrušen"),
    )

    stav = models.SmallIntegerField(
        choices=CHOICES, default=PROJEKT_STAV_OZNAMENY, verbose_name=_("Stav")
    )
    typ_projektu = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="typ_projektu",
        related_name="projekty_typu",
        limit_choices_to={"nazev_heslare": HESLAR_PROJEKT_TYP},
        verbose_name=_("Typ projektů"),
    )
    lokalizace = models.TextField(blank=True, null=True)
    kulturni_pamatka_cislo = models.TextField(blank=True, null=True)
    kulturni_pamatka_popis = models.TextField(blank=True, null=True)
    parcelni_cislo = models.TextField(blank=True, null=True)
    podnet = models.TextField(blank=True, null=True, verbose_name=_("Podnět"))
    uzivatelske_oznaceni = models.TextField(
        blank=True, null=True, verbose_name=_("Uživatelské označení")
    )
    vedouci_projektu = models.ForeignKey(
        Osoba,
        models.RESTRICT,
        db_column="vedouci_projektu",
        blank=True,
        null=True,
        verbose_name=_("Vedoucí projektů"),
    )
    datum_zahajeni = models.DateField(
        blank=True, null=True, verbose_name=_("Datum zahájení")
    )
    datum_ukonceni = models.DateField(
        blank=True, null=True, verbose_name=_("Datum ukončení")
    )
    kulturni_pamatka = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="kulturni_pamatka",
        blank=True,
        null=True,
        limit_choices_to={"nazev_heslare": HESLAR_PAMATKOVA_OCHRANA},
        verbose_name=_("Památka"),
    )
    termin_odevzdani_nz = models.DateField(blank=True, null=True)
    ident_cely = models.TextField(
        unique=True, verbose_name=_("Identifikátor")
    )
    geom = pgmodels.PointField(blank=True, null=True, srid=4326)
    soubory = models.OneToOneField(
        SouborVazby,
        on_delete=models.DO_NOTHING,
        db_column="soubory",
        blank=True,
        null=True,
        related_name="projekt_souboru",
    )
    historie = models.OneToOneField(
        HistorieVazby,
        on_delete=models.DO_NOTHING,
        db_column="historie",
        related_name="projekt_historie",
    )
    organizace = models.ForeignKey(
        Organizace, models.DO_NOTHING, db_column="organizace", blank=True, null=True
    )
    oznaceni_stavby = models.TextField(
        blank=True, null=True, verbose_name=_("Označení stavby")
    )
    planovane_zahajeni = DateRangeField(
        blank=True, null=True, verbose_name=_("Plánované zahájení")
    )
    katastry = models.ManyToManyField(RuianKatastr, through="ProjektKatastr")
    hlavni_katastr = models.ForeignKey(
        RuianKatastr,
        on_delete=models.DO_NOTHING,
        db_column="hlavni_katastr",
        related_name="projekty_hlavnich_katastru",
        verbose_name=_("Hlavní katastr"),
    )

    def __str__(self):
        if self.ident_cely:
            return self.ident_cely
        else:
            return "[ident_cely not yet assigned]"

    class Meta:
        db_table = "projekt"
        verbose_name = "projekty"

    def set_vytvoreny(self):
        self.stav = PROJEKT_STAV_VYTVORENY
        self.save()

    def set_oznameny(self):
        self.stav = PROJEKT_STAV_OZNAMENY
        owner = get_object_or_404(User, email="amcr@arup.cas.cz")
        Historie(
            typ_zmeny=OZNAMENI_PROJ,
            uzivatel=owner,
            vazba=self.historie,
        ).save()
        self.save()

    def set_schvaleny(self, user):
        self.stav = PROJEKT_STAV_ZAPSANY
        Historie(
            typ_zmeny=SCHVALENI_OZNAMENI_PROJ,
            uzivatel=user,
            vazba=self.historie,
        ).save()
        self.save()

    def set_zapsany(self, user):
        self.stav = PROJEKT_STAV_ZAPSANY
        Historie(typ_zmeny=ZAPSANI_PROJ, uzivatel=user, vazba=self.historie).save()
        self.save()
        if self.typ_projektu == TYP_PROJEKTU_ZACHRANNY_ID:
            self.create_confirmation_document(user)

    def set_prihlaseny(self, user):
        self.stav = PROJEKT_STAV_PRIHLASENY
        Historie(
            typ_zmeny=PRIHLASENI_PROJ,
            uzivatel=user,
            vazba=self.historie,
        ).save()
        self.save()

    def set_zahajeny_v_terenu(self, user):
        self.stav = PROJEKT_STAV_ZAHAJENY_V_TERENU
        Historie(
            typ_zmeny=ZAHAJENI_V_TERENU_PROJ,
            uzivatel=user,
            vazba=self.historie,
        ).save()
        self.save()

    def set_ukoncen_v_terenu(self, user):
        self.stav = PROJEKT_STAV_UKONCENY_V_TERENU
        Historie(
            typ_zmeny=UKONCENI_V_TERENU_PROJ,
            uzivatel=user,
            vazba=self.historie,
        ).save()
        self.save()

    def set_uzavreny(self, user):
        self.stav = PROJEKT_STAV_UZAVRENY
        Historie(
            typ_zmeny=UZAVRENI_PROJ,
            uzivatel=user,
            vazba=self.historie,
        ).save()
        self.save()

    def set_archivovany(self, user):
        from services.mailer import Mailer
        if self.typ_projektu.id == TYP_PROJEKTU_ZACHRANNY_ID:
            # Removing personal information from the projekt announcement
            if self.has_oznamovatel():
                self.oznamovatel.delete()
            # making txt file with deleted files
            today = datetime.datetime.now()
            soubory = self.soubory.soubory.exclude(
                nazev_zkraceny__regex="^log_dokumentace_"
            )
            logger.debug(soubory)
            if soubory.count() > 0:
                filename = (
                        "log_dokumentace_" + today.strftime("%Y-%m-%d-%H-%M") + ".txt"
                )
                ("soubory/APD/" + filename, "w+")
                file_content = (
                        "Z důvodu ochrany osobních údajů byly dne %s automaticky odstraněny následující soubory z projektové dokumentace:\n"
                        % today.strftime("%d. %m. %Y")
                )
                file_content += "\n".join(soubory.values_list("nazev_zkraceny", flat=True))
                prev = 0
                prev = zlib.crc32(bytes(file_content, "utf-8"), prev)
                new_filename = "%d_%s" % (prev & 0xFFFFFFFF, filename)
                myfile = ContentFile(content=file_content, name=new_filename)
                aktual_soubor = Soubor(
                    vazba=self.soubory,
                    nazev=new_filename,
                    nazev_zkraceny=filename,
                    nazev_puvodni=filename,
                    vlastnik=get_object_or_404(User, email="amcr@arup.cas.cz"),
                    mimetype="text/plain",
                    size_mb=myfile.size/1024/1024,
                )
                aktual_soubor.save()
                aktual_soubor.path.save(name=new_filename, content=myfile)
                aktual_soubor.zaznamenej_nahrani(user=user)
                for file in soubory:
                    file.path.delete()
                items_deleted = soubory.delete()
                logger.debug(
                    "Pocet smazanych souboru soubory: " + str(items_deleted[0])
                )

        self.stav = PROJEKT_STAV_ARCHIVOVANY
        Historie(typ_zmeny=ARCHIVACE_PROJ, uzivatel=user, vazba=self.historie).save()
        Mailer.send_ea01(project=self, user=user)
        self.save()

    def set_navrzen_ke_zruseni(self, user, poznamka):
        self.stav = PROJEKT_STAV_NAVRZEN_KE_ZRUSENI
        Historie(
            typ_zmeny=NAVRZENI_KE_ZRUSENI_PROJ,
            uzivatel=user,
            poznamka=poznamka,
            vazba=self.historie,
        ).save()
        self.save()

    def set_zruseny(self, user, poznamka):
        self.datum_ukonceni = None
        self.termin_odevzdani_nz = None
        self.datum_zahajeni = None
        self.vedouci_projektu = None
        self.uzivatelske_oznaceni = None
        self.organizace = None
        self.stav = PROJEKT_STAV_ZRUSENY
        Historie(
            typ_zmeny=RUSENI_PROJ, uzivatel=user, vazba=self.historie, poznamka=poznamka
        ).save()
        self.save()

    def set_vracen(self, user, new_state, poznamka):
        if self.stav == PROJEKT_STAV_UKONCENY_V_TERENU:
            self.datum_ukonceni = None
            self.termin_odevzdani_nz = None
        elif self.stav == PROJEKT_STAV_ZAHAJENY_V_TERENU:
            self.datum_zahajeni = None
        elif self.stav == PROJEKT_STAV_PRIHLASENY:
            self.vedouci_projektu = None
            self.uzivatelske_oznaceni = None
            self.organizace = None
        self.stav = new_state
        Historie(
            typ_zmeny=VRACENI_PROJ,
            uzivatel=user,
            poznamka=poznamka,
            vazba=self.historie,
        ).save()
        self.save()

    def set_znovu_zapsan(self, user, poznamka):
        if self.stav == PROJEKT_STAV_NAVRZEN_KE_ZRUSENI:
            zmena = VRACENI_NAVRHU_ZRUSENI
            self.datum_ukonceni = None
            self.termin_odevzdani_nz = None
            self.datum_zahajeni = None
            self.vedouci_projektu = None
            self.uzivatelske_oznaceni = None
            self.organizace = None
        else:
            zmena = VRACENI_ZRUSENI
        self.stav = PROJEKT_STAV_ZAPSANY

        Historie(
            typ_zmeny=zmena,
            uzivatel=user,
            poznamka=poznamka,
            vazba=self.historie,
        ).save()
        self.save()

    def check_pred_archivaci(self):
        result = {}
        for akce in self.akce_set.all():
            if akce.archeologicky_zaznam.stav != AZ_STAV_ARCHIVOVANY:
                result[akce.archeologicky_zaznam.ident_cely] = _(
                    "Akce musí být archivovaná!"
                )
        return result

    def check_pred_navrzeni_k_zruseni(self):
        has_event = len(self.akce_set.all()) > 0
        if has_event:
            return {"has_event": _("Projekt před zrušením nesmí mít projektové akce.")}
        else:
            return {}

    def check_pred_smazanim(self):
        resp = []
        has_event = len(self.akce_set.all()) > 0
        has_individual_finds = len(self.samostatne_nalezy.all()) > 0
        has_soubory = self.soubory.soubory.all()
        if has_event:
            resp.append(_("Projekt před smazáním nesmí mít projektové akce."))
        if has_individual_finds:
            resp.append(_("Projekt před smazáním nesmí mít samostatné nálezy."))
        if has_soubory:
            resp.append(_("Projekt má projektovou dokumentaci."))
        return resp

    def check_pred_uzavrenim(self):
        does_not_have_event = len(self.akce_set.all()) == 0
        result = {}
        if does_not_have_event and self.typ_projektu.id != TYP_PROJEKTU_PRUZKUM_ID:
            result["has_event"] = _("Projekt musí mít alespoň jednu projektovou akci.")
        for a in self.akce_set.all():
            if hasattr(a, "check_pred_odeslanim"):
                akce_warnings = a.check_pred_odeslanim()
                if akce_warnings:
                    result[_("Akce ") + a.archeologicky_zaznam.ident_cely] = akce_warnings
        return result

    def parse_ident_cely(self):
        year = None
        number = None
        region = None
        permanent = None
        if self.ident_cely:
            last_dash_index = self.ident_cely.rfind("-")
            region = self.ident_cely[last_dash_index - 1: last_dash_index]
            last_part = self.ident_cely[last_dash_index + 1:]
            year = last_part[:4]
            number = last_part[4:]
            permanent = False if "X-" in self.ident_cely else True
        else:
            logger.warning("Cannot retrieve year from null ident_cely.")
        return permanent, region, year, number

    def has_oznamovatel(self):
        has_oznamovatel = False
        try:
            has_oznamovatel = self.oznamovatel is not None
        except ObjectDoesNotExist:
            pass
        return has_oznamovatel

    def set_permanent_ident_cely(self):
        MAXIMUM: int = 99999
        current_year = datetime.datetime.now().year
        region = self.hlavni_katastr.okres.kraj.rada_id
        logger.debug(
            "Region " + region + " of the cadastry: " + str(self.hlavni_katastr)
        )
        sequence = ProjektSekvence.objects.filter(rada=region).filter(rok=current_year)[
            0
        ]
        perm_ident_cely = (
                region + "-" + str(current_year) + "{0}".format(sequence.sekvence).zfill(5)
        )
        # Loop through all of the idents that have been imported
        while True:
            if Projekt.objects.filter(ident_cely=perm_ident_cely).exists():
                sequence.sekvence += 1
                logger.warning(
                    "Ident "
                    + perm_ident_cely
                    + " already exists, trying next number "
                    + str(sequence.sekvence)
                )
                perm_ident_cely = (
                        region
                        + "-"
                        + str(current_year)
                        + "{0}".format(sequence.sekvence).zfill(5)
                )
            else:
                break
        if sequence.sekvence >= MAXIMUM:
            raise MaximalIdentNumberError(MAXIMUM)
        self.ident_cely = perm_ident_cely
        sequence.sekvence += 1
        sequence.save()
        self.save()

    def create_confirmation_document(self, additional=False, user=None):
        from core.utils import get_mime_type
        creator = OznameniPDFCreator(self.oznamovatel, self, additional)
        filename, filename_without_checksum = creator.build_document()
        filename_without_path = os.path.basename(filename)
        duplikat = Soubor.objects.filter(nazev=filename)
        if not duplikat.exists():
            soubor = Soubor(
                path=filename,
                vazba=self.soubory,
                nazev=filename_without_path,
                nazev_zkraceny=filename_without_checksum,
                nazev_puvodni=filename_without_path,
                mimetype=get_mime_type(filename_without_path),
                size_mb=os.path.getsize(filename)/1024/1024,
            )
            soubor.save()
            if user:
                soubor.zaznamenej_nahrani(user)
            else:
                soubor.create_soubor_vazby()

    @property
    def expert_list_can_be_created(self):
        if self.typ_projektu.pk != TYP_PROJEKTU_ZACHRANNY_ID:
            return False
        if self.stav not in (PROJEKT_STAV_ARCHIVOVANY, PROJEKT_STAV_UZAVRENY, PROJEKT_STAV_UKONCENY_V_TERENU):
            return False
        return True

    def create_expert_list(self, popup_parametry=None):
        elc = ExpertniListCreator(self, popup_parametry)
        path = elc.build_document()
        return path

    @property
    def should_generate_confirmation_document(self):
        if self.stav == PROJEKT_STAV_ZAPSANY and self.has_oznamovatel():
            return True
        return False

    def get_absolute_url(self):
        return reverse("projekt:detail", kwargs={"ident_cely": self.ident_cely})


class ProjektKatastr(models.Model):
    projekt = models.ForeignKey(Projekt, on_delete=models.CASCADE)
    katastr = models.ForeignKey(RuianKatastr, on_delete=models.RESTRICT)

    def __str__(self):
        return "P: " + str(self.projekt) + " - K: " + str(self.katastr)

    class Meta:
        unique_together = (("projekt", "katastr"),)
        db_table = "projekt_katastr"
