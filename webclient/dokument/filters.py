import logging

import crispy_forms
import django_filters as filters
from dal import autocomplete
from django.db import utils
from django.db import models
from django_filters.widgets import DateRangeWidget
from crispy_forms.layout import Div, Layout, HTML
from django.forms import SelectMultiple, NumberInput
from django_filters import (
    CharFilter,
    ModelMultipleChoiceFilter,
    MultipleChoiceFilter,
    NumberFilter,
    DateFromToRangeFilter,
)
from dokument.models import Dokument
from historie.models import Historie
from django.db.models import Q
from heslar.hesla import (
    HESLAR_AREAL_KAT,
    HESLAR_OBDOBI,
    HESLAR_OBDOBI_KAT,
    HESLAR_DOKUMENT_TYP,
    HESLAR_DOKUMENT_FORMAT,
    HESLAR_OBJEKT_DRUH_KAT,
    HESLAR_OBJEKT_SPECIFIKACE_KAT,
    HESLAR_PREDMET_DRUH_KAT,
    MODEL_3D_DOKUMENT_TYPES,
    HESLAR_ZEME,
    HESLAR_AREAL,
    HESLAR_AKTIVITA,
    HESLAR_OBJEKT_DRUH,
    HESLAR_OBJEKT_SPECIFIKACE,
    HESLAR_PREDMET_DRUH,
    HESLAR_PREDMET_SPECIFIKACE,
)
from heslar.models import Heslar
from uzivatel.models import Organizace, User, Osoba
from django.utils.translation import gettext as _

from heslar.views import heslar_12

logger = logging.getLogger(__name__)


class HistorieFilter(filters.FilterSet):
    def filter_queryset(self, queryset):
        """
        Filter the queryset with the underlying form's `cleaned_data`. You must
        call `is_valid()` or `errors` before calling this method.
        This method should be overridden if additional filtering needs to be
        applied to the queryset before it is cached.
        """
        zmena = self.form.cleaned_data["historie_typ_zmeny"]
        uzivatel = self.form.cleaned_data["historie_uzivatel"]
        datum = self.form.cleaned_data["historie_datum_zmeny_od"]
        filtered = Historie.objects.all()
        if zmena:
            filtered = filtered.filter(typ_zmeny__in=zmena)
        if uzivatel:
            filtered = filtered.filter(uzivatel__in=uzivatel)
        if datum and datum.start:
            filtered = filtered.filter(datum_zmeny__gte=datum.start)
        if datum and datum.stop:
            filtered = filtered.filter(datum_zmeny__lte=datum.stop)
        queryset = queryset.filter(historie__historie__in=filtered)
        for name, value in self.form.cleaned_data.items():
            queryset = self.filters[name].filter(queryset, value)
            assert isinstance(queryset, models.QuerySet), \
                "Expected '%s.%s' to return a QuerySet, but got a %s instead." \
                % (type(self).__name__, name, type(queryset).__name__)
        return queryset


