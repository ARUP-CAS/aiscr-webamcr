import logging

import crispy_forms
from crispy_forms.layout import Div, Layout, HTML
from django.db.models import Q, OuterRef, Subquery, F
from django.utils.translation import gettext as _
from django_filters import (
    ModelMultipleChoiceFilter, CharFilter,
)

from core.constants import ZAPSANI_AZ
from heslar.hesla import (
    HESLAR_JISTOTA_URCENI,
    HESLAR_LOKALITA_DRUH,
    HESLAR_LOKALITA_TYP,
    HESLAR_STAV_DOCHOVANI,
)
from heslar.models import Heslar
from arch_z.filters import ArchZaznamFilter
from core.forms import SelectMultipleSeparator
from historie.models import Historie
from uzivatel.models import Organizace
from .models import Lokalita

logger = logging.getLogger(__name__)


class LokalitaFilter(ArchZaznamFilter):
    """
    Třída pro zakladní filtrování lokality a jejich potomků.
    """
    typ_lokality = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_LOKALITA_TYP),
        label=_("lokalita.filters.typLokality.label"),
        widget=SelectMultipleSeparator(),
        distinct=True,
    )

    druh_lokality = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_LOKALITA_DRUH),
        label=_("lokalita.filters.druhLokality.label"),
        field_name="druh",
        widget=SelectMultipleSeparator(),
        distinct=True,
    )

    zachovalost_lokality = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_STAV_DOCHOVANI),
        label=_("lokalita.filters.zachovalostLokality.label"),
        field_name="zachovalost",
        widget=SelectMultipleSeparator(),
        distinct=True,
    )

    jistota_lokality = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_JISTOTA_URCENI),
        label=_("lokalita.filters.jistotaLokality.label"),
        field_name="jistota",
        widget=SelectMultipleSeparator(),
        distinct=True,
    )

    historie_zapsal_uzivatel_organizace = ModelMultipleChoiceFilter(
        queryset=Organizace.objects.all(),
        field_name="lokalita__archeologicky_zaznam__historie__historie__uzivatel",
        label=_("lokalita.filters.LokalitaFilter.filter_historie_zapsal_uzivatel_organizace.label"),
        widget=SelectMultipleSeparator(),
        method="filter_historie_zapsal_uzivatel_organizace",
        distinct=True,
    )

    def filter_popisne_udaje(self, queryset, name, value):
        """
        Metóda pro filtrování podle názvu, popisu, uživatelského označení a poznámek.
        """
        return queryset.filter(
            Q(nazev__icontains=value)
            | Q(popis__icontains=value)
            | Q(poznamka__icontains=value)
            | Q(archeologicky_zaznam__uzivatelske_oznaceni__icontains=value)
        ).distinct()

    def filter_historie_zapsal_uzivatel_organizace(self, queryset, name, value):
        if value:
            historie_subquery = Historie.objects.filter(vazba__archeologickyzaznam__isnull=False)\
                .filter(typ_zmeny=ZAPSANI_AZ)\
                .filter(vazba__archeologickyzaznam__lokalita=OuterRef("pk"))\
                .filter(uzivatel__organizace__in=value)\
                .annotate(lokalita_ids=F("vazba__archeologickyzaznam__lokalita"))
            return queryset.annotate(lokalita_ids=Subquery(historie_subquery.values("lokalita_ids")))\
                .filter(pk__in=F("lokalita_ids")).distinct()
        else:
            return queryset


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
    """
    Třída pro správne zobrazení filtru.
    """
    form_method = "GET"
    dj_pian_divider = u"<span class='app-divider-label'>%(translation)s</span>" % {
        "translation": _(u"lokalita.filters.djPian.divider.label")
    }
    history_divider = u"<span class='app-divider-label'>%(translation)s</span>" % {
        "translation": _(u"lokalita.filters.history.divider.label")
    }
    komponenta_divider = u"<span class='app-divider-label'>%(translation)s</span>" % {
        "translation": _(u"lokalita.filters.komponenta.divider.label")
    }
    dok_divider = u"<span class='app-divider-label'>%(translation)s</span>" % {
        "translation": _(u"lokalita.filters.dok.divider.label")
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
                Div("historie_zapsal_uzivatel_organizace", css_class="col-sm-3"),
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
    form_tag = False
