import logging

import crispy_forms
from dal import autocomplete
from crispy_forms.layout import Div, Layout, HTML
from django.db.models import Q
from django.forms import SelectMultiple
from django.utils.translation import gettext as _
from django_filters import (
    CharFilter,
    ModelMultipleChoiceFilter,
    MultipleChoiceFilter,
    DateFromToRangeFilter,
)
from django_filters.widgets import DateRangeWidget

from heslar.hesla import (
    HESLAR_DOKUMENT_TYP,
    HESLAR_EXTERNI_ZDROJ_TYP,
)
from heslar.models import Heslar
from dokument.filters import HistorieFilter
from historie.models import Historie
from .models import ExterniZdroj
from uzivatel.models import Organizace, Osoba, User

logger = logging.getLogger(__name__)


class ExterniZdrojFilter(HistorieFilter):
    stav = MultipleChoiceFilter(
        choices=ExterniZdroj.STATES,
        field_name="stav",
        label=_("externiZdroj.filter.stav.label"),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )

    ident_cely = CharFilter(
        field_name="ident_cely",
        lookup_expr="icontains",
        label=_("externiZdroj.filter.identCely.label"),
        distinct=True,
    )

    sysno = CharFilter(
        label=_("externiZdroj.filter.sysno.label"),
        lookup_expr="icontains",
        distinct=True,
    )

    typ = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_EXTERNI_ZDROJ_TYP),
        label=_("externiZdroj.filter.typ.label"),
        field_name="sysno",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )

    autori = MultipleChoiceFilter(
        field_name="externizdrojautor__autor__id",
        label=_("externiZdroj.filter.autori.label"),
        choices=Osoba.objects.all().values_list("id", "vypis_cely"),
        widget=autocomplete.Select2Multiple(
            url="heslar:osoba-autocomplete-choices",
        ),
        distinct=True,
    )

    editori = MultipleChoiceFilter(
        field_name="externizdrojeditor__edito__id",
        label=_("externiZdroj.filter.autori.label"),
        choices=Osoba.objects.all().values_list("id", "vypis_cely"),
        widget=autocomplete.Select2Multiple(
            url="heslar:osoba-autocomplete-choices",
        ),
        distinct=True,
    )

    rok_vydani_vzniku = DateFromToRangeFilter(
        field_name="rok_vydani_vzniku",
        label=_("externiZdroj.filter.rokVydaniVzniku.label"),
        widget=DateRangeWidget(attrs={"type": "date", "max": "2100-12-31"}),
        distinct=True,
    )

    typ_dokumentu = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_DOKUMENT_TYP),
        label=_("externiZdroj.filter.typDokumentu.label"),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )

    organizace = ModelMultipleChoiceFilter(
        queryset=Organizace.objects.all(),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    popisne_udaje = CharFilter(
        label=_("externiZdroj.filter.popisneUdaje.label"),
        method="filter_popisne_udaje",
    )

    historie_typ_zmeny = MultipleChoiceFilter(
        choices=filter(lambda x: x[0].endswith("EXT_ZD"), Historie.CHOICES),
        label=_("historie.filter.typZmeny.label"),
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

    akce_ident = CharFilter(
        field_name="externi_zdroj__externi_odkazy__archeologicky_zaznam__ident_cely",
        lookup_expr="icontains",
        label=_("externiZdroj.filter.idAkce.label"),
        distinct=True,
    )

    lokalita_ident = CharFilter(
        field_name="externi_zdroj__externi_odkazy__archeologicky_zaznam__ident_cely",
        lookup_expr="icontains",
        label=_("externiZdroj.filter.idLokalita.label"),
        distinct=True,
    )

    vlastnik = ModelMultipleChoiceFilter(
        queryset=User.objects.select_related("organizace").all(),
        field_name="historie__historie__uzivatel",
        label="Vlastník",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )

    def filter_popisne_udaje(self, queryset, name, value):
        return queryset.filter(
            Q(nazev__icontains=value)
            | Q(edice_rada__icontains=value)
            | Q(sbornik_nazev__icontains=value)
            | Q(casopis_denik_nazev__icontains=value)
            | Q(isbn__icontains=value)
            | Q(issn__icontains=value)
            | Q(poznamka__icontains=value)
        )

    class Meta:
        model = ExterniZdroj
        exclude = (
            "nazev",
            "edice_rada",
            "sbornik_nazev",
            "casopis_denik_nazev",
            "casopis_rocnik",
            "misto",
            "vydavatel",
            "paginace_titulu",
            "isbn",
            "issn",
            "link",
            "datum_rd",
        )

    def __init__(self, *args, **kwargs):
        super(ExterniZdrojFilter, self).__init__(*args, **kwargs)
        self.helper = ExterniZdrojFilterFormHelper()


class ExterniZdrojFilterFormHelper(crispy_forms.helper.FormHelper):
    form_method = "GET"
    history_divider = u"<span class='app-divider-label'>%(translation)s</span>" % {
        "translation": _(u"externiZdroj.filter.history.divider.label")
    }
    souvis_divider = u"<span class='app-divider-label'>%(translation)s</span>" % {
        "translation": _(u"externiZdroj.filter.souvisejiciZaznamy.divider.label")
    }
    layout = Layout(
        Div(
            Div(
                Div("ident_cely", css_class="col-sm-2"),
                Div("sysno", css_class="col-sm-2"),
                Div("typ", css_class="col-sm-2"),
                Div("stav", css_class="col-sm-2"),
                Div(css_class="col-sm-4"),
                Div("autori", css_class="col-sm-2"),
                Div("editori", css_class="col-sm-2"),
                Div("rok_vydani_vzniku", css_class="col-sm-4 app-daterangepicker"),
                Div("typ_dokumentu", css_class="col-sm-2"),
                Div("organizace", css_class="col-sm-2"),
                css_class="row",
            ),
            Div(
                HTML('<span class="material-icons app-icon-expand">expand_more</span>'),
                HTML(history_divider),
                HTML(_('<hr class="mt-0" />')),
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
                Div("historie_uzivatel", css_class="col-sm-4"),
                id="historieCollapse",
                css_class="collapse row",
            ),
            Div(
                HTML('<span class="material-icons app-icon-expand">expand_more</span>'),
                HTML(souvis_divider),
                HTML(_('<hr class="mt-0" />')),
                data_toggle="collapse",
                href="#SouvisCollapse",
                role="button",
                aria_expanded="false",
                aria_controls="SouvisCollapse",
                css_class="col-sm-12 app-btn-show-more collapsed",
            ),
            Div(
                Div("akce_ident", css_class="col-sm-2"),
                Div("lokalita_ident", css_class="col-sm-2"),
                id="SouvisCollapse",
                css_class="collapse row",
            ),
        ),
    )
    form_tag = False
