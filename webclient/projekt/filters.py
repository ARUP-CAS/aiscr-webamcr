import logging

import crispy_forms
from arch_z.models import ArcheologickyZaznam
from core.constants import (
    OBLAST_CECHY,
    OBLAST_CHOICES,
    OBLAST_MORAVA,
    OZNAMENI_PROJ,
    PROJEKT_RELATION_TYPE,
    SCHVALENI_OZNAMENI_PROJ,
)
from core.forms import SelectMultipleSeparator
from crispy_forms.layout import HTML, Div, Layout
from dal import autocomplete
from django.db.models import Q, QuerySet
from django.forms import SelectMultiple
from django.utils.translation import gettext_lazy as _
from django_filters import CharFilter, DateFromToRangeFilter, FilterSet, ModelMultipleChoiceFilter, MultipleChoiceFilter
from django_filters.widgets import DateRangeWidget
from dokument.filters import HistorieFilter
from heslar.hesla import (
    HESLAR_AKCE_TYP,
    HESLAR_AKCE_TYP_KAT,
    HESLAR_PAMATKOVA_OCHRANA,
    HESLAR_PRISTUPNOST,
    HESLAR_PROJEKT_TYP,
)
from heslar.models import Heslar, RuianKatastr, RuianKraj, RuianOkres
from heslar.views import heslar_12
from historie.models import Historie
from projekt.forms import ProjektFilterForm
from projekt.models import Projekt
from psycopg2._range import DateRange
from uzivatel.models import Organizace, Osoba, User

logger = logging.getLogger(__name__)


class MyAutocompleteWidget(autocomplete.ModelSelect2):
    """
    Override na třídu atocomplete widgetu pro nevrácení media objektů - js scriptů.
    """

    def media(self):
        return ()


class Users(QuerySet):
    def active_processes(self):
        return self.select_related("first_name", "last_name")


