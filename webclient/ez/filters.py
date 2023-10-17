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
)

from core.constants import ZAPSANI_EXT_ZD
from heslar.hesla import (
    HESLAR_DOKUMENT_TYP,
    HESLAR_EXTERNI_ZDROJ_TYP,
)
from heslar.models import Heslar
from dokument.filters import HistorieFilter
from historie.models import Historie
from core.forms import SelectMultipleSeparator
from arch_z.models import ArcheologickyZaznam
from .models import ExterniZdroj
from uzivatel.models import Organizace, Osoba, User

logger = logging.getLogger(__name__)


class ExterniZdrojFilter(HistorieFilter):
    """
    Třída pro zakladní filtrování externího zdroju a jejich potomků.
    """
    stav = MultipleChoiceFilter(
        choices=ExterniZdroj.STATES,
        field_name="stav",
        label=_("ez.filters.stav.label"),
        widget=SelectMultipleSeparator(),
        distinct=True,
    )

    ident_cely = CharFilter(
        field_name="ident_cely",
        lookup_expr="icontains",
        label=_("ez.filters.identCely.label"),
        distinct=True,
    )

    sysno = CharFilter(
        label=_("ez.filters.sysno.label"),
        lookup_expr="icontains",
        distinct=True,
    )

    typ = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_EXTERNI_ZDROJ_TYP),
        label=_("ez.filters.typ.label"),
        field_name="typ",
        widget=SelectMultipleSeparator(),
        distinct=True,
    )

    autori = MultipleChoiceFilter(
        field_name="externizdrojautor__autor__id",
        label=_("ez.filters.autori.label"),
        choices=Osoba.objects.all().values_list("id", "vypis_cely"),
        widget=autocomplete.Select2Multiple(
            url="heslar:osoba-autocomplete-choices",
        ),
        distinct=True,
    )

    editori = MultipleChoiceFilter(
        field_name="externizdrojeditor__editor__id",
        label=_("ez.filters.editori.label"),
        choices=Osoba.objects.all().values_list("id", "vypis_cely"),
        widget=autocomplete.Select2Multiple(
            url="heslar:osoba-autocomplete-choices",
        ),
        distinct=True,
    )

    typ_dokumentu = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_DOKUMENT_TYP),
        label=_("ez.filters.typDokumentu.label"),
        widget=SelectMultipleSeparator(),
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
        label=_("ez.filters.popisneUdaje.label"),
        method="filter_popisne_udaje",
    )

    historie_typ_zmeny = MultipleChoiceFilter(
        choices=filter(lambda x: x[0].startswith("EZ"), Historie.CHOICES),
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
        method="filter_akce_ident",
        label=_("ez.filters.idAkce.label"),
        distinct=True,
    )

    lokalita_ident = CharFilter(
        method="filter_lokalita_ident",
        label=_("ez.filters.idLokalita.label"),
        distinct=True,
    )

    vlastnik = ModelMultipleChoiceFilter(
        queryset=User.objects.select_related("organizace").all(),
        field_name="historie__historie__uzivatel",
        label="Vlastník",
        widget=SelectMultipleSeparator(),
    )

    historie_zapsal_uzivatel_organizace = CharFilter(
        label=_("arch_z.filters.ExterniZdrojFilter.filter_historie_zapsal_uzivatel_organizace.label"),
        method="filter_historie_zapsal_uzivatel_organizace",
        distinct=True,
    )

    def filter_popisne_udaje(self, queryset, name, value):
        """
        Metóda pro filtrování podle názvu, edice, sborníku, časopisu, isbn, issn, roku vydání a poznámek.
        """
        return queryset.filter(
            Q(nazev__icontains=value)
            | Q(edice_rada__icontains=value)
            | Q(sbornik_nazev__icontains=value)
            | Q(casopis_denik_nazev__icontains=value)
            | Q(isbn__icontains=value)
            | Q(issn__icontains=value)
            | Q(poznamka__icontains=value)
            | Q(rok_vydani_vzniku__icontains=value)
        )

    def filter_akce_ident(self, queryset, name, value):
        """
        Metóda pro filtrování podle identu celý akce.
        """
        return queryset.filter(
            externi_odkazy_zdroje__archeologicky_zaznam__ident_cely__icontains=value,
            externi_odkazy_zdroje__archeologicky_zaznam__typ_zaznamu=ArcheologickyZaznam.TYP_ZAZNAMU_AKCE,
        )

    def filter_lokalita_ident(self, queryset, name, value):
        """
        Metóda pro filtrování podle identu celý lokality.
        """
        return queryset.filter(
            externi_odkazy_zdroje__archeologicky_zaznam__ident_cely__icontains=value,
            externi_odkazy_zdroje__archeologicky_zaznam__typ_zaznamu=ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA,
        )

    def filter_historie_zapsal_uzivatel_organizace(self, queryset, name, value):
        historie_query = Historie.objects.filter(vazba__externizdroj__isnull=False).filter(typ_zmeny=ZAPSANI_EXT_ZD)\
            .filter(uzivatel__organizace=int(value))
        d_ids = [x.vazba.externizdroj.pk for x in historie_query]
        return queryset.filter(pk__in=d_ids).distinct()

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
            "rok_vydani_vzniku",
        )

    def __init__(self, *args, **kwargs):
        super(ExterniZdrojFilter, self).__init__(*args, **kwargs)
        self.helper = ExterniZdrojFilterFormHelper()


class ExterniZdrojFilterFormHelper(crispy_forms.helper.FormHelper):
    """
    Třída pro správne zobrazení filtru.
    """
    form_method = "GET"
    history_divider = u"<span class='app-divider-label'>%(translation)s</span>" % {
        "translation": _(u"ez.filters.history.divider.label")
    }
    souvis_divider = u"<span class='app-divider-label'>%(translation)s</span>" % {
        "translation": _(u"ez.filters.souvisejiciZaznamy.divider.label")
    }
    layout = Layout(
        Div(
            Div(
                Div("ident_cely", css_class="col-sm-2"),
                Div("sysno", css_class="col-sm-2"),
                Div("typ", css_class="col-sm-2"),
                Div("stav", css_class="col-sm-2"),
                Div("autori", css_class="col-sm-2"),
                Div("editori", css_class="col-sm-2"),
                Div("typ_dokumentu", css_class="col-sm-2"),
                Div("organizace", css_class="col-sm-2"),
                Div("popisne_udaje", css_class="col-sm-8"),
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
