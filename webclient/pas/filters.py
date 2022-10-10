import logging

import crispy_forms
import django_filters
import django_filters as filters
from dal import autocomplete
from crispy_forms.layout import Div, Layout, HTML
from django.contrib.auth.models import Group
from django.db import utils
from django.db.models import Q
from django.forms import Select, SelectMultiple
from django.utils.translation import gettext as _
from django_filters import (
    CharFilter,
    ModelMultipleChoiceFilter,
    MultipleChoiceFilter,
    DateFromToRangeFilter,
    NumberFilter,
)
from django_filters.widgets import DateRangeWidget

from core.constants import (
    OBLAST_CECHY,
    OBLAST_CHOICES,
    OBLAST_MORAVA,
    ROLE_ARCHEOLOG_ID,
)
from heslar.hesla import (
    HESLAR_NALEZOVE_OKOLNOSTI,
    HESLAR_OBDOBI,
    HESLAR_PREDMET_DRUH,
    HESLAR_PREDMET_DRUH_KAT,
    HESLAR_PREDMET_SPECIFIKACE,
    HESLAR_OBDOBI_KAT, HESLAR_PRISTUPNOST,
)
from heslar.models import Heslar, RuianKraj, RuianOkres
from historie.models import Historie
from pas.models import SamostatnyNalez, UzivatelSpoluprace
from uzivatel.models import Organizace, Osoba, User
from dokument.filters import HistorieFilter
from heslar.views import heslar_12

logger = logging.getLogger(__name__)


class SamostatnyNalezFilter(HistorieFilter):

    stav = MultipleChoiceFilter(
        choices=SamostatnyNalez.PAS_STATES,
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
        ),
    )

    oblast = django_filters.ChoiceFilter(
        choices=OBLAST_CHOICES,
        label=_("Územní příslušnost"),
        method="filter_by_oblast",
        widget=Select(attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}),
    )
    kraj = MultipleChoiceFilter(
        choices=RuianKraj.objects.all().values_list("id", "nazev"),
        label=_("Kraj"),
        field_name="katastr__okres__kraj",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
        ),
    )

    okres = MultipleChoiceFilter(
        choices=RuianOkres.objects.all().values_list("id", "nazev"),
        label=_("Okres"),
        field_name="katastr__okres",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
        ),
    )

    katastr = CharFilter(
        lookup_expr="nazev__icontains",
        label=_("Katastr"),
    )

    vlastnik = ModelMultipleChoiceFilter(
        queryset=User.objects.select_related("organizace").all(),
        field_name="historie__historie__uzivatel",
        label="Vlastník",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
        ),
    )
    popisne_udaje = CharFilter(
        method="filter_popisne_udaje",
        label="Popisné údaje",
    )

    nalezce = ModelMultipleChoiceFilter(
        widget=autocomplete.ModelSelect2Multiple(url="heslar:osoba-autocomplete"),
        queryset=Osoba.objects.all(),
    )

    predano_organizace = ModelMultipleChoiceFilter(
        queryset=Organizace.objects.all(),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
        ),
    )

    obdobi = MultipleChoiceFilter(
        method="filter_obdobi",
        label=_("Období"),
        choices=heslar_12(HESLAR_OBDOBI, HESLAR_OBDOBI_KAT)[1:],
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
        ),
    )

    okolnosti = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_NALEZOVE_OKOLNOSTI),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
        ),
    )

    druh_nalezu = MultipleChoiceFilter(
        method="filter_druh_nalezu)",
        label=_("Druh nálezu"),
        choices=heslar_12(HESLAR_PREDMET_DRUH, HESLAR_PREDMET_DRUH_KAT)[1:],
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
        ),
    )

    specifikace = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_PREDMET_SPECIFIKACE),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
        ),
    )

    datum_nalezu = DateFromToRangeFilter(
        label=_("pas.filters.datumNalezu.label"),
        field_name="datum_nalezu",
        widget=DateRangeWidget(attrs={"type": "date","max":"2100-12-31"}),
        distinct=True,
    )

    hloubka_od = NumberFilter(
        field_name="hloubka", label=_("pas.filters.hloubka.label"), lookup_expr="gte"
    )

    hloubka_do = NumberFilter(field_name="hloubka", label=" ", lookup_expr="lte")

    # Filters by historie
    historie_typ_zmeny = MultipleChoiceFilter(
        choices=filter(lambda x: x[0].startswith("SN"), Historie.CHOICES),
        label="Změna stavu",
        field_name="historie__historie__typ_zmeny",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
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
        field_name="historie__historie__uzivatel",
        label="Uživatel",
        widget=autocomplete.ModelSelect2Multiple(url="uzivatel:uzivatel-autocomplete"),
        distinct=True,
    )

    pristupnost = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_PRISTUPNOST),
        label=_("Přístupnost"),
        field_name="pristupnost",
        widget=autocomplete.ModelSelect2Multiple(url="heslar:pristupnost-autocomplete"),
    )

    class Meta:
        model = SamostatnyNalez
        fields = {
            "ident_cely": ["icontains"],
            "predano": ["exact"],
            "pristupnost": ["exact"],
        }

    def __init__(self, *args, **kwargs):
        super(SamostatnyNalezFilter, self).__init__(*args, **kwargs)
        self.helper = SamostatnyNalezFilterFormHelper()

    def filter_obdobi(self, queryset, name, value):
        return queryset.filter(obdobi__in=value)

    def filter_druh_nalezu(self, queryset, name, value):
        return queryset.filter(druh_nalezu__in=value)

    def filter_popisne_udaje(self, queryset, name, value):
        return queryset.filter(
            Q(lokalizace__icontains=value)
            | Q(poznamka__icontains=value)
            | Q(evidencni_cislo__icontains=value)
        )

    def filter_by_oblast(self, queryset, name, value):
        if value == OBLAST_CECHY:
            return queryset.filter(ident_cely__contains="C-")
        if value == OBLAST_MORAVA:
            return queryset.filter(ident_cely__contains="M-")
        return queryset


