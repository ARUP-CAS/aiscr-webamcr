import logging

import crispy_forms
from dal import autocomplete
from crispy_forms.layout import Div, Layout, HTML
from django.db.models import Q, OuterRef, Subquery
from django.forms import SelectMultiple, Select, NumberInput
from django.utils.translation import gettext_lazy as _
from django_filters import (
    CharFilter,
    ModelMultipleChoiceFilter,
    MultipleChoiceFilter,
    DateFromToRangeFilter,
    RangeFilter,
    ChoiceFilter, FilterSet,
    NumberFilter
)
from django_filters.widgets import DateRangeWidget, SuffixedMultiWidget
from django_filters.fields import RangeField

from core.constants import ROLE_ADMIN_ID, ROLE_ARCHIVAR_ID, ARCHEOLOGICKY_ZAZNAM_RELATION_TYPE
from dj.models import DokumentacniJednotka
from heslar.hesla import (
    HESLAR_ADB_PODNET,
    HESLAR_ADB_TYP,
    HESLAR_AKCE_TYP,
    HESLAR_AKCE_TYP_KAT,
    HESLAR_AKTIVITA,
    HESLAR_AREAL,
    HESLAR_AREAL_KAT,
    HESLAR_DJ_TYP,
    HESLAR_OBDOBI,
    HESLAR_OBDOBI_KAT,
    HESLAR_OBJEKT_DRUH,
    HESLAR_OBJEKT_DRUH_KAT,
    HESLAR_OBJEKT_SPECIFIKACE,
    HESLAR_OBJEKT_SPECIFIKACE_KAT,
    HESLAR_PIAN_PRESNOST,
    HESLAR_PIAN_TYP,
    HESLAR_PREDMET_DRUH,
    HESLAR_PREDMET_DRUH_KAT,
    HESLAR_PREDMET_SPECIFIKACE,
    HESLAR_PRISTUPNOST,
    HESLAR_VYSKOVY_BOD_TYP,
)
from heslar.models import Heslar, RuianKraj, RuianOkres, RuianKatastr
from historie.filters import HistorieOrganizaceMultipleChoiceFilter
from historie.models import Historie
from projekt.filters import KatastrFilterMixin
from core.forms import SelectMultipleSeparator
from arch_z.forms import ArchzFilterForm
from .models import Akce
from arch_z.models import ArcheologickyZaznam
from uzivatel.models import Organizace, Osoba, User
from dokument.filters import HistorieFilter
from heslar.views import heslar_12


logger = logging.getLogger(__name__)


class NumberRangeWidget(SuffixedMultiWidget):
    template_name = "django_filters/widgets/multiwidget.html"
    suffixes = ["min", "max"]

    def __init__(self, attrs=None):
        widgets = (NumberInput, NumberInput)
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return [value.start, value.stop]
        return [None, None]


class NumberRangeField(RangeField):
    widget = NumberRangeWidget


class NumberRangeFilter(RangeFilter):
    field_class = NumberRangeField