class DokumentFilter(HistorieFilter):

    ident_cely = CharFilter(lookup_expr="icontains", label="ID")

    typ_dokumentu = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_DOKUMENT_TYP).filter(
            id__in=MODEL_3D_DOKUMENT_TYPES
        ),
        label=_("Typ"),
        widget=SelectMultiple(attrs={"class": "selectpicker"}),
    )

    format = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_DOKUMENT_FORMAT).filter(
            heslo__startswith="3D"
        ),
        label=_("Formát"),
        field_name="extra_data__format",
        widget=SelectMultiple(attrs={"class": "selectpicker"}),
    )

    stav = MultipleChoiceFilter(
        choices=Dokument.STATES,
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )

    organizace = ModelMultipleChoiceFilter(
        queryset=Organizace.objects.all(),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )

    autor = ModelMultipleChoiceFilter(
        label=_("Autor"),
        field_name="autori",
        widget=autocomplete.ModelSelect2Multiple(url="uzivatel:osoba-autocomplete"),
        queryset=Osoba.objects.all(),
    )

    rok_vzniku_od = NumberFilter(
        field_name="rok_vzniku", label=_("Rok vzniku (od-do)"), lookup_expr="gte"
    )

    rok_vzniku_do = NumberFilter(field_name="rok_vzniku", label=" ", lookup_expr="lte")

    duveryhodnost = NumberFilter(
        field_name="extra_data__duveryhodnost",
        label=_("Důvěryhodnost (min. %)"),
        lookup_expr="gte",
        widget=NumberInput(attrs={"min": "1", "max": "100"}),
        distinct=True,
    )
    popisne_udaje = CharFilter(label=_("Popisné údaje"), method="filter_popisne_udaje",)

    zeme = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_ZEME),
        field_name="extra_data__zeme",
        label=_("Země"),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )

    obdobi = MultipleChoiceFilter(
        method = "filter_obdobi",
        label=_("Období"),
        choices=heslar_12(HESLAR_OBDOBI, HESLAR_OBDOBI_KAT),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )

    areal = MultipleChoiceFilter(
        method = "filter_areal",
        label=_("Areál"),
        choices=heslar_12(HESLAR_AREAL, HESLAR_AREAL_KAT),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )

    aktivity = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(
            nazev_heslare=HESLAR_AKTIVITA
        ),  # nezda se mi pouziti obou hesel - plati i pro create a edit
        field_name="casti__komponenty__komponenty__komponentaaktivita__aktivita",
        label=_("Aktivity"),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )

    predmet_druh = MultipleChoiceFilter(
        method = "filter_predmety_druh",
        label=_("Druh předmětu"),
        choices=heslar_12(HESLAR_PREDMET_DRUH, HESLAR_PREDMET_DRUH_KAT),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )

    predmet_specifikace = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(
            nazev_heslare=HESLAR_PREDMET_SPECIFIKACE
        ),  # nezda se mi pouziti obou hesel - plati i pro create a edit
        field_name="casti__komponenty__komponenty__predmety__specifikace",
        label=_("Specifikace předmětu"),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )
    objekt_druh = MultipleChoiceFilter(
        method = "filter_objekty_druh",
        label=_("Druh objektu"),
        choices=heslar_12(HESLAR_OBJEKT_DRUH, HESLAR_OBJEKT_DRUH_KAT),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )

    objekt_specifikace = MultipleChoiceFilter(
        method = "filter_objekty_specifikace",
        label=_("Specifikace objektu"),
        choices=heslar_12(HESLAR_OBJEKT_SPECIFIKACE, HESLAR_OBJEKT_SPECIFIKACE_KAT),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )

    # Filters by historie
    historie_typ_zmeny = MultipleChoiceFilter(
        choices=filter(
            lambda x: x[0].startswith("D"), Historie.CHOICES
        ),  # Historie.CHOICES.,
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
        widget=DateRangeWidget(attrs={"type": "date"}),
        distinct=True,
    )

    historie_uzivatel = ModelMultipleChoiceFilter(
        queryset=User.objects.all(),
        field_name="historie__historie__uzivatel",
        label="Uživatel",
        widget=autocomplete.ModelSelect2Multiple(url="uzivatel:uzivatel-autocomplete"),
        distinct=True,
    )

    def filter_popisne_udaje(self, queryset, name, value):
        return queryset.filter(
            Q(oznaceni_originalu__icontains=value)
            | Q(popis__icontains=value)
            | Q(poznamka__icontains=value)
            | Q(extra_data__odkaz__icontains=value)
            | Q(casti__komponenty__komponenty__objekty__poznamka__icontains=value)
            | Q(casti__komponenty__komponenty__predmety__poznamka__icontains=value)
        )

    def filter_obdobi(self, queryset, name, value):
        return queryset.filter(casti__komponenty__komponenty__obdobi__in=value)

    def filter_areal(self, queryset, name, value):
        return queryset.filter(casti__komponenty__komponenty__areal__in=value)
    
    def filter_predmety_druh(self, queryset, name, value):
        return queryset.filter(casti__komponenty__komponenty__predmety__druh__in=value)

    def filter_objekty_druh(self, queryset, name, value):
        return queryset.filter(casti__komponenty__komponenty__objekty__druh__in=value)

    def filter_objekty_specifikace(self, queryset, name, value):
        return queryset.filter(casti__komponenty__komponenty__objekty__specifikace__in=value)
    class Meta:
        model = Dokument
        exclude = []

    def __init__(self, *args, **kwargs):
        super(DokumentFilter, self).__init__(*args, **kwargs)
        self.helper = DokumentFilterFormHelper()

    

class DokumentFilterFormHelper(crispy_forms.helper.FormHelper):
    form_method = "GET"
    layout = Layout(
        Div(
            Div(
                Div("ident_cely", css_class="col-sm-2"),
                Div("typ_dokumentu", css_class="col-sm-2"),
                Div("format", css_class="col-sm-2"),
                Div("stav", css_class="col-sm-2"),
                Div("organizace", css_class="col-sm-2"),
                Div("autor", css_class="col-sm-2"),
                Div("rok_vzniku_od", css_class="col-sm-2"),
                Div("rok_vzniku_do", css_class="col-sm-2"),
                Div("duveryhodnost", css_class="col-sm-2"),
                Div("popisne_udaje", css_class="col-sm-4"),
                Div("zeme", css_class="col-sm-2"),
                Div("obdobi", css_class="col-sm-2"),
                Div("areal", css_class="col-sm-2"),
                Div("aktivity", css_class="col-sm-2"),
                css_class="row",
            ),
            Div(
                Div("predmet_druh", css_class="col-sm-2"),
                Div("predmet_specifikace", css_class="col-sm-2"),
                Div("objekt_druh", css_class="col-sm-2"),
                Div("objekt_specifikace", css_class="col-sm-2"),
                css_class="row",
            ),
            Div(
                HTML('<span class="material-icons app-icon-expand">expand_more</span>'),
                HTML(_('<span class="app-divider-label">Výběr podle historie</span>')),
                HTML(_('<hr class="mt-0" />')),
                data_toggle="collapse", href="#historieCollapse", role="button", aria_expanded="false", aria_controls="historieCollapse",
                css_class="col-sm-12 app-btn-show-more collapsed",
            ),
            Div(
                Div("historie_typ_zmeny", css_class="col-sm-2"),
                Div(
                    "historie_datum_zmeny_od", css_class="col-sm-4 app-daterangepicker"
                ),
                Div("historie_uzivatel", css_class="col-sm-4"),
                id="historieCollapse", css_class="collapse row",
            ),
        ),
    )
    form_tag = False