class UzivatelSpolupraceFilter(filters.FilterSet):
    vedouci = ModelMultipleChoiceFilter(
        queryset=User.objects.select_related("organizace"),
        field_name="vedouci",
        label="Vedoucí",
        widget=autocomplete.ModelSelect2Multiple(url="uzivatel:uzivatel-autocomplete"),
    )

    spolupracovnik = ModelMultipleChoiceFilter(
        queryset=User.objects.select_related("organizace"),
        field_name="spolupracovnik",
        label="Spolupracovník",
        widget=autocomplete.ModelSelect2Multiple(url="uzivatel:uzivatel-autocomplete"),
    )

    class Meta:
        model = UzivatelSpoluprace
        fields = ["stav"]

    def __init__(self, *args, **kwargs):
        super(UzivatelSpolupraceFilter, self).__init__(*args, **kwargs)
        try:
            self.filters["vedouci"].extra.update(
                {
                    "queryset": User.objects.select_related("organizace").filter(
                        hlavni_role=Group.objects.get(id=ROLE_ARCHEOLOG_ID)
                    )
                }
            )
        except utils.ProgrammingError as err:
            self.filters["vedouci"].extra.update({"queryset": None})

        self.helper = UzivatelSpolupraceFilterFormHelper()


class SamostatnyNalezFilterFormHelper(crispy_forms.helper.FormHelper):
    form_method = "GET"
    layout = Layout(
        Div(
            Div("ident_cely__icontains", css_class="col-sm-2"),
            Div("nalezce", css_class="col-sm-2"),
            Div("datum_nalezu", css_class="col-sm-4 app-daterangepicker"),
            Div("predano_organizace", css_class="col-sm-2"),
            Div("predano", css_class="col-sm-2"),
            Div("katastr", css_class="col-sm-2"),
            Div("okres", css_class="col-sm-2"),
            Div("kraj", css_class="col-sm-2"),
            Div("oblast", css_class="col-sm-2"),
            Div("popisne_udaje", css_class="col-sm-4"),
            Div("obdobi", css_class="col-sm-2"),
            Div("druh_nalezu", css_class="col-sm-2"),
            Div("specifikace", css_class="col-sm-2"),
            Div("okolnosti", css_class="col-sm-2"),
            Div("hloubka_od", css_class="col-sm-2"),
            Div("hloubka_do", css_class="col-sm-2"),
            Div("pristupnost", css_class="col-sm-2"),
            Div("stav", css_class="col-sm-2"),
            Div(
                HTML(_('<span class="app-divider-label">Výběr podle historie</span>')),
                HTML(_('<hr class="mt-0" />')),
                css_class="col-sm-12",
            ),
            Div("historie_typ_zmeny", css_class="col-sm-2"),
            Div("historie_datum_zmeny_od", css_class="col-sm-4 app-daterangepicker"),
            Div("historie_uzivatel", css_class="col-sm-4"),
            css_class="row",
        ),
    )
    form_tag = False


class UzivatelSpolupraceFilterFormHelper(crispy_forms.helper.FormHelper):
    form_method = "GET"
    layout = Layout(
        Div(
            Div("vedouci", css_class="col-sm-4"),
            Div("spolupracovnik", css_class="col-sm-4"),
            Div("stav", css_class="col-sm-4"),
            css_class="row",
        ),
    )
    form_tag = False