class ArchZaznamFilter(HistorieFilter, KatastrFilterMixin, FilterSet):
    """
    Třída pro zakladní filtrování archeologických záznamů a jejich potomků.
    """
    # Filters by historie

    TYP_VAZBY = ARCHEOLOGICKY_ZAZNAM_RELATION_TYPE
    HISTORIE_TYP_ZMENY_STARTS_WITH = "AZ"

    stav = MultipleChoiceFilter(
        choices=ArcheologickyZaznam.STATES,
        field_name="archeologicky_zaznam__stav",
        label=_("arch_z.filters.ArchZaznamFilter.stav.label"),
        widget=SelectMultipleSeparator(),
        distinct=True,
    )

    ident_cely = CharFilter(
        field_name="archeologicky_zaznam__ident_cely",
        lookup_expr="icontains",
        label=_("arch_z.filters.ArchZaznamFilter.ident_cely.label"),
        distinct=True,
    )

    pristupnost = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_PRISTUPNOST),
        label=_("arch_z.filters.ArchZaznamFilter.pristupnost.label"),
        field_name="archeologicky_zaznam__pristupnost",
        widget=SelectMultipleSeparator(),
        distinct=True,
    )

    # Historie
    historie_typ_zmeny = MultipleChoiceFilter(
        choices=filter(lambda x: x[0].startswith("AZ") or x[0].startswith("KAT"), Historie.CHOICES),
        label=_("arch_z.filters.ArchZaznamFilter.historie_typ_zmeny.label"),
        field_name="archeologicky_zaznam__historie__historie__typ_zmeny",
        widget=SelectMultipleSeparator(),
        distinct=True,
    )

    # Dj a Pian
    dj_typ = ModelMultipleChoiceFilter(
        label=_("arch_z.filters.ArchZaznamFilter.dj_typ.label"),
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_DJ_TYP),
        field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__typ",
        widget=SelectMultipleSeparator(),
        distinct=True,
    )

    dj_nazev = CharFilter(
        label=_("arch_z.filters.ArchZaznamFilter.dj_nazev.label"),
        field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__nazev",
        lookup_expr="icontains",
        distinct=True,
    )

    dj_zjisteni = MultipleChoiceFilter(
        method="filter_dj_zjisteni",
        label=_("arch_z.filters.ArchZaznamFilter.dj_zjisteni.label"),
        choices=[("True", _("arch_z.filters.ArchZaznamFilter.dj_zjisteni.pozitivni")), ("False", _("arch_z.filters.ArchZaznamFilter.dj_zjisteni.negativni"))],
        widget=SelectMultipleSeparator(),
        distinct=True,
    )

    pian_ident_obsahuje = CharFilter(
        field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__pian__ident_cely",
        lookup_expr="icontains",
        label=_("arch_z.filters.ArchZaznamFilter.pian_ident_obsahuje.label"),
        distinct=True,
    )

    pian_typ = ModelMultipleChoiceFilter(
        label=_("arch_z.filters.ArchZaznamFilter.pianTyp.label"),
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_PIAN_TYP),
        field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__pian__typ",
        widget=SelectMultipleSeparator(),
        distinct=True,
    )

    pian_presnost = ModelMultipleChoiceFilter(
        label=_("arch_z.filters.ArchZaznamFilter.pian_presnost.label"),
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_PIAN_PRESNOST),
        field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__pian__presnost",
        widget=SelectMultipleSeparator(),
        distinct=True,
    )

    komponenta_jistota = MultipleChoiceFilter(
        label=_("arch_z.filters.ArchZaznamFilter.komponenta_jistota.label"),
        field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__komponenty__komponenty__jistota",
        choices=[
            (True, _("lokalita.filter.komponentaJistota.ano.label")),
            (False, _("lokalita.filter.komponentaJistota.ne.label")),
        ],
        widget=SelectMultipleSeparator(),
        distinct=True,
    )
    komponenta_aktivity = ModelMultipleChoiceFilter(
        label=_("arch_z.filters.ArchZaznamFilter.komponenta_aktivity.label"),
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_AKTIVITA),
        field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__komponenty__komponenty__komponentaaktivita__aktivita",
        widget=SelectMultipleSeparator(),
        distinct=True,
    )
    komponenta_poznamka = CharFilter(
        label=_("arch_z.filters.ArchZaznamFilter.komponenta_poznamka.label"),
        field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__komponenty__komponenty__poznamka",
        distinct=True,
    )

    predmet_specifikace = ModelMultipleChoiceFilter(
        label=_("arch_z.filters.ArchZaznamFilter.predmet_specifikace.label"),
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_PREDMET_SPECIFIKACE),
        field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__komponenty__komponenty__predmety__specifikace",
        widget=SelectMultipleSeparator(),
        distinct=True,
    )

    predmet_pozn_pocet = CharFilter(
        method="filter_predmet_pozn_pocet",
        label=_("arch_z.filters.ArchZaznamFilter.predmet_pozn_pocet.label"),
        distinct=True,
    )

    objekt_pozn_pocet = CharFilter(
        method="filter_objekt_pozn_pocet",
        label=_("arch_z.filters.ArchZaznamFilter.objekt_pozn_pocet.label"),
        distinct=True,
    )

    dokument_ident = CharFilter(
        field_name="archeologicky_zaznam__casti_dokumentu__dokument__ident_cely",
        lookup_expr="icontains",
        label=_("arch_z.filters.ArchZaznamFilter.dokument_ident.label"),
        distinct=True,
    )

    zdroj_ident = CharFilter(
        field_name="archeologicky_zaznam__externi_odkazy__externi_zdroj__ident_cely",
        lookup_expr="icontains",
        label=_("arch_z.filters.ArchZaznamFilter.zdroj_ident.label"),
        distinct=True,
    )


    def filtr_katastr(self, queryset, name, value):
        """
        Metóda pro filtrování podle hlavního i vedlejšího katastru.
        """
        if value:
            return queryset.filter(
                Q(archeologicky_zaznam__hlavni_katastr__in=value)
                | Q(archeologicky_zaznam__katastry__in=value)
            ).distinct()
        return queryset

    def filtr_katastr_kraj(self, queryset, name, value):
        """
        Metóda pro filtrování podle hlavního i vedlejšího kraje.
        """
        return queryset.filter(
            Q(archeologicky_zaznam__hlavni_katastr__okres__kraj__in=value)
            | Q(archeologicky_zaznam__katastry__okres__kraj__in=value)
        ).distinct()

    def filtr_katastr_okres(self, queryset, name, value):
        """
        Metóda pro filtrování podle hlavního i vedlejšího okresu.
        """
        return queryset.filter(
            Q(archeologicky_zaznam__hlavni_katastr__okres__in=value)
            | Q(archeologicky_zaznam__katastry__okres__in=value)
        ).distinct()

    def filter_dj_zjisteni(self, queryset, name, value):
        """
        Metóda pro filtrování podle dj_zjisteni.
        """
        if "True" in value and "False" in value:
            return queryset.filter(
                Q(
                    archeologicky_zaznam__dokumentacni_jednotky_akce__negativni_jednotka=False
                )
                | Q(
                    archeologicky_zaznam__dokumentacni_jednotky_akce__negativni_jednotka=True
                )
            ).distinct()
        elif "True" in value:
            return queryset.filter(
                archeologicky_zaznam__dokumentacni_jednotky_akce__negativni_jednotka=False
            ).distinct()
        elif "False" in value:
            return queryset.filter(
                archeologicky_zaznam__dokumentacni_jednotky_akce__negativni_jednotka=True
            ).distinct()

    def filter_predmet_pozn_pocet(self, queryset, name, value):
        """
        Metóda pro filtrování podle poznámky a počtu predmětu.
        """
        return queryset.filter(
            Q(
                archeologicky_zaznam__dokumentacni_jednotky_akce__komponenty__komponenty__predmety__poznamka__icontains=value
            )
            | Q(
                archeologicky_zaznam__dokumentacni_jednotky_akce__komponenty__komponenty__predmety__pocet__icontains=value
            )
        ).distinct()

    def filter_objekt_pozn_pocet(self, queryset, name, value):
        """
        Metóda pro filtrování podle poznámky a počtu objektu.
        """
        return queryset.filter(
            Q(
                archeologicky_zaznam__dokumentacni_jednotky_akce__komponenty__komponenty__objekty__poznamka__icontains=value
            )
            | Q(
                archeologicky_zaznam__dokumentacni_jednotky_akce__komponenty__komponenty__objekty__pocet__icontains=value
            )
        ).distinct()

    def __init__(self, *args, **kwargs):
        super(ArchZaznamFilter, self).__init__(*args, **kwargs)
        user: User = kwargs.get("request").user
        if user.hlavni_role.pk in (ROLE_ADMIN_ID, ROLE_ARCHIVAR_ID):
            self.filters["historie_uzivatel"] = ModelMultipleChoiceFilter(
                queryset=User.objects.all(),
                field_name="archeologicky_zaznam__historie__historie__uzivatel",
                label=_("arch_z.filters.ArchZaznamFilter.historie_uzivatel.label"),
                widget=autocomplete.ModelSelect2Multiple(url="uzivatel:uzivatel-autocomplete"),
                distinct=True,
            )
        else:
            self.filters["historie_uzivatel"] = ModelMultipleChoiceFilter(
                queryset=User.objects.all(),
                field_name="archeologicky_zaznam__historie__historie__uzivatel",
                label=_("arch_z.filters.ArchZaznamFilter.historie_uzivatel.label"),
                widget=autocomplete.ModelSelect2Multiple(url="uzivatel:uzivatel-autocomplete-public"),
                distinct=True,
            )
        self.filters["komponenta_obdobi"] = MultipleChoiceFilter(
            field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__komponenty__komponenty__obdobi",
            label=_("arch_z.filters.ArchZaznamFilter.komponenta_obdobi.label"),
            choices=heslar_12(HESLAR_OBDOBI, HESLAR_OBDOBI_KAT)[1:],
            widget=SelectMultipleSeparator(),
        )

        self.filters["komponenta_areal"] = MultipleChoiceFilter(
            field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__komponenty__komponenty__areal",
            label=_("arch_z.filters.ArchZaznamFilter.komponenta_areal.label"),
            choices=heslar_12(HESLAR_AREAL, HESLAR_AREAL_KAT)[1:],
            widget=SelectMultipleSeparator(),
            distinct=True,
        )

        self.filters["objekt_druh"] = MultipleChoiceFilter(
            field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__komponenty__komponenty__objekty__druh",
            label=_("arch_z.filters.ArchZaznamFilter.objekt_druh.label"),
            choices=heslar_12(HESLAR_OBJEKT_DRUH, HESLAR_OBJEKT_DRUH_KAT)[1:],
            widget=SelectMultipleSeparator(),
            distinct=True,
        )

        self.filters["objekt_specifikace"] = MultipleChoiceFilter(
            field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__komponenty__komponenty__objekty__specifikace",
            label=_("arch_z.filters.ArchZaznamFilter.objekt_specifikace.label"),
            choices=heslar_12(HESLAR_OBJEKT_SPECIFIKACE, HESLAR_OBJEKT_SPECIFIKACE_KAT)[1:],
            widget=SelectMultipleSeparator(),
            distinct=True,
        )

        self.filters["predmet_druh"] = MultipleChoiceFilter(
            field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__komponenty__komponenty__predmety__druh",
            label=_("arch_z.filters.ArchZaznamFilter.predmet_druh.label"),
            choices=heslar_12(HESLAR_PREDMET_DRUH, HESLAR_PREDMET_DRUH_KAT)[1:],
            widget=SelectMultipleSeparator(),
            distinct=True,
        )
        self.set_filter_fields(user)


