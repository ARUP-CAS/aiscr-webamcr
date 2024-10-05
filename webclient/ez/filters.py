import logging

import crispy_forms
from arch_z.models import ArcheologickyZaznam
from core.constants import EXTERNI_ZDROJ_RELATION_TYPE
from core.forms import SelectMultipleSeparator
from crispy_forms.layout import HTML, Div, Layout
from dal import autocomplete
from django.db.models import Q
from django.forms import SelectMultiple
from django.utils.translation import gettext_lazy as _
from django_filters import CharFilter, FilterSet, ModelMultipleChoiceFilter, MultipleChoiceFilter
from dokument.filters import HistorieFilter
from heslar.hesla import HESLAR_DOKUMENT_TYP, HESLAR_EXTERNI_ZDROJ_TYP
from heslar.models import Heslar
from historie.models import Historie
from uzivatel.models import Osoba, User

from .models import ExterniZdroj

logger = logging.getLogger(__name__)


class ExterniZdrojFilter(HistorieFilter, FilterSet):
    """
    Třída pro zakladní filtrování externího zdroju a jejich potomků.
    """

    HISTORIE_TYP_ZMENY_STARTS_WITH = "EZ"
    INCLUDE_KAT_TYP_ZMENY = False
    TYP_VAZBY = EXTERNI_ZDROJ_RELATION_TYPE

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

    typ = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_EXTERNI_ZDROJ_TYP),
        label=_("ez.filters.typ.label"),
        field_name="typ",
        widget=SelectMultipleSeparator(),
        distinct=True,
    )

    autori = ModelMultipleChoiceFilter(
        field_name="externizdrojautor__autor",
        label=_("ez.filters.autori.label"),
        widget=autocomplete.ModelSelect2Multiple(url="heslar:osoba-autocomplete"),
        queryset=Osoba.objects.all(),
        distinct=True,
    )

    editori = ModelMultipleChoiceFilter(
        field_name="externizdrojeditor__editor",
        label=_("ez.filters.editori.label"),
        widget=autocomplete.ModelSelect2Multiple(url="heslar:osoba-autocomplete"),
        queryset=Osoba.objects.all(),
        distinct=True,
    )

    typ_dokumentu = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_DOKUMENT_TYP),
        label=_("ez.filters.typDokumentu.label"),
        widget=SelectMultipleSeparator(),
        distinct=True,
    )

    organizace = CharFilter(
        label=_("ez.filters.organizace.label"),
    )

    popisne_udaje = CharFilter(
        label=_("ez.filters.popisneUdaje.label"),
        method="filter_popisne_udaje",
    )

    historie_typ_zmeny = MultipleChoiceFilter(
        choices=list(filter(lambda x: x[0].startswith("EZ"), Historie.CHOICES)),
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

    def filter_queryset(self, queryset):
        logger.debug("ez.filters.ExterniZdrojFilter.filter_queryset.start")
        historie = self._get_history_subquery()
        queryset = super(ExterniZdrojFilter, self).filter_queryset(queryset)
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
        logger.debug("ez.filters.ExterniZdrojFilter.filter_queryset.end", extra={"query": str(queryset.query)})
        return queryset

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
        user: User = kwargs.get("request").user
        super(ExterniZdrojFilter, self).__init__(*args, **kwargs)
        self.set_filter_fields(user)
        self.helper = ExterniZdrojFilterFormHelper()


class ExterniZdrojFilterFormHelper(crispy_forms.helper.FormHelper):
    """
    Třída pro správne zobrazení filtru.
    """

    form_method = "GET"

    def __init__(self, form=None):
        history_divider = "<span class='app-divider-label'>%(translation)s</span>" % {
            "translation": _("ez.filters.history.divider.label")
        }
        souvis_divider = "<span class='app-divider-label'>%(translation)s</span>" % {
            "translation": _("ez.filters.souvisejiciZaznamy.divider.label")
        }
        self.layout = Layout(
            Div(
                Div(
                    Div("ident_cely", css_class="col-sm-2"),
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
                    HTML(souvis_divider),
                    HTML('<hr class="mt-0" />'),
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
        self.form_tag = False
        super().__init__(form)
