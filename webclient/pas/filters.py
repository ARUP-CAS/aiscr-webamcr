import logging

import crispy_forms
import django_filters
import django_filters as filters
from core.constants import (
    OBLAST_CECHY,
    OBLAST_CHOICES,
    OBLAST_MORAVA,
    ROLE_ARCHEOLOG_ID,
)
from crispy_forms.layout import Div, Layout
from django.contrib.auth.models import Group
from django.db.models import Q
from django.forms import Select, SelectMultiple
from django.utils.translation import gettext as _
from django_filters import CharFilter, ModelMultipleChoiceFilter, MultipleChoiceFilter
from heslar.hesla import (
    HESLAR_NALEZOVE_OKOLNOSTI,
    HESLAR_OBDOBI,
    HESLAR_PREDMET_DRUH,
    HESLAR_PREDMET_SPECIFIKACE,
)
from heslar.models import Heslar, RuianKraj, RuianOkres
from pas.models import SamostatnyNalez, UzivatelSpoluprace
from uzivatel.models import Organizace, Osoba, User

logger = logging.getLogger(__name__)


class SamostatnyNalezFilter(filters.FilterSet):

    stav = MultipleChoiceFilter(
        choices=SamostatnyNalez.PAS_STATES,
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )

    oblast = django_filters.ChoiceFilter(
        choices=OBLAST_CHOICES,
        label=_("Územní příslušnost"),
        method="filter_by_oblast",
        widget=Select(attrs={"class": "selectpicker", "data-live-search": "true"}),
    )
    kraj = MultipleChoiceFilter(
        choices=RuianKraj.objects.all().values_list("id", "nazev"),
        label=_("Kraj"),
        field_name="katastr__okres__kraj",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )

    okres = MultipleChoiceFilter(
        choices=RuianOkres.objects.all().values_list("id", "nazev"),
        label=_("Okres"),
        field_name="katastr__okres",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
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
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )
    popisne_udaje = CharFilter(
        method="filter_popisne_udaje",
        label="Popisné údaje",
    )

    nalezce = ModelMultipleChoiceFilter(
        queryset=Osoba.objects.all(),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )

    predano_organizace = ModelMultipleChoiceFilter(
        queryset=Organizace.objects.all(),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )

    obdobi = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_OBDOBI),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )

    okolnosti = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_NALEZOVE_OKOLNOSTI),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )

    druh_nalezu = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_PREDMET_DRUH),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )

    specifikace = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_PREDMET_SPECIFIKACE),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )

    class Meta:
        model = SamostatnyNalez
        fields = {
            "ident_cely": ["icontains"],
            "datum_nalezu": ["lt", "gt"],
            "predano": ["exact"],
            "hloubka": ["lt", "gt"],
            "pristupnost": ["exact"],
        }

    def __init__(self, *args, **kwargs):
        super(SamostatnyNalezFilter, self).__init__(*args, **kwargs)
        self.helper = SamostatnyNalezFilterFormHelper()

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
        queryset=User.objects.select_related("organizace").filter(
            hlavni_role=Group.objects.get(id=ROLE_ARCHEOLOG_ID)
        ),
        field_name="vedouci",
        label="Vedoucí",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )

    spolupracovnik = ModelMultipleChoiceFilter(
        queryset=User.objects.select_related("organizace"),
        field_name="spolupracovnik",
        label="Spolupracovník",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )

    class Meta:
        model = UzivatelSpoluprace
        fields = ["stav"]

    def __init__(self, *args, **kwargs):
        super(UzivatelSpolupraceFilter, self).__init__(*args, **kwargs)
        self.helper = UzivatelSpolupraceFilterFormHelper()


class SamostatnyNalezFilterFormHelper(crispy_forms.helper.FormHelper):
    form_method = "GET"
    layout = Layout(
        Div(
            Div("ident_cely__icontains", css_class="col-sm-2"),
            Div("nalezce", css_class="col-sm-2"),
            Div("datum_nalezu__gt", css_class="col-sm-2"),
            Div("datum_nalezu__lt", css_class="col-sm-2"),
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
            Div("hloubka__gt", css_class="col-sm-2"),
            Div("hloubka__lt", css_class="col-sm-2"),
            Div("pristupnost", css_class="col-sm-2"),
            Div("stav", css_class="col-sm-2"),
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