class AkceFilter(ArchZaznamFilter):
    """
    Class pro filtrování akce.
    """

    organizace = ModelMultipleChoiceFilter(
        queryset=Organizace.objects.all(),
        label=_("arch_z.filters.AkceFilter.organizace.label"),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
    )

    vedouci = ModelMultipleChoiceFilter(
        method="filtr_vedouci",
        label=_("arch_z.filters.AkceFilter.vedouci.label"),
        widget=autocomplete.ModelSelect2Multiple(url="heslar:osoba-autocomplete"),
        queryset=Osoba.objects.all(),
        distinct=True,
    )

    zahrnout_projektove = ChoiceFilter(
        choices=[("False", _("arch_z.filters.AkceFilter.zahrnout_projektove.ne")), ("True", _("arch_z.filters.AkceFilter.zahrnout_projektove.ano"))],
        label=_("arch_z.filters.AkceFilter.zahrnout_projektove.label"),
        method="filtr_zahrnout_projektove",
        empty_label=None,
        null_label=None,
        widget=Select(
            attrs={
                "class": "selectpicker",
                "data-live-search": "true",
            }
        ),
    )

    datum_zahajeni = DateFromToRangeFilter(
        label=_("arch_z.filters.AkceFilter.datum_zahajeni.label"),
        field_name="datum_zahajeni",
        widget=DateRangeWidget(attrs={"type": "text", "max": "2100-12-31"}),
        distinct=True,
    )

    datum_ukonceni = DateFromToRangeFilter(
        label=_("arch_z.filters.AkceFilter.datum_ukonceni.label"),
        field_name="datum_ukonceni",
        widget=DateRangeWidget(attrs={"type": "text", "max": "2100-12-31"}),
        distinct=True,
    )

    je_nz = MultipleChoiceFilter(
        choices=[(False, _("arch_z.filters.AkceFilter.je_nz.ne")), (True, _("arch_z.filters.AkceFilter.je_nz.ano"))],
        label=_("arch_z.filters.AkceFilter.je_nz.label"),
        field_name="je_nz",
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    odlozena_nz = MultipleChoiceFilter(
        choices=[(False, _("arch_z.filters.AkceFilter.odlozena_nz.ne")), (True, _("arch_z.filters.AkceFilter.odlozena_nz.ano"))],
        label=_("arch_z.filters.AkceFilter.odlozena_nz.label"),
        field_name="odlozena_nz",
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    has_positive_find = MultipleChoiceFilter(
        method="filter_has_positive_find",
        label=_("arch_z.filters.AkceFilter.has_positive_find.label"),
        choices=[("True", _("arch_z.filters.AkceFilter.has_positive_find.pozitivni")), ("False", _("arch_z.filters.AkceFilter.has_positive_find.negativni"))],
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    adb_ident_obsahuje = CharFilter(
        field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__adb__ident_cely",
        lookup_expr="icontains",
        label=_("arch_z.filters.AkceFilter.adb_ident_obsahuje.label"),
        distinct=True,
    )

    adb_typ_sondy = ModelMultipleChoiceFilter(
        label=_("arch_z.filters.AkceFilter.adb_typ_sondy.label"),
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_ADB_TYP),
        field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__adb__typ_sondy",
        widget=SelectMultipleSeparator(),
        distinct=True,
    )

    adb_podnet = ModelMultipleChoiceFilter(
        label=_("arch_z.filters.AkceFilter.adb_podnet.label"),
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_ADB_PODNET),
        field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__adb__podnet",
        widget=SelectMultipleSeparator(),
        distinct=True,
    )

    adb_popisne_udaje = CharFilter(
        method="filter_adb_popisne_udaje",
        label=_("arch_z.filters.AkceFilter.adb_popisne_udaje.label"),
        distinct=True,
    )

    adb_autori = ModelMultipleChoiceFilter(
        method="filtr_adb_autori",
        label=_("arch_z.filters.AkceFilter.adb_autori.label"),
        widget=autocomplete.ModelSelect2Multiple(url="heslar:osoba-autocomplete"),
        queryset=Osoba.objects.all(),
        distinct=True,
    )

    adb_roky = RangeFilter(
        label=_("arch_z.filters.AkceFilter.adb_roky.label"),
        method="filter_adb_roky",
        widget=DateRangeWidget(
            attrs={
                "max": "2100-12-31",
                "class": "textinput textInput dateinput form-control date_roky",
            }
        ),
        distinct=True,
    )

    vb_ident_obsahuje = CharFilter(
        field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__adb__vyskove_body__ident_cely",
        lookup_expr="icontains",
        label=_("arch_z.filters.AkceFilter.vb_ident_obsahuje.label"),
        distinct=True,
    )

    vb_uroven = ModelMultipleChoiceFilter(
        label=_("arch_z.filters.AkceFilter.vb_uroven.label"),
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_VYSKOVY_BOD_TYP),
        field_name="archeologicky_zaznam__dokumentacni_jednotky_akce__adb__vyskove_body__typ",
        widget=SelectMultipleSeparator(),
        distinct=True,
    )

    vb_niveleta_od = NumberFilter(
        label=_("arch_z.filters.AkceFilter.vb_niveleta.label"),
        method='filter_by_z_range',
        distinct=True,
    )

    vb_niveleta_do = NumberFilter(
        label=" ",
        method='filter_by_z_range',
        distinct=True,
    )

    typ = MultipleChoiceFilter(
        method="filter_akce_typ",
        label=_("arch_z.filters.AkceFilter.typ.label"),
        choices=heslar_12(HESLAR_AKCE_TYP, HESLAR_AKCE_TYP_KAT)[1:],
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
    )

    def filter_akce_typ(self, queryset, name, value):
        """
        Metóda pro filtrování podle typu akce.
        """
        return queryset.filter(
            Q(hlavni_typ__in=value) | Q(vedlejsi_typ__in=value)
        ).distinct()

    def filtr_vedouci(self, queryset, name, value):
        """
        Metóda pro filtrování podle hlavního a vedlejšiho vedoucího akce.
        """
        if not value:
            return queryset
        return queryset.filter(
            Q(hlavni_vedouci__in=value) | Q(akcevedouci__vedouci__in=value)
        ).distinct()

    def filter_popisne_udaje(self, queryset, name, value):
        """
        Metóda pro filtrování podle lokalizace, upřesnení, uložení, označení akce.
        """
        return queryset.filter(
            Q(lokalizace_okolnosti__icontains=value)
            | Q(souhrn_upresneni__icontains=value)
            | Q(ulozeni_nalezu__icontains=value)
            | Q(ulozeni_dokumentace__icontains=value)
            | Q(archeologicky_zaznam__uzivatelske_oznaceni__icontains=value)
        ).distinct()

    def filtr_zahrnout_projektove(self, queryset, name, value):
        """
        Metóda pro filtrování mezi projektovými a samostatnými akcemi.
        """
        if value is None:
            return queryset.exclude(typ=Akce.TYP_AKCE_PROJEKTOVA)
        if "True" in value:
            return queryset
        elif "False" in value:
            return queryset.exclude(typ=Akce.TYP_AKCE_PROJEKTOVA)

    def filter_has_positive_find(self, queryset, name, value):
        """
        Metóda pro filtrování podle toho či akce má pozitivní DJ.
        """
        if "True" not in value and "False" not in value:
            return queryset
        queryset = queryset.filter(archeologicky_zaznam__dokumentacni_jednotky_akce__isnull=False)
        if "True" in value and "False" in value:
            return queryset
        doumentacni_jednotka_subquery = DokumentacniJednotka.objects \
            .filter(negativni_jednotka=False).values_list("archeologicky_zaznam__pk", flat=True)
        if "True" in value:
            return queryset.filter(pk__in=doumentacni_jednotka_subquery).distinct()
        if "False" in value:
            return queryset.filter(~Q(pk__in=doumentacni_jednotka_subquery)).distinct()

    def filter_adb_popisne_udaje(self, queryset, name, value):
        """
        Metóda pro filtrování podle popisných údajů ADB.
        """
        return queryset.filter(
            Q(
                archeologicky_zaznam__dokumentacni_jednotky_akce__adb__uzivatelske_oznaceni_sondy__icontains=value
            )
            | Q(
                archeologicky_zaznam__dokumentacni_jednotky_akce__adb__cislo_popisne__icontains=value
            )
            | Q(
                archeologicky_zaznam__dokumentacni_jednotky_akce__adb__trat__icontains=value
            )
            | Q(
                archeologicky_zaznam__dokumentacni_jednotky_akce__adb__parcelni_cislo__icontains=value
            )
            | Q(
                archeologicky_zaznam__dokumentacni_jednotky_akce__adb__poznamka__icontains=value
            )
        ).distinct()

    def filtr_adb_autori(self, queryset, name, value):
        """
        Metóda pro filtrování podle autorů revize a popisu ADB.
        """
        if not value:
            return queryset
        return queryset.filter(
            Q(
                archeologicky_zaznam__dokumentacni_jednotky_akce__adb__autor_popisu__in=value
            )
            | Q(
                archeologicky_zaznam__dokumentacni_jednotky_akce__adb__autor_revize__in=value
            )
        ).distinct()

    def filter_adb_roky(self, queryset, name, value):
        """
        Metóda pro filtrování podle roku revize a popisu ADB.
        """
        if value:
            if value.start is not None and value.stop is not None:
                self.lookup_expr = "range"
                value = (value.start, value.stop)
            elif value.start is not None:
                self.lookup_expr = "gte"
                value = value.start
            elif value.stop is not None:
                self.lookup_expr = "lte"
                value = value.stop
        lookup1 = "%s__%s" % (
            "archeologicky_zaznam__dokumentacni_jednotky_akce__adb__rok_popisu",
            self.lookup_expr,
        )
        lookup2 = "%s__%s" % (
            "archeologicky_zaznam__dokumentacni_jednotky_akce__adb__rok_revize",
            self.lookup_expr,
        )
        return queryset.filter(Q(**{lookup1: value}) | Q(**{lookup2: value})).distinct()

    def filter_by_z_range(self, queryset, name, value):
        if value:
            if name ==  'vb_niveleta_od':
                queryset = queryset.extra(where=["ST_Z(geom) >= %s"],params=[value])
            if name ==  'vb_niveleta_do':
                queryset = queryset.extra(where=["ST_Z(geom) <= %s"],params=[value])
        return queryset

    def filter_queryset(self, queryset):
        logger.debug("arch_z.filters.AkceFilter.filter_queryset.start")
        historie = self._get_history_subquery()
        queryset = super(AkceFilter, self).filter_queryset(queryset)
        if 'vb_niveleta_od' in self.request.GET or 'vb_niveleta_do' in self.request.GET:
            queryset = queryset.filter(
                    archeologicky_zaznam__dokumentacni_jednotky_akce__adb__vyskove_body__geom__isnull=False
                )            
        if historie:
            queryset_history = Q(archeologicky_zaznam__historie__typ_vazby=historie["typ_vazby"])
            if "uzivatel" in historie:
                queryset_history &= Q(archeologicky_zaznam__historie__historie__uzivatel__in=historie["uzivatel"])
            if "uzivatel_organizace" in historie:
                queryset_history &= Q(archeologicky_zaznam__historie__historie__organizace_snapshot__in
                                      =historie["uzivatel_organizace"])
            if "datum_zmeny__gte" in historie:
                queryset_history &= Q(archeologicky_zaznam__historie__historie__datum_zmeny__gte
                                      =historie["datum_zmeny__gte"])
            if "datum_zmeny__lte" in historie:
                queryset_history &= Q(archeologicky_zaznam__historie__historie__datum_zmeny__lte
                                      =historie["datum_zmeny__lte"])
            if "typ_zmeny" in historie:
                queryset_history &= Q(archeologicky_zaznam__historie__historie__typ_zmeny__in=historie["typ_zmeny"])
            queryset = queryset.filter(queryset_history)
        queryset.cache()
        logger.debug("arch_z.filters.AkceFilter.filter_queryset.end", extra={"query": str(queryset.query)})
        return queryset

    class Meta:
        model = Akce
        exclude = ("projekt",)
        form = ArchzFilterForm

    def __init__(self, *args, **kwargs):
        super(AkceFilter, self).__init__(*args, **kwargs)
        self.filters["typ"].extra["choices"] =heslar_12(HESLAR_AKCE_TYP, HESLAR_AKCE_TYP_KAT)[1:]
        self.filters["historie_uzivatel_organizace"] = HistorieOrganizaceMultipleChoiceFilter(
            label=_("arch_z.filters.ArchZaznamFilter.historie_uzivatel_organizace.label"),
            widget=SelectMultipleSeparator(),
            distinct=True,
        )
        self.helper = AkceFilterFormHelper()


