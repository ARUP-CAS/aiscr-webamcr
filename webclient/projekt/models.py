import datetime
import logging
import os
import zlib

from django.contrib.gis.db import models as pgmodels
from django.contrib.gis.db.models.functions import AsGML, AsWKT
from django.contrib.postgres.fields import DateRangeField
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.db import models
from django.db.models.functions import Cast, Substr
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext as _
from django_prometheus.models import ExportModelOperationsMixin

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
from core.repository_connector import RepositoryBinaryFile
from heslar.hesla import (
    HESLAR_PAMATKOVA_OCHRANA,
    HESLAR_PROJEKT_TYP,
)
from heslar.hesla_dynamicka import (
    TYP_PROJEKTU_PRUZKUM_ID,
    TYP_PROJEKTU_ZACHRANNY_ID,
)
from heslar.models import Heslar, RuianKatastr
from historie.models import Historie, HistorieVazby
from projekt.doc_utils import OznameniPDFCreator
from projekt.rtf_utils import ExpertniListCreator
from uzivatel.models import Organizace, Osoba, User
from xml_generator.models import ModelWithMetadata

logger = logging.getLogger(__name__)


class Projekt(ExportModelOperationsMixin("projekt"), ModelWithMetadata):
    """
    Class pro db model projekt.
    """
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
        choices=CHOICES, default=PROJEKT_STAV_OZNAMENY, verbose_name=_("Stav"), db_index=True
    )
    typ_projektu = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="typ_projektu",
        related_name="projekty_typu",
        limit_choices_to={"nazev_heslare": HESLAR_PROJEKT_TYP},
        verbose_name=_("Typ projektů"),
        db_index=True,
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
        db_index=True,
    )
    datum_zahajeni = models.DateField(
        blank=True, null=True, verbose_name=_("Datum zahájení")
    )
    datum_ukonceni = models.DateField(
        blank=True, null=True, verbose_name=_("Datum ukončení")
    )
    kulturni_pamatka = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="kulturni_pamatka",
        blank=True,
        null=True,
        limit_choices_to={"nazev_heslare": HESLAR_PAMATKOVA_OCHRANA},
        verbose_name=_("Památka"),
        db_index=True,
    )
    termin_odevzdani_nz = models.DateField(blank=True, null=True)
    ident_cely = models.TextField(
        unique=True, verbose_name=_("Identifikátor")
    )
    geom = pgmodels.PointField(blank=True, null=True, srid=4326)
    soubory = models.OneToOneField(
        SouborVazby,
        on_delete=models.SET_NULL,
        db_column="soubory",
        blank=True,
        null=True,
        related_name="projekt_souboru",
    )
    historie = models.OneToOneField(
        HistorieVazby,
        on_delete=models.SET_NULL,
        db_column="historie",
        related_name="projekt_historie",
        null=True,
    )
    organizace = models.ForeignKey(
        Organizace, models.RESTRICT, db_column="organizace", blank=True, null=True, db_index=True
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
        on_delete=models.RESTRICT,
        db_column="hlavni_katastr",
        related_name="projekty_hlavnich_katastru",
        verbose_name=_("Hlavní katastr"),
        db_index=True,
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
        """
        Metóda pro nastavení pomocného stavu vytvořený.
        """
        self.stav = PROJEKT_STAV_VYTVORENY
        self.save()

    def set_oznameny(self):
        """
        Metóda pro nastavení stavu oznámený a uložení změny do historie.
        """
        self.stav = PROJEKT_STAV_OZNAMENY
        owner = get_object_or_404(User, email="amcr@arup.cas.cz")
        Historie(
            typ_zmeny=OZNAMENI_PROJ,
            uzivatel=owner,
            vazba=self.historie,
        ).save()
        self.save()

    def set_schvaleny(self, user, old_ident):
        """
        Metóda pro nastavení stavu schvýlený a uložení změny do historie.
        """
        logger.debug("projekt.models.Projekt.set_schvaleny.start", extra={"old_ident": old_ident})
        self.stav = PROJEKT_STAV_ZAPSANY
        Historie(
            typ_zmeny=SCHVALENI_OZNAMENI_PROJ,
            uzivatel=user,
            vazba=self.historie,
            poznamka=f"{old_ident} -> {self.ident_cely}",
        ).save()
        self.save()
        self.record_ident_change(old_ident)
        logger.debug("projekt.models.Projekt.set_schvaleny.end", extra={"old_ident": old_ident})

    def set_zapsany(self, user):
        """
        Metóda pro nastavení stavu zapsaný a uložení změny do historie.
        """
        self.stav = PROJEKT_STAV_ZAPSANY
        Historie(typ_zmeny=ZAPSANI_PROJ, uzivatel=user, vazba=self.historie).save()
        self.save()
        if self.typ_projektu == TYP_PROJEKTU_ZACHRANNY_ID:
            self.create_confirmation_document(user)

    def set_prihlaseny(self, user):
        """
        Metóda pro nastavení stavu prihlásený a uložení změny do historie.
        """
        self.stav = PROJEKT_STAV_PRIHLASENY
        Historie(
            typ_zmeny=PRIHLASENI_PROJ,
            uzivatel=user,
            vazba=self.historie,
        ).save()
        self.save()

    def set_zahajeny_v_terenu(self, user):
        """
        Metóda pro nastavení stavu zahájený v terénu a uložení změny do historie.
        """
        self.stav = PROJEKT_STAV_ZAHAJENY_V_TERENU
        Historie(
            typ_zmeny=ZAHAJENI_V_TERENU_PROJ,
            uzivatel=user,
            vazba=self.historie,
        ).save()
        self.save()

    def set_ukoncen_v_terenu(self, user):
        """
        Metóda pro nastavení stavu ukončený v terénu a uložení změny do historie.
        """
        self.stav = PROJEKT_STAV_UKONCENY_V_TERENU
        Historie(
            typ_zmeny=UKONCENI_V_TERENU_PROJ,
            uzivatel=user,
            vazba=self.historie,
        ).save()
        self.save()

    def set_uzavreny(self, user):
        """
        Metóda pro nastavení stavu uzavřený a uložení změny do historie.
        """
        self.stav = PROJEKT_STAV_UZAVRENY
        Historie(
            typ_zmeny=UZAVRENI_PROJ,
            uzivatel=user,
            vazba=self.historie,
        ).save()
        self.save()

    def set_archivovany(self, user):
        """
        Metóda pro nastavení stavu archivovaný a uložení změny do historie.
        Součásti je archivace dokumentů a odesláni emailu.
        """
        from services.mailer import Mailer
        if self.typ_projektu.id == TYP_PROJEKTU_ZACHRANNY_ID:
            # Removing personal information from the projekt announcement
            if self.has_oznamovatel():
                self.oznamovatel.delete()
            # making txt file with deleted files
            today = datetime.datetime.now()
            soubory = self.soubory.soubory.exclude(
                nazev__regex="^log_dokumentace_"
            )
            if soubory.count() > 0:
                filename = (
                        "log_dokumentace_" + today.strftime("%Y-%m-%d-%H-%M") + ".txt"
                )
                ("soubory/APD/" + filename, "w+")
                file_content = (
                        "Z důvodu ochrany osobních údajů byly dne %s automaticky odstraněny následující soubory z projektové dokumentace:\n"
                        % today.strftime("%d. %m. %Y")
                )
                file_content += "\n".join(soubory.values_list("nazev", flat=True))
                prev = 0
                prev = zlib.crc32(bytes(file_content, "utf-8"), prev)
                new_filename = "%d_%s" % (prev & 0xFFFFFFFF, filename)
                myfile = ContentFile(content=file_content, name=new_filename)
                aktual_soubor = Soubor(
                    vazba=self.soubory,
                    nazev=filename,
                    mimetype="text/plain",
                    size_mb=myfile.size/1024/1024,
                )
                aktual_soubor.save()
                aktual_soubor.path.save(name=new_filename, content=myfile)
                aktual_soubor.zaznamenej_nahrani(user=user)
                for file in soubory:
                    file.path.delete()
                items_deleted = soubory.delete()
                logger.debug("projekt.models.Projekt.set_archivovany.files_deleted",
                             extra={"deleted": items_deleted[0]})

        self.stav = PROJEKT_STAV_ARCHIVOVANY
        Historie(typ_zmeny=ARCHIVACE_PROJ, uzivatel=user, vazba=self.historie).save()
        Mailer.send_ea01(project=self, user=user)
        self.save()

    def set_navrzen_ke_zruseni(self, user: User, poznamka: str):
        """
        Metóda pro nastavení stavu navržen k zrušení a uložení změny do historie.
        """
        self.stav = PROJEKT_STAV_NAVRZEN_KE_ZRUSENI
        Historie(
            typ_zmeny=NAVRZENI_KE_ZRUSENI_PROJ,
            uzivatel=user,
            poznamka=poznamka,
            vazba=self.historie,
        ).save()
        self.save()

    def set_zruseny(self, user, poznamka):
        """
        Metóda pro nastavení stavu zrušený a uložení změny do historie.
        """
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
        """
        Metóda pro vrácení stavu zpět a uložení změny do historie.
        """
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
        """
        Metóda pro nastavení stavu zapsaný ze stavu zrušen nebo navrh na zrušení a uložení změny do historie.
        """
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
        """
        Metóda na kontrolu prerekvizit pred posunem do stavu archivovaný:
            
            Připojení akce musejí být ve stavu archivovaná.
        """
        result = {}
        for akce in self.akce_set.all():
            if akce.archeologicky_zaznam.stav != AZ_STAV_ARCHIVOVANY:
                result[akce.archeologicky_zaznam.ident_cely] = _(
                    "Akce musí být archivovaná!"
                )
        return result

    def check_pred_navrzeni_k_zruseni(self):
        """
        Metóda na kontrolu prerekvizit pred posunem do stavu navržen ke zrušení:

            Projekt nesmí mít pripojené akce.
        """
        has_event = len(self.akce_set.all()) > 0
        if has_event:
            return {"has_event": _("Projekt před zrušením nesmí mít projektové akce.")}
        else:
            return {}

    def check_pred_smazanim(self):
        """
        Metóda na kontrolu prerekvizit pred smazaním projektu:

            Projekt nesmí mít žádnou akci, soubor ani samostatný nález.
        """
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
        """
        Metóda na kontrolu prerekvizit pred posunem do stavu uzavřený:

            Projekt musí mít alespoň jednou akci která projde svou kontrolou před odesláním.
        """
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
        """
        Metóda pro rozdelení identu na region, rok, pořadové číslo a jestli je permanentí.
        """
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
            if self.pk:
                logger.warning("projekt.models.Projekt.parse_ident_cely.cannot_retrieve_ident_cely",
                               extra={"pk": self.pk})
            else:
                logger.warning("projekt.models.Projekt.parse_ident_cely.cannot_retrieve_ident_cely.no_pk")
        return permanent, region, year, number

    def has_oznamovatel(self):
        """
        Metóda na kontrolu jestli má projekt oznamovatele.
        """
        has_oznamovatel = False
        try:
            has_oznamovatel = self.oznamovatel is not None
        except ObjectDoesNotExist:
            pass
        return has_oznamovatel

    def set_permanent_ident_cely(self):
        """
        Metóda na nastavení permanentního identu akce z projektu sekvence.
        """
        MAXIMUM: int = 99999
        current_year = datetime.datetime.now().year
        region = self.hlavni_katastr.okres.kraj.rada_id
        try:
            sequence = ProjektSekvence.objects.get(region=region, rok=current_year)
            if sequence.sekvence >= MAXIMUM:
                raise MaximalIdentNumberError(MAXIMUM)
            sequence.sekvence += 1
        except ObjectDoesNotExist:
            projekts = Projekt.objects.filter(ident_cely__startswith=f"{region}-{str(current_year)}")
            if projekts.count() > 0:
                last = projekts.annotate(sekv=Cast(Substr("ident_cely", 7), models.IntegerField())).order_by("-sekv")[0]
                if last.sekv >= MAXIMUM:
                    raise MaximalIdentNumberError(MAXIMUM)
                sequence = ProjektSekvence.objects.create(region=region, rok=current_year, sekvence=last.sekv+1)
            else:
                sequence = ProjektSekvence.objects.create(region=region, rok=current_year, sekvence=1)
        sequence.save()
        self.ident_cely = (
            sequence.region + "-" + str(sequence.rok) + f"{sequence.sekvence:05}"
        )
        self.save()

    def create_confirmation_document(self, additional=False, user=None):
        """
        Metóda na vytvoření oznámovací dokumentace.
        """
        creator = OznameniPDFCreator(self.oznamovatel, self, additional)
        rep_bin_file: RepositoryBinaryFile = creator.build_document()
        duplikat = Soubor.objects.filter(nazev=rep_bin_file.filename)
        if not duplikat.exists():
            soubor = Soubor(
                vazba=self.soubory,
                nazev=rep_bin_file.filename,
                mimetype="application/pdf",
                path=rep_bin_file.url_without_domain,
                size_mb=rep_bin_file.size_mb,
                sha_512=rep_bin_file.sha_512(),
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

    @property
    def pristupnost(self):
        return Heslar.objects.get(ident_cely="HES-000865")

    @property
    def planovane_zahajeni_str(self):
        if self.planovane_zahajeni:
            return f"[{self.planovane_zahajeni.lower}, {self.planovane_zahajeni.upper + datetime.timedelta(days=-1)}]"
        else:
            return ""

    def record_ident_change(self, old_ident_cely):
        logger.debug("xml_generator.models.ModelWithMetadata.record_ident_change.start")
        from core.repository_connector import FedoraRepositoryConnector
        from core.utils import get_mime_type
        from core.views import get_projekt_soubor_name
        connector = FedoraRepositoryConnector(self)
        connector.record_ident_change(old_ident_cely)
        for soubor in self.soubory.soubory.all():
            soubor: Soubor
            repository_binary_file = soubor.get_repository_content()
            rep_bin_file = connector.save_binary_file(get_projekt_soubor_name(soubor.nazev),
                                                      get_mime_type(soubor.nazev),
                                                      repository_binary_file.content)
        logger.debug("xml_generator.models.ModelWithMetadata.record_ident_change.end")


class ProjektKatastr(ExportModelOperationsMixin("projekt_katastr"), models.Model):
    """
    Class pro db model dalších katastru proketu.
    """
    projekt = models.ForeignKey(Projekt, on_delete=models.CASCADE)
    katastr = models.ForeignKey(RuianKatastr, on_delete=models.RESTRICT)

    def __str__(self):
        return "P: " + str(self.projekt) + " - K: " + str(self.katastr)

    class Meta:
        unique_together = (("projekt", "katastr"),)
        db_table = "projekt_katastr"
