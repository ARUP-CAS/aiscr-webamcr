import logging
from datetime import datetime

import crispy_forms
from dal import autocomplete
import django_filters as filters
from django.db import utils

from arch_z.models import ArcheologickyZaznam
from core.constants import (
    OBLAST_CECHY,
    OBLAST_CHOICES,
    OBLAST_MORAVA,
    OZNAMENI_PROJ,
    SCHVALENI_OZNAMENI_PROJ,
)
from crispy_forms.layout import HTML, Div, Layout
from django.db.models import Q, QuerySet
from django.forms import Select, SelectMultiple
from django.utils.translation import gettext as _
from django_filters import (
    CharFilter,
    ChoiceFilter,
    DateFromToRangeFilter,
    ModelMultipleChoiceFilter,
    MultipleChoiceFilter,
)
from django_filters.widgets import DateRangeWidget
from heslar.hesla import (
    HESLAR_AKCE_TYP,
    HESLAR_PAMATKOVA_OCHRANA,
    HESLAR_PRISTUPNOST,
    HESLAR_PROJEKT_TYP,
    HESLAR_AKCE_TYP_KAT,
)
from heslar.models import Heslar, RuianKraj, RuianOkres
from projekt.models import Projekt
from psycopg2._range import DateRange
from uzivatel.models import Organizace, Osoba, User
from historie.models import Historie
from dokument.filters import HistorieFilter
from heslar.views import heslar_12

logger = logging.getLogger(__name__)

class MyAutocompleteWidget(autocomplete.ModelSelect2):
    def media(self):
        return ()


class Users(QuerySet):
    def active_processes(self):
        return self.select_related("first_name", "last_name")