class AkceFilterFormHelper(crispy_forms.helper.FormHelper):
    """
    Class pro form helper pro zobrazení formuláře.
    """
    form_method = "GET"
    def __init__(self, form=None):
        dj_pian_divider = u"<span class='app-divider-label'>%(translation)s</span>" % {
            "translation": _("arch_z.filters.AkceFilterFormHelper.djPian.divider.label")
        }
        history_divider = u"<span class='app-divider-label'>%(translation)s</span>" % {
            "translation": _(u"arch_z.filters.AkceFilterFormHelper.history.divider.label")
        }
        komponenta_divider = u"<span class='app-divider-label'>%(translation)s</span>" % {
            "translation": _(u"arch_z.filters.AkceFilterFormHelper.komponenta.divider.label")
        }
        dok_divider = u"<span class='app-divider-label'>%(translation)s</span>" % {
            "translation": _(u"arch_z.filters.AkceFilterFormHelper.dok.divider.label")
        }
        adb_divider = u"<span class='app-divider-label'>%(translation)s</span>" % {
            "translation": _(u"arch_z.filters.AkceFilterFormHelper.adb.divider.label")
        }
        self.layout = Layout(
            Div(
                Div(
                    Div("ident_cely", css_class="col-sm-2"),
                    Div("typ", css_class="col-sm-2"),
                    Div("stav", css_class="col-sm-2"),
                    Div("organizace", css_class="col-sm-2"),
                    Div("vedouci", css_class="col-sm-2"),
                    Div("pristupnost", css_class="col-sm-2"),
                    Div("katastr", css_class="col-sm-2"),
                    Div("okres", css_class="col-sm-2"),
                    Div("kraj", css_class="col-sm-2"),
                    Div("popisne_udaje", css_class="col-sm-4"),
                    Div("zahrnout_projektove", css_class="col-sm-2"),
                    Div("datum_zahajeni", css_class="col-sm-4 app-daterangepicker"),
                    Div("datum_ukonceni", css_class="col-sm-4 app-daterangepicker"),
                    Div("has_positive_find", css_class="col-sm-2"),
                    Div("je_nz", css_class="col-sm-2"),
                    Div("odlozena_nz", css_class="col-sm-2"),
                    css_class="row",
                ),
                Div(
                    HTML('<span class="material-icons app-icon-expand">expand_more</span>'),
                    HTML(history_divider),
                    HTML('<hr class="mt-0" />'),
                    data_toggle="collapse",
                    href="#historieCollapse",
                    role="button",
                    aria_expanded="false",
                    aria_controls="historieCollapse",
                    css_class="col-sm-12 app-btn-show-more collapsed",
                ),
                Div(
                    Div("historie_typ_zmeny", css_class="col-sm-2"),
                    Div(
                        "historie_datum_zmeny_od", css_class="col-sm-4 app-daterangepicker"
                    ),
                    Div("historie_uzivatel", css_class="col-sm-3"),
                    Div("historie_uzivatel_organizace", css_class="col-sm-3"),
                    id="historieCollapse",
                    css_class="collapse row",
                ),
                Div(
                    HTML('<span class="material-icons app-icon-expand">expand_more</span>'),
                    HTML(dj_pian_divider),
                    HTML('<hr class="mt-0" />'),
                    data_toggle="collapse",
                    href="#DjPianCollapse",
                    role="button",
                    aria_expanded="false",
                    aria_controls="DjPianCollapse",
                    css_class="col-sm-12 app-btn-show-more collapsed",
                ),
                Div(
                    Div("dj_typ", css_class="col-sm-2"),
                    Div("dj_nazev", css_class="col-sm-2"),
                    Div("dj_zjisteni", css_class="col-sm-2"),
                    Div("pian_ident_obsahuje", css_class="col-sm-2"),
                    Div("pian_typ", css_class="col-sm-2"),
                    Div("pian_presnost", css_class="col-sm-2"),
                    id="DjPianCollapse",
                    css_class="collapse row",
                ),
                Div(
                    HTML('<span class="material-icons app-icon-expand">expand_more</span>'),
                    HTML(komponenta_divider),
                    HTML('<hr class="mt-0" />'),
                    data_toggle="collapse",
                    href="#KomponentaCollapse",
                    role="button",
                    aria_expanded="false",
                    aria_controls="KomponentaCollapse",
                    css_class="col-sm-12 app-btn-show-more collapsed",
                ),
                Div(
                    Div("komponenta_obdobi", css_class="col-sm-2"),
                    Div("komponenta_jistota", css_class="col-sm-2"),
                    Div("komponenta_areal", css_class="col-sm-2"),
                    Div("komponenta_aktivity", css_class="col-sm-2"),
                    Div("komponenta_poznamka", css_class="col-sm-4"),
                    Div("predmet_druh", css_class="col-sm-2"),
                    Div("predmet_specifikace", css_class="col-sm-2"),
                    Div("predmet_pozn_pocet", css_class="col-sm-4"),
                    Div(css_class="col-sm-4"),
                    Div("objekt_druh", css_class="col-sm-2"),
                    Div("objekt_specifikace", css_class="col-sm-2"),
                    Div("objekt_pozn_pocet", css_class="col-sm-4"),
                    id="KomponentaCollapse",
                    css_class="collapse row",
                ),
                Div(
                    HTML('<span class="material-icons app-icon-expand">expand_more</span>'),
                    HTML(adb_divider),
                    HTML('<hr class="mt-0" />'),
                    data_toggle="collapse",
                    href="#AdbCollapse",
                    role="button",
                    aria_expanded="false",
                    aria_controls="AdbCollapse",
                    css_class="col-sm-12 app-btn-show-more collapsed",
                ),
                Div(
                    Div("adb_ident_obsahuje", css_class="col-sm-2"),
                    Div("adb_typ_sondy", css_class="col-sm-2"),
                    Div("adb_podnet", css_class="col-sm-2"),
                    Div("adb_popisne_udaje", css_class="col-sm-4"),
                    Div(css_class="col-sm-2"),
                    Div("adb_autori", css_class="col-sm-2"),
                    Div("adb_roky", css_class="col-sm-4 app-daterangepicker"),
                    Div(css_class="col-sm-6"),
                    Div("vb_ident_obsahuje", css_class="col-sm-2"),
                    Div("vb_uroven", css_class="col-sm-2"),
                    Div("vb_niveleta_od", css_class="col-sm-2"),
                    Div("vb_niveleta_do", css_class="col-sm-2"),
                    id="AdbCollapse",
                    css_class="collapse row",
                ),
                Div(
                    HTML('<span class="material-icons app-icon-expand">expand_more</span>'),
                    HTML(dok_divider),
                    HTML('<hr class="mt-0" />'),
                    data_toggle="collapse",
                    href="#zaznamyCollapse",
                    role="button",
                    aria_expanded="false",
                    aria_controls="zaznamyCollapse",
                    css_class="col-sm-12 app-btn-show-more collapsed",
                ),
                Div(
                    Div("dokument_ident", css_class="col-sm-2"),
                    Div("zdroj_ident", css_class="col-sm-2"),
                    id="zaznamyCollapse",
                    css_class="collapse row",
                ),
            ),
        )
        self.form_tag = False
        super().__init__(form)
