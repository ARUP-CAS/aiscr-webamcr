import logging

import crispy_forms
from dal import autocomplete
from crispy_forms.layout import Div, Layout, HTML
from django.db.models import Q
from django.forms import Select, SelectMultiple
from django.utils.translation import gettext as _
from django_filters import (
    CharFilter,
    ModelMultipleChoiceFilter,
    MultipleChoiceFilter,
    DateFromToRangeFilter,
)
from django_filters.widgets import DateRangeWidget

from heslar.hesla import (
    HESLAR_AKTIVITA,
    HESLAR_AREAL,
    HESLAR_AREAL_KAT,
    HESLAR_DJ_TYP,
    HESLAR_JISTOTA_URCENI,
    HESLAR_LOKALITA_DRUH,
    HESLAR_LOKALITA_TYP,
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
    HESLAR_STAV_DOCHOVANI,
)
from heslar.models import Heslar
from historie.models import Historie
from projekt.filters import KatastrFilter
from arch_z.filters import ArchZaznamFilter
from .models import Lokalita
from arch_z.models import ArcheologickyZaznam
from uzivatel.models import User
from dokument.filters import HistorieFilter
from heslar.views import heslar_12

logger = logging.getLogger(__name__)


class LokalitaFilter(ArchZaznamFilter):
    typ_lokality = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_LOKALITA_TYP),
        label=_("lokalita.filter.typLokality.label"),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )

    druh_lokality = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_LOKALITA_DRUH),
        label=_("lokalita.filter.druhLokality.label"),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )

    zachovalost_lokality = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_STAV_DOCHOVANI),
        label=_("lokalita.filter.zachovalostLokality.label"),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )

    jistota_lokality = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_JISTOTA_URCENI),
        label=_("lokalita.filter.jistotaLokality.label"),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
        distinct=True,
    )

    def filter_popisne_udaje(self, queryset, name, value):
        return queryset.filter(
            Q(nazev__icontains=value)
            | Q(popis__icontains=value)
            | Q(poznamka__icontains=value)
            | Q(archeologicky_zaznam__uzivatelske_oznaceni__icontains=value)
        ).distinct()

    class Meta:
        model = Lokalita
        exclude = (
            "nazev",
            "popis",
            "poznamka",
        )

    def __init__(self, *args, **kwargs):
        super(LokalitaFilter, self).__init__(*args, **kwargs)
        self.helper = LokalitaFilterFormHelper()


class LokalitaFilterFormHelper(crispy_forms.helper.FormHelper):
    form_method = "GET"
    dj_pian_divider = u"<span class='app-divider-label'>%(translation)s</span>" % {
        "translation": _(u"lokalita.filter.djPian.divider.label")
    }
    history_divider = u"<span class='app-divider-label'>%(translation)s</span>" % {
        "translation": _(u"lokalita.filter.history.divider.label")
    }
    komponenta_divider = u"<span class='app-divider-label'>%(translation)s</span>" % {
        "translation": _(u"lokalita.filter.komponenta.divider.label")
    }
    dok_divider = u"<span class='app-divider-label'>%(translation)s</span>" % {
        "translation": _(u"lokalita.filter.dok.divider.label")
    }
    layout = Layout(
        Div(
            Div(
                Div("ident_cely", css_class="col-sm-2"),
                Div("typ_lokality", css_class="col-sm-2"),
                Div("druh_lokality", css_class="col-sm-2"),
                Div("zachovalost_lokality", css_class="col-sm-2"),
                Div("jistota_lokality", css_class="col-sm-2"),
                Div("stav", css_class="col-sm-2"),
                Div("katastr", css_class="col-sm-2"),
                Div("okres", css_class="col-sm-2"),
                Div("kraj", css_class="col-sm-2"),
                Div("popisne_udaje", css_class="col-sm-4"),
                Div("pristupnost", css_class="col-sm-2"),
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
                HTML(dj_pian_divider),
                HTML(_('<hr class="mt-0" />')),
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
                HTML(_('<hr class="mt-0" />')),
                data_toggle="collapse",
                href="#KomponentaCollapse",
                role="button",
                aria_expanded="false",
                aria_controls="KomponentaCollapse",
                css_class="col-sm-12 app-btn-show-more collapsed",
            ),
            Div(
                Div("komponenta_obdobi", css_class="col-sm-2"),
                Div("komponenta_datace", css_class="col-sm-2"),
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
                HTML(dok_divider),
                HTML(_('<hr class="mt-0" />')),
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
    form_tag = False