class KatastrFilterMixin(FilterSet):
    """
    Třída pro filtrování záznamu podle katastru, kraje, okresu a popisních údajů.
    Třída je prepoužita v dalších filtrech.
    """

    kraj = MultipleChoiceFilter(
        choices=RuianKraj.objects.all().values_list("id", "nazev"),
        label=_("projekt.filters.katastrFilter.kraj.label"),
        method="filtr_katastr_kraj",
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    okres = MultipleChoiceFilter(
        choices=RuianOkres.objects.all().values_list("id", "nazev"),
        label=_("projekt.filters.katastrFilter.okres.label"),
        method="filtr_katastr_okres",
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    katastr = ModelMultipleChoiceFilter(
        queryset=RuianKatastr.objects.all(),
        method="filtr_katastr",
        label=_("projekt.filters.katastrFilter.katastr.label"),
        widget=autocomplete.ModelSelect2Multiple(url="heslar:katastr-autocomplete"),
        distinct=True,
    )

    popisne_udaje = CharFilter(
        method="filter_popisne_udaje",
        label=_("projekt.filters.katastrFilter.popisneUdaje.label"),
        distinct=True,
    )

    def filtr_katastr(self, queryset, name, value):
        """
        Metóda pro filtrování podle názvu hlavního a dalších katastrů.
        """
        if value:
            return queryset.filter(Q(hlavni_katastr__in=value) | Q(katastry__in=value)).distinct()
        return queryset

    def filtr_katastr_kraj(self, queryset, name, value):
        """
        Metóda pro filtrování podle názvu okresu hlavního a dalších katastrů.
        """
        return queryset.filter(Q(hlavni_katastr__okres__kraj__in=value) | Q(katastry__okres__kraj__in=value)).distinct()

    def filtr_katastr_okres(self, queryset, name, value):
        """
        Metóda pro filtrování podle názvu kraje hlavního a dalších katastrů.
        """
        return queryset.filter(Q(hlavni_katastr__okres__in=value) | Q(katastry__okres__in=value)).distinct()

    def filter_popisne_udaje(self, queryset, name, value):
        """
        Metóda pro filtrování podle popisních údajů.
        """
        return queryset.filter(
            Q(lokalizace__icontains=value)
            | Q(kulturni_pamatka_cislo__icontains=value)
            | Q(kulturni_pamatka_popis__icontains=value)
            | Q(parcelni_cislo__icontains=value)
            | Q(oznaceni_stavby__icontains=value)
            | Q(podnet__icontains=value)
            | Q(uzivatelske_oznaceni__icontains=value)
            | Q(oznamovatel__oznamovatel__icontains=value)
            | Q(oznamovatel__odpovedna_osoba__icontains=value)
            | Q(oznamovatel__adresa__icontains=value)
            | Q(oznamovatel__telefon__icontains=value)
            | Q(oznamovatel__email__icontains=value)
        ).distinct()


class ProjektFilter(HistorieFilter, KatastrFilterMixin, FilterSet):
    """
    Třída pro filtrování projektů.
    """

    HISTORIE_TYP_ZMENY_STARTS_WITH = "P"
    TYP_VAZBY = PROJEKT_RELATION_TYPE

    ident_cely = CharFilter(
        lookup_expr="icontains",
        distinct=True,
    )

    typ_projektu = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_PROJEKT_TYP),
        label=_("projekt.filters.projektFilter.typProjektu.label"),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    stav = MultipleChoiceFilter(
        choices=Projekt.CHOICES,
        label=_("projekt.filters.projektFilter.stav.label"),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    datum_zahajeni = DateFromToRangeFilter(
        field_name="datum_zahajeni",
        label=_("projekt.filters.projektFilter.datumZahajeni.label"),
        widget=DateRangeWidget(attrs={"type": "text", "max": "2100-12-31"}),
        distinct=True,
    )

    datum_ukonceni = DateFromToRangeFilter(
        field_name="datum_ukonceni",
        label=_("projekt.filters.projektFilter.datumUkonceni.label"),
        widget=DateRangeWidget(attrs={"type": "text", "max": "2100-12-31"}),
        distinct=True,
    )

    vedouci_projektu = ModelMultipleChoiceFilter(
        queryset=Osoba.objects.all(),
        label=_("projekt.filters.projektFilter.vedouci.label"),
        widget=autocomplete.ModelSelect2Multiple(url="heslar:osoba-autocomplete"),
        distinct=True,
    )
    organizace = ModelMultipleChoiceFilter(
        queryset=Organizace.objects.all(),
        label=_("projekt.filters.projektFilter.organizace.label"),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )
    kulturni_pamatka = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_PAMATKOVA_OCHRANA),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    planovane_zahajeni = DateFromToRangeFilter(
        # field_name="planovane_zahajeni",
        method="filter_planovane_zahajeni",
        widget=DateRangeWidget(attrs={"type": "text", "max": "2100-12-31"}),
        distinct=True,
    )

    termin_odevzdani_nz = DateFromToRangeFilter(
        field_name="termin_odevzdani_nz",
        label=_("projekt.filters.projektFilter.terminOdevzdani.label"),
        widget=DateRangeWidget(attrs={"type": "text", "max": "2100-12-31"}),
        distinct=True,
    )

    # Dle transakci nevyuzito"
    """
    datum_oznameni_od = DateFilter(
        method="filter_announced_after",
        label="Datum oznámení od",
        widget=DateInput(attrs={"data-provide": "datepicker"}),
    )
    datum_oznameni_do = DateFilter(
        method="filter_announced_before",
        label="Datum oznámení do",
        widget=DateInput(attrs={"data-provide": "datepicker"}),
    )
    datum_schvaleni_od = DateFilter(
        method="filter_approved_after",
        label="Datum schválení od",
        widget=DateInput(attrs={"data-provide": "datepicker"}),
    )
    datum_schvaleni_do = DateFilter(
        method="filter_approved_before",
        label="Datum schválení do",
        widget=DateInput(attrs={"data-provide": "datepicker"}),
    )
    """

    # Filters by historie
    historie_typ_zmeny = MultipleChoiceFilter(
        choices=list(
            filter(
                lambda x: x[0].startswith("P") and not x[0].startswith("PI") or x[0].startswith("KAT"),
                Historie.CHOICES,
            )
        ),
        label=_("projekt.filters.projektFilter.historieTypeZmeny.label"),
        field_name="historie__historie__typ_zmeny",
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    # Filters by event
    akce_ident_obsahuje = CharFilter(
        field_name="akce__archeologicky_zaznam__ident_cely",
        lookup_expr="icontains",
        label=_("projekt.filters.projektFilter.idAkce.label"),
        distinct=True,
    )

    akce_zjisteni = MultipleChoiceFilter(
        method="filter_has_positive_find",
        label=_("projekt.filters.projektFilter.akceZjisteni.label"),
        choices=[
            ("True", _("projekt.filters.projektFilter.akceZjisteni.choice.pozitivni")),
            ("False", _("projekt.filters.projektFilter.akceZjisteni.choice.negativni")),
        ],
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    akce_popisne_udaje = CharFilter(
        method="filter_popisne_udaje_akce",
        label=_("projekt.filters.projektFilter.akcePopisneUdaje.label"),
        distinct=True,
    )

    akce_katastr = ModelMultipleChoiceFilter(
        method="filtr_akce_katastr",
        queryset=RuianKatastr.objects.all(),
        field_name="katastr",
        label=_("projekt.filters.projektFilter.akceKatastr.label"),
        widget=autocomplete.ModelSelect2Multiple(url="heslar:katastr-autocomplete"),
    )

    akce_kraj = MultipleChoiceFilter(
        choices=RuianKraj.objects.all().values_list("id", "nazev"),
        label=_("projekt.filters.projektFilter.akceKraj.label"),
        method="filtr_akce_katastr_kraj",
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    akce_okres = MultipleChoiceFilter(
        choices=RuianOkres.objects.all().values_list("id", "nazev"),
        label=_("projekt.filters.projektFilter.akceOkres.label"),
        method="filtr_akce_katastr_okres",
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    akce_vedouci = ModelMultipleChoiceFilter(
        method="filtr_akce_vedouci",
        label=_("projekt.filters.projektFilter.akceVedouci.label"),
        widget=autocomplete.ModelSelect2Multiple(url="heslar:osoba-autocomplete"),
        queryset=Osoba.objects.all(),
        distinct=True,
    )

    akce_vedouci_organizace = ModelMultipleChoiceFilter(
        queryset=Organizace.objects.all(),
        label=_("projekt.filters.projektFilter.akceVedouciOrganizace.label"),
        method="filtr_akce_organizace",
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    akce_datum_zahajeni = DateFromToRangeFilter(
        field_name="akce__datum_zahajeni",
        label=_("projekt.filters.projektFilter.akceDatumZahajeni.label"),
        widget=DateRangeWidget(attrs={"type": "text", "max": "2100-12-31"}),
        distinct=True,
    )
    akce_datum_ukonceni = DateFromToRangeFilter(
        field_name="akce__datum_ukonceni",
        label=_("projekt.filters.projektFilter.akceDatumUkonceni.label"),
        widget=DateRangeWidget(attrs={"type": "text", "max": "2100-12-31"}),
        distinct=True,
    )

    pristupnost_akce = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_PRISTUPNOST),
        field_name="akce__archeologicky_zaznam__pristupnost",
        label=_("projekt.filters.projektFilter.akcePristupnost.label"),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )
    stav_akce = MultipleChoiceFilter(
        choices=ArcheologickyZaznam.STATES,
        field_name="akce__archeologicky_zaznam__stav",
        label=_("projekt.filters.projektFilter.akceStav.label"),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )
    akce_je_nz = MultipleChoiceFilter(
        choices=[
            ("True", _("projekt.filters.projektFilter.akceJeNz.choice.ano")),
            ("False", _("projekt.filters.projektFilter.akceJeNz.choice.ne")),
        ],
        field_name="akce__je_nz",
        lookup_expr="iexact",
        label=_("projekt.filters.projektFilter.akceJeNz.label"),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    pian_ident_obsahuje = CharFilter(
        field_name="akce__archeologicky_zaznam__dokumentacni_jednotky_akce__pian__ident_cely",
        lookup_expr="icontains",
        label=_("projekt.filters.projektFilter.pianIdent.label"),
        distinct=True,
    )

    dokument_ident_obsahuje = CharFilter(
        # field_name="akce__archeologicky_zaznam__casti_dokumentu__dokument__ident_cely",
        # lookup_expr="icontains",
        method="filtr_dokumenty_ident",
        label=_("projekt.filters.projektFilter.dokumentIdent.label"),
        distinct=True,
    )

    zdroj_ident_obsahuje = CharFilter(
        field_name="akce__archeologicky_zaznam__externi_odkazy__externi_zdroj__ident_cely",
        lookup_expr="icontains",
        label=_("projekt.filters.projektFilter.ezIdent.label"),
        distinct=True,
    )

    adb_ident_obsahuje = CharFilter(
        field_name="akce__archeologicky_zaznam__dokumentacni_jednotky_akce__adb__ident_cely",
        lookup_expr="icontains",
        label=_("projekt.filters.projektFilter.adbIdent.label"),
        distinct=True,
    )

    historie_uzivatel_organizace = ModelMultipleChoiceFilter(
        queryset=Organizace.objects.all(),
        field_name="historie__historie__uzivatel__organizace",
        label=_("dokument.filters.Model3DFilter.filter_historie_uzivatel_organizace.label"),
        widget=SelectMultipleSeparator(),
        distinct=True,
    )

    typ_akce = MultipleChoiceFilter(
        choices=heslar_12(HESLAR_AKCE_TYP, HESLAR_AKCE_TYP_KAT)[1:],
        method="filter_akce_typ",
        label=_("projekt.filters.projektFilter.akceTyp.label"),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    oblast = MultipleChoiceFilter(
        choices=OBLAST_CHOICES,
        label=_("projekt.filters.projektFilter.oblast.label"),
        method="filter_by_oblast",
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    def filter_queryset(self, queryset):
        logger.debug("projekt.filters.AkceFilter.filter_queryset.start")
        queryset = super(ProjektFilter, self).filter_queryset(queryset)
        historie = self._get_history_subquery()
        if historie:
            queryset_history = Q(historie__typ_vazby=historie["typ_vazby"])
            if "uzivatel" in historie:
                queryset_history &= Q(historie__historie__uzivatel__in=historie["uzivatel"])
            if "uzivatel_organizace" in historie:
                queryset_history &= Q(historie__historie__organizace_snapshot__in=historie["uzivatel_organizace"])
            if "datum_zmeny__gte" in historie:
                queryset_history &= Q(historie__historie__datum_zmeny__gte=historie["datum_zmeny__gte"])
            if "datum_zmeny__lte" in historie:
                queryset_history &= Q(historie__historie__datum_zmeny__lte=historie["datum_zmeny__lte"])
            if "typ_zmeny" in historie:
                queryset_history &= Q(historie__historie__typ_zmeny__in=historie["typ_zmeny"])
            queryset = queryset.filter(queryset_history)
        logger.debug("projekt.filters.AkceFilter.filter_queryset.end", extra={"query": str(queryset.query)})
        return queryset

    def filter_planovane_zahajeni(self, queryset, name, value):
        """
        Metóda pro filtrování podle plánovaného zahájení.
        """
        if value.start and value.stop:
            rng = DateRange(
                lower=value.start.strftime("%m/%d/%Y"),
                upper=value.stop.strftime("%m/%d/%Y"),
            )
        elif value.start and not value.stop:
            rng = DateRange(
                lower=value.start.strftime("%m/%d/%Y"),
                upper="01/01/2100",
            )
        elif value.stop and not value.start:
            rng = DateRange(lower="01/01/1900", upper=value.stop.strftime("%m/%d/%Y"))
        else:
            rng = DateRange(lower="01/01/1900", upper="01/01/2100")
        return queryset.filter(planovane_zahajeni__overlap=rng)

    def filter_popisne_udaje_akce(self, queryset, name, value):
        """
        Metóda pro filtrování podle popisních údajů akce.
        """
        return queryset.filter(
            Q(akce__lokalizace_okolnosti__icontains=value)
            | Q(akce__souhrn_upresneni__icontains=value)
            | Q(akce__ulozeni_nalezu__icontains=value)
            | Q(akce__ulozeni_dokumentace__icontains=value)
            | Q(akce__archeologicky_zaznam__uzivatelske_oznaceni__icontains=value)
        ).distinct()

    def filter_has_positive_find(self, queryset, name, value):
        """
        Metóda pro filtrování podle pozitivního nálezu akce.
        """
        if "True" in value and "False" in value:
            return queryset.filter(akce__archeologicky_zaznam__dokumentacni_jednotky_akce__isnull=False).distinct()
        elif "True" in value:
            return queryset.filter(
                akce__archeologicky_zaznam__dokumentacni_jednotky_akce__negativni_jednotka=False
            ).distinct()
        elif "False" in value:
            return queryset.exclude(
                akce__archeologicky_zaznam__dokumentacni_jednotky_akce__negativni_jednotka=False
            ).distinct()

    def filter_by_oblast(self, queryset, name, value):
        """
        Metóda pro filtrování podle oblasti projektu.
        """
        if OBLAST_CECHY in value and OBLAST_MORAVA in value:
            return queryset
        if OBLAST_CECHY in value:
            return queryset.filter(ident_cely__contains="C-")
        if OBLAST_MORAVA in value:
            return queryset.filter(ident_cely__contains="M-")
        return queryset

    def filter_announced_after(self, queryset, name, value):
        """
        Metóda pro filtrování podle datumu oznámení od.
        """
        return queryset.filter(historie__historie__typ_zmeny=OZNAMENI_PROJ).filter(
            historie__historie__datum_zmeny__gte=value
        )

    def filter_announced_before(self, queryset, name, value):
        """
        Metóda pro filtrování podle datumu oznámení do.
        """
        return queryset.filter(historie__historie__typ_zmeny=OZNAMENI_PROJ).filter(
            historie__historie__datum_zmeny__lte=value
        )

    def filter_approved_after(self, queryset, name, value):
        """
        Metóda pro filtrování podle datumu schválení od.
        """
        return queryset.filter(historie__historie__typ_zmeny=SCHVALENI_OZNAMENI_PROJ).filter(
            historie__historie__datum_zmeny__gte=value
        )

    def filter_approved_before(self, queryset, name, value):
        """
        Metóda pro filtrování podle datumu schválení do.
        """
        return queryset.filter(historie__historie__typ_zmeny=SCHVALENI_OZNAMENI_PROJ).filter(
            historie__historie__datum_zmeny__lte=value
        )

    def filter_akce_typ(self, queryset, name, value):
        """
        Metóda pro filtrování podle typu akce.
        """
        return queryset.filter(Q(akce__hlavni_typ__in=value) | Q(akce__vedlejsi_typ__in=value)).distinct()

    def filtr_akce_katastr(self, queryset, name, value):
        """
        Metóda pro filtrování podle katastru akce.
        """
        if value:
            return queryset.filter(
                Q(akce__archeologicky_zaznam__hlavni_katastr__in=value)
                | Q(akce__archeologicky_zaznam__katastry__in=value)
            ).distinct()
        return queryset

    def filtr_akce_katastr_kraj(self, queryset, name, value):
        """
        Metóda pro filtrování podle kraje katastru akce.
        """
        return queryset.filter(
            Q(akce__archeologicky_zaznam__hlavni_katastr__okres__kraj__in=value)
            | Q(akce__archeologicky_zaznam__katastry__okres__kraj__in=value)
        ).distinct()

    def filtr_akce_katastr_okres(self, queryset, name, value):
        """
        Metóda pro filtrování podle okresu katastru akce.
        """
        return queryset.filter(
            Q(akce__archeologicky_zaznam__hlavni_katastr__okres__in=value)
            | Q(akce__archeologicky_zaznam__katastry__okres__in=value)
        ).distinct()

    def filtr_akce_vedouci(self, queryset, name, value):
        """
        Metóda pro filtrování podle vedoucího akce.
        """
        if not value:
            return queryset
        return queryset.filter(Q(akce__hlavni_vedouci__in=value) | Q(akce__akcevedouci__vedouci__in=value)).distinct()

    def filtr_akce_organizace(self, queryset, name, value):
        """
        Metóda pro filtrování podle organizace akce.
        """
        if value:
            return queryset.filter(
                Q(akce__organizace__in=value) | Q(akce__akcevedouci__organizace__in=value)
            ).distinct()
        else:
            return queryset

    def filtr_dokumenty_ident(self, queryset, name, value):
        """
        Metóda pro filtrování podle identu dokumentu.
        """
        return queryset.filter(
            Q(akce__archeologicky_zaznam__casti_dokumentu__dokument__ident_cely__icontains=value)
            | Q(casti_dokumentu__dokument__ident_cely__icontains=value)
        ).distinct()

    class Meta:
        model = Projekt
        fields = [
            "ident_cely",
            "hlavni_katastr",
        ]
        form = ProjektFilterForm

    def __init__(self, *args, **kwargs):
        super(ProjektFilter, self).__init__(*args, **kwargs)
        user: User = kwargs.get("request").user
        self.filters["typ_akce"].extra["choices"] = heslar_12(HESLAR_AKCE_TYP, HESLAR_AKCE_TYP_KAT)[1:]
        self.filters["oblast"].extra["choices"] = OBLAST_CHOICES

        self.helper = ProjektFilterFormHelper()
        self.set_filter_fields(user)


class ProjektFilterFormHelper(crispy_forms.helper.FormHelper):
    """
    Třída pro správne zobrazení filtru.
    """

    form_method = "GET"

    def __init__(self, form=None):
        history_divider = "<span class='app-divider-label'>%(translation)s</span>" % {
            "translation": _("projekt.filters.history.divider.label")
        }
        akce_divider = "<span class='app-divider-label'>%(translation)s</span>" % {
            "translation": _("projekt.filters.akce.divider.label")
        }
        dok_divider = "<span class='app-divider-label'>%(translation)s</span>" % {
            "translation": _("projekt.filters.dok.divider.label")
        }
        self.layout = Layout(
            Div(
                Div(
                    Div("ident_cely", css_class="col-sm-2"),
                    Div("typ_projektu", css_class="col-sm-2"),
                    Div("stav", css_class="col-sm-2"),
                    Div("organizace", css_class="col-sm-2"),
                    Div("vedouci_projektu", css_class="col-sm-2"),
                    Div("kulturni_pamatka", css_class="col-sm-2"),
                    Div("katastr", css_class="col-sm-2"),
                    Div("okres", css_class="col-sm-2"),
                    Div("kraj", css_class="col-sm-2"),
                    Div("oblast", css_class="col-sm-2"),
                    Div("popisne_udaje", css_class="col-sm-4"),
                    Div("planovane_zahajeni", css_class="col-sm-4 app-daterangepicker"),
                    Div("datum_zahajeni", css_class="col-sm-4 app-daterangepicker"),
                    Div("datum_ukonceni", css_class="col-sm-4 app-daterangepicker"),
                    Div("termin_odevzdani_nz", css_class="col-sm-4 app-daterangepicker"),
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
                    Div("historie_datum_zmeny_od", css_class="col-sm-4 app-daterangepicker"),
                    Div("historie_uzivatel", css_class="col-sm-3"),
                    Div("historie_uzivatel_organizace", css_class="col-sm-3"),
                    id="historieCollapse",
                    css_class="collapse row",
                ),
                Div(
                    HTML('<span class="material-icons app-icon-expand">expand_more</span>'),
                    HTML(akce_divider),
                    HTML('<hr class="mt-0" />'),
                    data_toggle="collapse",
                    href="#akcieCollapse",
                    role="button",
                    aria_expanded="false",
                    aria_controls="akcieCollapse",
                    css_class="col-sm-12 app-btn-show-more collapsed",
                ),
                Div(
                    Div("akce_ident_obsahuje", css_class="col-sm-2"),
                    Div("typ_akce", css_class="col-sm-2"),
                    Div("stav_akce", css_class="col-sm-2"),
                    Div("akce_vedouci_organizace", css_class="col-sm-2"),
                    Div("akce_vedouci", css_class="col-sm-2"),
                    Div("pristupnost_akce", css_class="col-sm-2"),
                    Div("akce_katastr", css_class="col-sm-2"),
                    Div("akce_okres", css_class="col-sm-2"),
                    Div("akce_kraj", css_class="col-sm-2"),
                    Div("akce_popisne_udaje", css_class="col-sm-6"),
                    Div("akce_datum_zahajeni", css_class="col-sm-4 app-daterangepicker"),
                    Div("akce_datum_ukonceni", css_class="col-sm-4 app-daterangepicker"),
                    Div("akce_zjisteni", css_class="col-sm-2"),
                    Div("akce_je_nz", css_class="col-sm-2"),
                    id="akcieCollapse",
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
                    Div("dokument_ident_obsahuje", css_class="col-sm-2"),
                    Div("pian_ident_obsahuje", css_class="col-sm-2"),
                    Div("zdroj_ident_obsahuje", css_class="col-sm-2"),
                    Div("adb_ident_obsahuje", css_class="col-sm-2"),
                    id="zaznamyCollapse",
                    css_class="collapse row",
                ),
            ),
        )
        self.form_tag = False
        super().__init__(form)