class ProjektFilter(HistorieFilter):

    ident_cely = CharFilter(lookup_expr="icontains",distinct=True,)

    oblast = MultipleChoiceFilter(
        choices=OBLAST_CHOICES,
        label=_("Územní příslušnost"),
        method="filter_by_oblast",
        widget=SelectMultiple(attrs={"class": "selectpicker", "data-live-search": "true"}),
        distinct=True,
    )

    typ_projektu = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_PROJEKT_TYP),
        label=_("Typ"),
        widget=SelectMultiple(attrs={"class": "selectpicker", "data-live-search": "true"}),
        distinct=True,
    )

    kraj = MultipleChoiceFilter(
        choices=RuianKraj.objects.all().values_list("id", "nazev"),
        label=_("Kraj"),
        method="filtr_katastr_kraj",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )

    okres = MultipleChoiceFilter(
        choices=RuianOkres.objects.all().values_list("id", "nazev"),
        label=_("Okres"),
        method="filtr_katastr_okres",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )

    katastr = CharFilter(method="filtr_katastr", label=_("Katastr"),distinct=True,)

    popisne_udaje = CharFilter(method="filter_popisne_udaje", label="Popisné údaje",distinct=True,)

    stav = MultipleChoiceFilter(
        choices=Projekt.CHOICES,
        label=_("Stav"),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )

    datum_zahajeni = DateFromToRangeFilter(
        field_name="datum_zahajeni",
        label=_("Datum zahájení (od-do)"),
        widget=DateRangeWidget(attrs={"type": "date","max":"2100-12-31"}),
        distinct=True,
    )

    datum_ukonceni = DateFromToRangeFilter(
        field_name="datum_ukonceni",
        label=_("Datum ukončení (od-do)"),
        widget=DateRangeWidget(attrs={"type": "date","max":"2100-12-31"}),
        distinct=True,
    )

    vedouci_projektu = ModelMultipleChoiceFilter(
        queryset=Osoba.objects.all(),
        label=_("Vedoucí"),
        widget=autocomplete.ModelSelect2Multiple(url="heslar:osoba-autocomplete"),
        distinct=True,
    )
    organizace = ModelMultipleChoiceFilter(
        queryset=Organizace.objects.all(),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )
    kulturni_pamatka = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_PAMATKOVA_OCHRANA),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )

    planovane_zahajeni = DateFromToRangeFilter(
        # field_name="planovane_zahajeni",
        method="filter_planovane_zahajeni",
        widget=DateRangeWidget(attrs={"type": "date","max":"2100-12-31"}),
        distinct=True,
    )

    termin_odevzdani_nz = DateFromToRangeFilter(
        field_name="termin_odevzdani_nz",
        label=_("Termín odevzdání NZ (od-do)"),
        widget=DateRangeWidget(attrs={"type": "date","max":"2100-12-31"}),
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
        choices=filter(
            lambda x: x[0].startswith("P") and not x[0].startswith("PI"),
            Historie.CHOICES,
        ),
        label="Změna stavu",
        field_name="historie__historie__typ_zmeny",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )

    historie_datum_zmeny_od = DateFromToRangeFilter(
        label="Datum změny (od-do)",
        field_name="historie__historie__datum_zmeny",
        widget=DateRangeWidget(attrs={"type": "date","max":"2100-12-31"}),
        distinct=True,
    )

    historie_uzivatel = ModelMultipleChoiceFilter(
        queryset=User.objects.all(),
        label="Uživatel",
        field_name="historie__historie__uzivatel",
        widget=autocomplete.ModelSelect2Multiple(url="uzivatel:uzivatel-autocomplete"),
        distinct=True,
    )

    # Filters by event
    akce_ident_obsahuje = CharFilter(
        field_name="akce__archeologicky_zaznam__ident_cely",
        lookup_expr="icontains",
        label=_("ID akce"),
        distinct=True,
    )

    akce_zjisteni = MultipleChoiceFilter(
        method="filter_has_positive_find",
        label=_("Terénní zjištění"),
        choices=[("True", "pozitivní"), ("False", "negativní")],
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )

    akce_popisne_udaje = CharFilter(
        method="filter_popisne_udaje_akce", label="Popisné údaje", distinct=True,
    )

    akce_katastr = CharFilter(
        method="filtr_akce_katastr", label=_("Katastr"), distinct=True,
    )

    akce_kraj = MultipleChoiceFilter(
        choices=RuianKraj.objects.all().values_list("id", "nazev"),
        label=_("Kraj"),
        method="filtr_akce_katastr_kraj",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )

    akce_okres = MultipleChoiceFilter(
        choices=RuianOkres.objects.all().values_list("id", "nazev"),
        label=_("Okres"),
        method="filtr_akce_katastr_okres",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )

    akce_vedouci = MultipleChoiceFilter(
        method="filtr_akce_vedouci",
        choices=Osoba.objects.all().values_list("id", "vypis_cely"),
        widget=autocomplete.Select2Multiple(url="heslar:osoba-autocomplete-choices",),
        distinct=True,
    )

    akce_vedouci_organizace = MultipleChoiceFilter(
        choices=Organizace.objects.all().values_list("id", "nazev_zkraceny"),
        label="Organizace",
        method="filtr_akce_organizace",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )

    akce_datum_zahajeni = DateFromToRangeFilter(
        field_name="akce__datum_zahajeni",
        label="Datum zahájení (od-do)",
        widget=DateRangeWidget(attrs={"type": "date","max":"2100-12-31"}),
        distinct=True,
    )
    akce_datum_ukonceni = DateFromToRangeFilter(
        field_name="akce__datum_ukonceni",
        label="Datum ukončení (od-do)",
        widget=DateRangeWidget(attrs={"type": "date","max":"2100-12-31"}),
        distinct=True,
    )
    typ_akce = MultipleChoiceFilter(
        #choices=Heslar.objects.filter(nazev_heslare=HESLAR_AKCE_TYP).values_list(
        #    "id", "heslo"
        #),
        choices = heslar_12(HESLAR_AKCE_TYP, HESLAR_AKCE_TYP_KAT),
        method="filter_akce_typ",
        label="Typ",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )
    pristupnost_akce = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_PRISTUPNOST),
        field_name="akce__archeologicky_zaznam__pristupnost",
        label="Přístupnost",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )
    stav_akce = MultipleChoiceFilter(
        choices=ArcheologickyZaznam.STATES,
        field_name="akce__archeologicky_zaznam__stav",
        label="Stav",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )
    akce_je_nz = MultipleChoiceFilter(
        choices=[("True", "Ano"), ("False", "Ne")],
        field_name="akce__je_nz",
        lookup_expr="iexact",
        label="ZAA jako NZ",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )

    pian_ident_obsahuje = CharFilter(
        field_name="akce__archeologicky_zaznam__dokumentacni_jednotky_akce__pian__ident_cely",
        lookup_expr="icontains",
        label="ID PIAN",
        distinct=True,
    )

    dokument_ident_obsahuje = CharFilter(
        #field_name="akce__archeologicky_zaznam__casti_dokumentu__dokument__ident_cely",
        #lookup_expr="icontains",
        method = "filtr_dokumenty_ident",
        label="ID dokumentu",
        distinct=True,
    )

    zdroj_ident_obsahuje = CharFilter(
        field_name="akce__archeologicky_zaznam__externi_odkazy__externi_zdroj__ident_cely",
        lookup_expr="icontains",
        label="ID externího zdroje",
        distinct=True,
    )

    adb_ident_obsahuje = CharFilter(
        field_name="akce__archeologicky_zaznam__dokumentacni_jednotky_akce__adb__ident_cely",
        lookup_expr="icontains",
        label="ID ADB",
        distinct=True,
    )

    def filter_planovane_zahajeni(self, queryset, name, value):
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
            rng = DateRange(
                lower="01/01/1900", upper="01/01/2100"
            )
        return queryset.filter(planovane_zahajeni__overlap=rng)

    def filter_popisne_udaje_akce(self, queryset, name, value):
        return queryset.filter(
            Q(akce__lokalizace_okolnosti__icontains=value)
            | Q(akce__souhrn_upresneni__icontains=value)
            | Q(akce__ulozeni_nalezu__icontains=value)
            | Q(akce__ulozeni_dokumentace__icontains=value)
            | Q(akce__archeologicky_zaznam__uzivatelske_oznaceni__icontains=value)
        ).distinct()

    def filter_popisne_udaje(self, queryset, name, value):
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

    def filter_has_positive_find(self, queryset, name, value):
        if "True" in value and "False" in value:
            return queryset
        elif "True" in value:
            return queryset.filter(
                akce__archeologicky_zaznam__dokumentacni_jednotky_akce__negativni_jednotka=False
            ).distinct()
        elif "False" in value:
            return queryset.exclude(
                akce__archeologicky_zaznam__dokumentacni_jednotky_akce__negativni_jednotka=False
            ).distinct()

    def filter_by_oblast(self, queryset, name, value):
        if OBLAST_CECHY in value and OBLAST_MORAVA in value:
            return queryset
        if OBLAST_CECHY in value:
            return queryset.filter(ident_cely__contains="C-")
        if OBLAST_MORAVA in value:
            return queryset.filter(ident_cely__contains="M-")
        return queryset

    def filter_announced_after(self, queryset, name, value):
        return queryset.filter(historie__historie__typ_zmeny=OZNAMENI_PROJ).filter(
            historie__historie__datum_zmeny__gte=value
        )

    def filter_announced_before(self, queryset, name, value):
        return queryset.filter(historie__historie__typ_zmeny=OZNAMENI_PROJ).filter(
            historie__historie__datum_zmeny__lte=value
        )

    def filter_approved_after(self, queryset, name, value):
        return queryset.filter(
            historie__historie__typ_zmeny=SCHVALENI_OZNAMENI_PROJ
        ).filter(historie__historie__datum_zmeny__gte=value)

    def filter_approved_before(self, queryset, name, value):
        return queryset.filter(
            historie__historie__typ_zmeny=SCHVALENI_OZNAMENI_PROJ
        ).filter(historie__historie__datum_zmeny__lte=value)

    def filtr_katastr(self, queryset, name, value):
        return queryset.filter(
            Q(hlavni_katastr__nazev__icontains=value)
            | Q(katastry__nazev__icontains=value)
        ).distinct()

    def filtr_katastr_kraj(self, queryset, name, value):
        return queryset.filter(
            Q(hlavni_katastr__okres__kraj__in=value)
            | Q(katastry__okres__kraj__in=value)
        ).distinct()

    def filtr_katastr_okres(self, queryset, name, value):
        return queryset.filter(
            Q(hlavni_katastr__okres__in=value) | Q(katastry__okres__in=value)
        ).distinct()

    def filter_akce_typ(self, queryset, name, value):
        return queryset.filter(
            Q(akce__hlavni_typ__in=value) | Q(akce__vedlejsi_typ__in=value)
        ).distinct()

    def filtr_akce_katastr(self, queryset, name, value):
        return queryset.filter(
            Q(akce__archeologicky_zaznam__hlavni_katastr__nazev__icontains=value)
            | Q(akce__archeologicky_zaznam__katastry__nazev__icontains=value)
        ).distinct()

    def filtr_akce_katastr_kraj(self, queryset, name, value):
        return queryset.filter(
            Q(akce__archeologicky_zaznam__hlavni_katastr__okres__kraj__in=value)
            | Q(akce__archeologicky_zaznam__katastry__okres__kraj__in=value)
        ).distinct()

    def filtr_akce_katastr_okres(self, queryset, name, value):
        return queryset.filter(
            Q(akce__archeologicky_zaznam__hlavni_katastr__okres__in=value)
            | Q(akce__archeologicky_zaznam__katastry__okres__in=value)
        ).distinct()

    def filtr_akce_vedouci(self, queryset, name, value):
        return queryset.filter(
            Q(akce__hlavni_vedouci__id__in=value) | Q(akce__akcevedouci__vedouci__id__in=value)
        ).distinct()

    def filtr_akce_organizace(self, queryset, name, value):
        return queryset.filter(
            Q(akce__organizace__in=value) | Q(akce__akcevedouci__organizace__in=value)
        ).distinct()

    def filtr_dokumenty_ident(self, queryset, name, value):
        return queryset.filter(
            Q(akce__archeologicky_zaznam__casti_dokumentu__dokument__ident_cely__icontains=value) | Q(casti_dokumentu__dokument__ident_cely__icontains=value)
        ).distinct()

    class Meta:
        model = Projekt
        fields = [
            "ident_cely",
            "hlavni_katastr",
        ]

    def __init__(self, *args, **kwargs):
        super(ProjektFilter, self).__init__(*args, **kwargs)
        #try:
            #self.filters["historie_uzivatel"].extra.update({"queryset": User.objects.all()})
            #self.filters["akce_vedouci"].extra.update({"queryset": Osoba.objects.all()})
            #self.filters["vedouci_projektu"].extra.update({"queryset": Osoba.objects.all()})
        #except utils.ProgrammingError as err:
            #self.filters["historie_uzivatel"].choices = []
            #self.filters["akce_vedouci"].choices = []
            #self.filters["vedouci_projektu"].extra.update({"queryset": None})
        self.helper = ProjektFilterFormHelper()


class ProjektFilterFormHelper(crispy_forms.helper.FormHelper):
    form_method = "GET"
    layout = Layout(
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
            Div(
                HTML(_('<span class="app-divider-label">Výběr podle historie</span>')),
                HTML(_('<hr class="mt-0" />')),
                css_class="col-sm-12",
            ),
            Div("historie_typ_zmeny", css_class="col-sm-2"),
            Div("historie_datum_zmeny_od", css_class="col-sm-4 app-daterangepicker"),
            Div("historie_uzivatel", css_class="col-sm-4"),
            Div(
                HTML(_('<span class="app-divider-label">Výběr podle akcí</span>')),
                HTML(_('<hr class="mt-0" />')),
                css_class="col-sm-12",
            ),
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
            Div(
                HTML(
                    _(
                        '<span class="app-divider-label">Výběr podle souvisejících záznamů</span>'
                    )
                ),
                HTML(_('<hr class="mt-0" />')),
                css_class="col-sm-12",
            ),
            Div("dokument_ident_obsahuje", css_class="col-sm-2"),
            Div("pian_ident_obsahuje", css_class="col-sm-2"),
            Div("zdroj_ident_obsahuje", css_class="col-sm-2"),
            Div("adb_ident_obsahuje", css_class="col-sm-2"),
            css_class="row",
        ),
    )
    form_tag = False
