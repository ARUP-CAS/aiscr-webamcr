import logging
import operator
from functools import reduce

import crispy_forms
from core.constants import DOKUMENT_RELATION_TYPE, ROLE_ADMIN_ID, ROLE_ARCHIVAR_ID, ZMENA_KATASTRU
from core.filters import GeomWithinFilterMixin
from core.forms import SelectMultipleSeparator
from core.models import Soubor
from core.widgets import AutocompleteModelSelect2Multiple
from crispy_forms.layout import HTML, Div, Layout
from django.db import models
from django.db.models import Exists, OuterRef, Q
from django.forms import NumberInput, SelectMultiple
from django.utils.translation import gettext_lazy as _
from django_filters import (
    CharFilter,
    DateFromToRangeFilter,
    FilterSet,
    ModelMultipleChoiceFilter,
    MultipleChoiceFilter,
    NumberFilter,
    RangeFilter,
)
from django_filters.widgets import DateRangeWidget
from dokument.forms import DokumentFilterForm
from dokument.models import Dokument, DokumentCast, Tvar
from heslar.hesla import (
    HESLAR_AKTIVITA,
    HESLAR_AREAL,
    HESLAR_AREAL_KAT,
    HESLAR_DOHLEDNOST,
    HESLAR_DOKUMENT_FORMAT,
    HESLAR_DOKUMENT_MATERIAL,
    HESLAR_DOKUMENT_NAHRADA,
    HESLAR_DOKUMENT_RADA,
    HESLAR_DOKUMENT_TYP,
    HESLAR_DOKUMENT_ULOZENI,
    HESLAR_DOKUMENT_ZACHOVALOST,
    HESLAR_JAZYK,
    HESLAR_LETFOTO_TVAR,
    HESLAR_LETISTE,
    HESLAR_LICENCE,
    HESLAR_OBDOBI,
    HESLAR_OBDOBI_KAT,
    HESLAR_OBJEKT_DRUH,
    HESLAR_OBJEKT_DRUH_KAT,
    HESLAR_OBJEKT_SPECIFIKACE,
    HESLAR_OBJEKT_SPECIFIKACE_KAT,
    HESLAR_POCASI,
    HESLAR_POSUDEK_TYP,
    HESLAR_POSUDEK_TYP_KAT,
    HESLAR_PREDMET_DRUH,
    HESLAR_PREDMET_DRUH_KAT,
    HESLAR_PREDMET_SPECIFIKACE,
    HESLAR_PRISTUPNOST,
    HESLAR_UDALOST_TYP,
    HESLAR_ZEME,
)
from heslar.hesla_dynamicka import MODEL_3D_DOKUMENT_FORMATS, MODEL_3D_DOKUMENT_TYPES
from heslar.models import Heslar, RuianKatastr
from heslar.views import heslar_12
from historie.models import Historie
from komponenta.models import Komponenta
from nalez.models import NalezObjekt
from neidentakce.models import NeidentAkce
from uzivatel.models import Organizace, Osoba, User

logger = logging.getLogger(__name__)


class SouborTypFilter(MultipleChoiceFilter):
    """Implementuje komponentu ``SouborTypFilter`` v rámci aplikace."""

    @property
    def field(self):
        """
        Vrací dynamicky generované pole s volbami typů souborů z aktuální databáze.

        Nabízí pouze typy souborů navázaných na dokument – volby, které nemá žádný
        dokument, by ve filtru vracely prázdný výsledek. Dotaz vychází z modelu
        ``Soubor`` (místo joinu od ``Dokument``), což je rychlejší při shodném výsledku.

        :return: FormField s volbami z databáze.
        """
        qs = (
            Soubor.objects.filter(vazba__dokument_souboru__isnull=False)
            .values_list("mimetype", flat=True)
            .distinct()
            .order_by("mimetype")
        )
        self.extra["choices"] = [(o, o) for o in qs if o is not None]
        return super().field


class HistorieFilter(FilterSet):
    """
    Třída pro základní filtrování historie. Třída je děděná v jednotlivých filtracích záznamů.
    """

    HISTORIE_TYP_ZMENY_STARTS_WITH = None
    INCLUDE_KAT_TYP_ZMENY = True
    TYP_VAZBY = None

    def set_filter_fields(self, user):
        """
        Nastaví filter fields.

        :param user: Parametr ``user`` pracuje se s atributy ``hlavni_role``, ovlivňuje větvení podmínek.
        """
        if user.hlavni_role.pk in (ROLE_ADMIN_ID, ROLE_ARCHIVAR_ID):
            self.filters["historie_uzivatel"] = ModelMultipleChoiceFilter(
                queryset=User.objects.all(),
                field_name="historie__historie__uzivatel",
                label=_("dokument.filters.historieFilter.historieUzivatel.label"),
                widget=AutocompleteModelSelect2Multiple(url="uzivatel:uzivatel-autocomplete"),
                distinct=True,
            )
        else:
            self.filters["historie_uzivatel"] = ModelMultipleChoiceFilter(
                queryset=User.objects.all(),
                field_name="historie__historie__uzivatel",
                label=_("dokument.filters.historieFilter.historieUzivatel.label"),
                widget=AutocompleteModelSelect2Multiple(url="uzivatel:uzivatel-autocomplete-public"),
                distinct=True,
            )
        self.filters["historie_typ_zmeny"] = MultipleChoiceFilter(
            choices=list(
                filter(
                    lambda x: (
                        x[0].startswith(self.HISTORIE_TYP_ZMENY_STARTS_WITH)
                        or (self.INCLUDE_KAT_TYP_ZMENY and x[0] == ZMENA_KATASTRU)
                    )
                    and not (self.HISTORIE_TYP_ZMENY_STARTS_WITH == "P" and x[0].startswith("PI")),
                    Historie.CHOICES,
                )
            ),
            label=_("dokument.filters.historieFilter.historieTypZmeny.label"),
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
        self.filters["historie_datum_zmeny_od"] = DateFromToRangeFilter(
            label=_("dokument.filters.historieFilter.historieDatumZmeny.label"),
            field_name="historie__historie__datum_zmeny",
            widget=DateRangeWidget(attrs={"type": "text", "max": "2100-12-31"}),
            distinct=True,
        )
        self.filters["historie_uzivatel_organizace"] = ModelMultipleChoiceFilter(
            queryset=Organizace.objects.all(),
            field_name="historie__historie__uzivatel__organizace",
            label=_("ez.filters.historieFilter.filter_historie_uzivatel_organizace.label"),
            widget=SelectMultipleSeparator(),
            distinct=True,
        )
        self.filters["historie_poznamka"] = CharFilter(
            field_name="historie__historie__poznamka",
            lookup_expr="icontains",
            label=_("dokument.filters.historieFilter.historiePoznamka.label"),
            distinct=True,
        )

    def _get_history_subquery(self):
        """
        Vrací history subquery.

        :return: Načtená data odpovídající zadaným vstupům.
        """
        logger.debug("dokument.filters.HistorieFilter._get_history_subquery.start")
        uzivatel_organizace = self.form.cleaned_data.pop("historie_uzivatel_organizace", None)
        zmena = self.form.cleaned_data.pop("historie_typ_zmeny", None)
        uzivatel = self.form.cleaned_data.pop("historie_uzivatel", None)
        datum = self.form.cleaned_data.pop("historie_datum_zmeny_od", None)
        poznamka = self.form.cleaned_data.pop("historie_poznamka", None)

        if not uzivatel_organizace and not zmena and not uzivatel and not datum and not poznamka:
            return

        filtered_fields = {"typ_vazby": self.TYP_VAZBY}
        if uzivatel:
            filtered_fields["uzivatel"] = uzivatel
            self.filters.pop("historie_uzivatel")
        if uzivatel_organizace:
            filtered_fields["uzivatel_organizace"] = uzivatel_organizace
            self.filters.pop("historie_uzivatel_organizace")
        if zmena:
            filtered_fields["typ_zmeny"] = zmena
            self.filters.pop("historie_typ_zmeny")
        if datum and datum.start:
            filtered_fields["datum_zmeny__gte"] = datum.start
            self.filters.pop("historie_datum_zmeny_od")
        if datum and datum.stop:
            filtered_fields["datum_zmeny__lte"] = datum.stop
        if poznamka:
            filtered_fields["poznamka__icontains"] = poznamka
            self.filters.pop("historie_poznamka")
        return filtered_fields

    def filter_ident_cely(self, queryset, name, value):
        """
        Metoda pro filtrování podle identu dokumentu/projektu/EZ, ale i dočasného.

        :param queryset: Parametr ``queryset`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
        :param name: Parametr ``name`` nepoužito.
        :param value: Parametr ``value`` ovlivňuje větvení podmínek, předává se do volání ``filter()``.

            :return: Vrací filtrovaný ``queryset`` podle ``ident_cely`` nebo poznámky z historie.
        """
        if not value:
            return queryset

        # 1) primárně hledat v Projekt.ident_cely
        qs = queryset.filter(ident_cely__icontains=value)
        if qs.exists():  # jen když něco najde, tak tím skončit
            return qs

        # 2) fallback: hledat v Historie.poznamka (přes vazbu Projekt.historie -> HistorieVazby -> Historie)
        return queryset.filter(
            historie__historie__poznamka__icontains=value,
        ).distinct()


class Model3DFilter(GeomWithinFilterMixin, HistorieFilter, FilterSet):
    """
    Třída pro základní filtrování modelu 3D a jejich potomků.
    """

    TYP_VAZBY = DOKUMENT_RELATION_TYPE
    INCLUDE_KAT_TYP_ZMENY = False
    geom_filter_lookup = "extra_data__geom"
    HISTORIE_TYP_ZMENY_STARTS_WITH = "D"

    ident_cely = CharFilter(
        method="filter_ident_cely", distinct=True, label=_("dokument.filters.dokumentFilter.ident_cely.label")
    )

    doi = CharFilter(lookup_expr="icontains", label=_("dokument.filters.dokumentFilter.doi.label"))

    typ_dokumentu = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_DOKUMENT_TYP).filter(id__in=MODEL_3D_DOKUMENT_TYPES),
        label=_("dokument.filters.dokumentFilter.typDokumentu.label"),
        field_name="typ_dokumentu",
        widget=SelectMultipleSeparator(),
    )

    format = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_DOKUMENT_FORMAT).filter(id__in=MODEL_3D_DOKUMENT_FORMATS),
        label=_("dokument.filters.dokumentFilter.format.label"),
        field_name="extra_data__format",
        widget=SelectMultipleSeparator(),
    )

    stav = MultipleChoiceFilter(
        choices=Dokument.STATES,
        label=_("dokument.filters.dokumentFilter.stav.label"),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
    )

    organizace = ModelMultipleChoiceFilter(
        queryset=Organizace.objects.all(),
        label=_("dokument.filters.dokumentFilter.organizace.label"),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
    )

    autor = ModelMultipleChoiceFilter(
        label=_("dokument.filters.dokumentFilter.autor.label"),
        field_name="autori",
        widget=AutocompleteModelSelect2Multiple(url="heslar:osoba-autocomplete"),
        queryset=Osoba.objects.all(),
    )

    rok_vzniku = RangeFilter(
        label=_("dokument.filters.dokumentFilter.rok_vzniku.label"),
        method="filter_roky",
        widget=DateRangeWidget(
            attrs={
                "max": "2100-12-31",
                "class": "textinput textInput dateinput form-control date_roky",
            }
        ),
        distinct=True,
        field_name="rok_vzniku",
    )

    duveryhodnost = NumberFilter(
        field_name="extra_data__duveryhodnost",
        label=_("dokument.filters.dokumentFilter.duverihodnost.label"),
        lookup_expr="gte",
        widget=NumberInput(attrs={"min": "0", "max": "100"}),
        distinct=True,
    )
    popisne_udaje = CharFilter(
        label=_("dokument.filters.dokumentFilter.popisneUdaje.label"),
        method="filter_popisne_udaje",
    )

    zeme = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_ZEME),
        field_name="extra_data__zeme",
        label=_("dokument.filters.dokumentFilter.zeme.label"),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    aktivity = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(
            nazev_heslare=HESLAR_AKTIVITA
        ),  # Nezdá se mi použití obou hesel – platí i pro vytvoření a úpravu.
        field_name="casti__komponenty__komponenty__komponentaaktivita__aktivita",
        label=_("dokument.filters.dokumentFilter.aktivity.label"),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    predmet_specifikace = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(
            nazev_heslare=HESLAR_PREDMET_SPECIFIKACE
        ),  # Nezdá se mi použití obou hesel – platí i pro vytvoření a úpravu.
        field_name="casti__komponenty__komponenty__predmety__specifikace",
        label=_("dokument.filters.dokumentFilter.predmetSpecifikace.label"),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    licence = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_LICENCE),
        label=_("dokument.filters.dokumentFilter.Licence.label"),
        field_name="licence",
        widget=SelectMultipleSeparator(),
    )

    def filter_queryset(self, queryset):
        """
        Filtruje queryset. v aplikaci.

        :param queryset: Parametr ``queryset`` předává se do volání ``filter_queryset()``, pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.

            :return: Vrací proměnná ``queryset``.
        """
        logger.debug("dokument.filters.AkceFilter.filter_queryset.start")
        historie = self._get_history_subquery()
        queryset = super(Model3DFilter, self).filter_queryset(queryset)
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
            if "poznamka__icontains" in historie:
                queryset_history &= Q(historie__historie__poznamka__icontains=historie["poznamka__icontains"])
            queryset = queryset.filter(queryset_history).distinct()

        return queryset

    def filter_popisne_udaje(self, queryset, name, value):
        """
        Filtruje modely 3D podle popisu, poznámky, odkazu a textů v komponentách.

        :param queryset: QuerySet modelů 3D k filtrování.
        :param name: Jméno pole pro filtrování.
        :param value: Hodnota pro vyhledávání.
        :return: Filtrovaný QuerySet.
        """
        return queryset.filter(
            Q(oznaceni_originalu__icontains=value)
            | Q(popis__icontains=value)
            | Q(poznamka__icontains=value)
            | Q(extra_data__odkaz__icontains=value)
            | Q(casti__komponenty__komponenty__objekty__poznamka__icontains=value)
            | Q(casti__komponenty__komponenty__predmety__poznamka__icontains=value)
        ).distinct()

    def filter_roky(self, queryset, name, value):
        """
        Filtruje modely podle roku vzniku.

        :param queryset: QuerySet modelů k filtrování.
        :param name: Jméno pole pro filtrování.
        :param value: RangeField s start/stop roky.
        :return: Filtrovaný QuerySet.
        """
        if value:
            if value.start is not None and value.stop is not None:
                self.lookup_expr = "range"
                value = (value.start, value.stop)
            elif value.start is not None:
                self.lookup_expr = "gte"
                value = value.start
            elif value.stop is not None:
                self.lookup_expr = "lte"
                value = value.stop
        lookup1 = "%s__%s" % (
            name,
            self.lookup_expr,
        )
        return queryset.filter(**{lookup1: value}).distinct()

    def filter_roky_range(self, queryset, name, value):
        """
        Filtruje modely podle rozsahu let.

        :param queryset: QuerySet modelů k filtrování.
        :param name: Jméno pole pro filtrování (tuple name).
        :param value: RangeField s start/stop roky.
        :return: Filtrovaný QuerySet.
        """
        if value:
            if value.start is not None:
                lookup1 = "%s__%s" % (
                    name[0],
                    "gte",
                )
                value1 = value.start
                queryset = queryset.filter(**{lookup1: value1}).distinct()
            if value.stop is not None:
                lookup2 = "%s__%s" % (
                    name[1],
                    "lte",
                )
                value2 = value.stop
                queryset = queryset.filter(**{lookup2: value2}).distinct()
        return queryset

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        model = Dokument
        exclude = []
        form = DokumentFilterForm

    def __init__(self, *args, **kwargs):
        """
        Inicializuje instanci třídy.

        :param args: Parametr ``args`` se předává do volání ``__init__()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``, pracuje se s atributy ``get``.
        """
        super(Model3DFilter, self).__init__(*args, **kwargs)
        user: User = kwargs.get("request").user
        self.filters["obdobi"] = MultipleChoiceFilter(
            field_name="casti__komponenty__komponenty__obdobi",
            label=_("dokument.filters.dokumentFilter.obdobi.label"),
            choices=heslar_12(HESLAR_OBDOBI, HESLAR_OBDOBI_KAT)[1:],
            widget=SelectMultiple(
                attrs={
                    "class": "selectpicker",
                    "data-multiple-separator": "; ",
                    "data-live-search": "true",
                }
            ),
        )

        self.filters["areal"] = MultipleChoiceFilter(
            field_name="casti__komponenty__komponenty__areal",
            label=_("dokument.filters.dokumentFilter.areal.label"),
            choices=heslar_12(HESLAR_AREAL, HESLAR_AREAL_KAT)[1:],
            widget=SelectMultiple(
                attrs={
                    "class": "selectpicker",
                    "data-multiple-separator": "; ",
                    "data-live-search": "true",
                }
            ),
            distinct=True,
        )
        self.filters["objekt_druh"] = MultipleChoiceFilter(
            field_name="casti__komponenty__komponenty__objekty__druh",
            label=_("dokument.filters.dokumentFilter.objektDruh.label"),
            choices=heslar_12(HESLAR_OBJEKT_DRUH, HESLAR_OBJEKT_DRUH_KAT)[1:],
            widget=SelectMultiple(
                attrs={
                    "class": "selectpicker",
                    "data-multiple-separator": "; ",
                    "data-live-search": "true",
                }
            ),
            distinct=True,
        )

        self.filters["objekt_specifikace"] = MultipleChoiceFilter(
            field_name="casti__komponenty__komponenty__objekty__specifikace",
            label=_("dokument.filters.dokumentFilter.objektSpecifikace.label"),
            choices=heslar_12(HESLAR_OBJEKT_SPECIFIKACE, HESLAR_OBJEKT_SPECIFIKACE_KAT)[1:],
            widget=SelectMultiple(
                attrs={
                    "class": "selectpicker",
                    "data-multiple-separator": "; ",
                    "data-live-search": "true",
                }
            ),
            distinct=True,
        )

        self.filters["predmet_druh"] = MultipleChoiceFilter(
            field_name="casti__komponenty__komponenty__predmety__druh",
            label=_("dokument.filters.dokumentFilter.predmetDruh.label"),
            choices=heslar_12(HESLAR_PREDMET_DRUH, HESLAR_PREDMET_DRUH_KAT)[1:],
            widget=SelectMultiple(
                attrs={
                    "class": "selectpicker",
                    "data-multiple-separator": "; ",
                    "data-live-search": "true",
                }
            ),
            distinct=True,
        )
        self.filters["posudky"] = MultipleChoiceFilter(
            field_name="posudky",
            label=_("dokument.filters.dokumentFilter.posudky.label"),
            choices=heslar_12(HESLAR_POSUDEK_TYP, HESLAR_POSUDEK_TYP_KAT)[1:],
            widget=SelectMultiple(
                attrs={
                    "class": "selectpicker",
                    "data-multiple-separator": "; ",
                    "data-live-search": "true",
                }
            ),
            distinct=True,
        )
        self.set_filter_fields(user)
        self.helper = Model3DFilterFormHelper()


class Model3DFilterFormHelper(crispy_forms.helper.FormHelper):
    """Třída pro správně zobrazení filtru."""

    form_method = "GET"

    def __init__(self, form=None):
        """
        Inicializuje instanci třídy.

        :param form: Parametr ``form`` se předává do volání ``__init__()``.
        """
        history_divider = "<span class='app-divider-label'>%(translation)s</span>" % {
            "translation": _("dokument.filters.model3DFilterFormHelper.historyDivider.label")
        }
        self.layout = Layout(
            Div(
                Div(
                    Div("ident_cely", css_class="col-sm-2"),
                    Div("doi", css_class="col-sm-2"),
                    Div("typ_dokumentu", css_class="col-sm-2"),
                    Div("format", css_class="col-sm-2"),
                    Div("stav", css_class="col-sm-2"),
                    Div("organizace", css_class="col-sm-2"),
                    Div("autor", css_class="col-sm-2"),
                    Div("rok_vzniku", css_class="col-sm-4 app-daterangepicker"),
                    Div("duveryhodnost", css_class="col-sm-2"),
                    Div("popisne_udaje", css_class="col-sm-4"),
                    Div("zeme", css_class="col-sm-2"),
                    Div("obdobi", css_class="col-sm-2"),
                    Div("areal", css_class="col-sm-2"),
                    Div("aktivity", css_class="col-sm-2"),
                    Div("licence", css_class="col-sm-2"),
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
                    HTML(history_divider),
                    HTML('<hr class="mt-0" />'),
                    data_bs_toggle="collapse",
                    href="#historieCollapse",
                    role="button",
                    aria_expanded="false",
                    aria_controls="historieCollapse",
                    css_class="col-sm-12 app-btn-show-more collapsed",
                ),
                Div(
                    Div("historie_typ_zmeny", css_class="col-sm-2"),
                    Div("historie_datum_zmeny_od", css_class="col-sm-3 app-daterangepicker"),
                    Div("historie_uzivatel", css_class="col-sm-2"),
                    Div("historie_uzivatel_organizace", css_class="col-sm-2"),
                    Div("historie_poznamka", css_class="col-sm-3"),
                    id="historieCollapse",
                    css_class="collapse row",
                ),
            ),
        )
        self.form_tag = False
        super().__init__(form)


class DokumentFilter(Model3DFilter):
    """
    Třída pro základní filtrování dokumentu a jejich potomků.
    """

    TYP_VAZBY = DOKUMENT_RELATION_TYPE
    HISTORIE_TYP_ZMENY_STARTS_WITH = "D"

    rada = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_DOKUMENT_RADA),
        label=_("dokument.filters.dokumentFilter.rada.label"),
        widget=SelectMultipleSeparator(),
    )
    typ_dokumentu = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_DOKUMENT_TYP).exclude(id__in=MODEL_3D_DOKUMENT_TYPES),
        label=_("dokument.filters.dokumentFilter.typDokumentu.label"),
        field_name="typ_dokumentu",
        widget=SelectMultipleSeparator(),
    )
    material_originalu = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_DOKUMENT_MATERIAL),
        label=_("dokument.filters.dokumentFilter.materialOriginalu.label"),
        widget=SelectMultipleSeparator(),
    )

    uzemni_prislusnost = MultipleChoiceFilter(
        method="filter_uzemni_prislusnost",
        label=_("dokument.filters.dokumentFilter.uzemniPrislusnost.label"),
        choices=(
            ("M-", _("dokument.filters.dokumentFilter.uzemniPrislusnost.M.option")),
            ("C-", _("dokument.filters.dokumentFilter.uzemniPrislusnost.C.option")),
        ),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )
    jazyky = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_JAZYK),
        label=_("dokument.filters.dokumentFilter.jazyky.label"),
        widget=SelectMultipleSeparator(),
    )

    ulozeni_originalu = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_DOKUMENT_ULOZENI),
        label=_("dokument.filters.dokumentFilter.ulozeniOriginalu.label"),
        widget=SelectMultipleSeparator(),
    )
    pristupnost = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_PRISTUPNOST),
        label=_("dokument.filters.dokumentFilter.pristupnost.label"),
        widget=SelectMultipleSeparator(),
    )

    datum_zverejneni = DateFromToRangeFilter(
        label=_("dokument.filters.dokumentFilter.datumZverejneni.label"),
        widget=DateRangeWidget(attrs={"type": "text", "max": "2100-12-31"}),
        distinct=True,
    )
    datum_vzniku = DateFromToRangeFilter(
        label=_("dokument.filters.dokumentFilter.datumVzniku.label"),
        field_name="extra_data__datum_vzniku",
        widget=DateRangeWidget(attrs={"type": "text", "max": "2100-12-31"}),
        distinct=True,
    )
    zachovalost = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_DOKUMENT_ZACHOVALOST),
        label=_("dokument.filters.dokumentFilter.zachovalost.label"),
        field_name="extra_data__zachovalost",
        widget=SelectMultipleSeparator(),
    )
    nahrada = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_DOKUMENT_NAHRADA),
        label=_("dokument.filters.dokumentFilter.nahrada.label"),
        field_name="extra_data__nahrada",
        widget=SelectMultipleSeparator(),
    )
    udalost_typ = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_UDALOST_TYP),
        label=_("dokument.filters.dokumentFilter.udalostTyp.label"),
        field_name="extra_data__udalost_typ",
        widget=SelectMultipleSeparator(),
    )

    rok_udalosti = RangeFilter(
        label=_("dokument.filters.dokumentFilter.rokUdalosti.label"),
        method="filter_roky_range",
        widget=DateRangeWidget(
            attrs={
                "max": "2100-12-31",
                "class": "textinput textInput dateinput form-control date_roky",
            }
        ),
        distinct=True,
        field_name=["extra_data__rok_od", "extra_data__rok_do"],
    )

    osoby = ModelMultipleChoiceFilter(
        label=_("dokument.filters.dokumentFilter.osoby.label"),
        widget=AutocompleteModelSelect2Multiple(url="heslar:osoba-autocomplete"),
        queryset=Osoba.objects.all(),
    )
    duveryhodnost_od = NumberFilter(
        field_name="extra_data__duveryhodnost",
        label=_("dokument.filters.dokumentFilter.duveryhodnost.label"),
        lookup_expr="gte",
    )

    duveryhodnost_do = NumberFilter(field_name="extra_data__duveryhodnost", label=" ", lookup_expr="lte")

    jistota = MultipleChoiceFilter(
        choices=[
            ("True", _("dokument.filters.dokumentFilter.true.option")),
            ("False", _("dokument.filters.dokumentFilter.false.option")),
        ],
        method="filter_jistota",
        label=_("dokument.filters.dokumentFilter.jistota.label"),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )
    format = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_DOKUMENT_FORMAT).exclude(id__in=MODEL_3D_DOKUMENT_FORMATS),
        label=_("dokument.filters.dokumentFilter.format.label"),
        field_name="extra_data__format",
        widget=SelectMultipleSeparator(),
    )

    poznamka_komponenty = CharFilter(
        label=_("dokument.filters.dokumentFilter.poznamkaKomponenty.label"),
        field_name="casti__komponenty__komponenty__poznamka",
        lookup_expr="icontains",
        distinct=True,
    )

    predmet_pozn_pocet = CharFilter(
        method="filter_predmet_pozn_pocet",
        label=_("dokument.filters.dokumentFilter.predmetPoznPocet.label"),
        distinct=True,
    )

    objekt_pozn_pocet = CharFilter(
        method="filter_objekt_pozn_pocet",
        label=_("dokument.filters.dokumentFilter.objektPoznPocet.label"),
        distinct=True,
    )

    neident_katastr = ModelMultipleChoiceFilter(
        queryset=RuianKatastr.objects.all(),
        label=_("dokument.filters.dokumentFilter.neidentAkceKatastr.label"),
        field_name="casti__neident_akce__katastr",
        widget=AutocompleteModelSelect2Multiple(url="heslar:katastr-autocomplete"),
        distinct=True,
    )

    neident_vedouci = ModelMultipleChoiceFilter(
        label=_("dokument.filters.dokumentFilter.neidentVedouci.label"),
        field_name="casti__neident_akce__neidentakcevedouci__vedouci",
        widget=AutocompleteModelSelect2Multiple(url="heslar:osoba-autocomplete"),
        queryset=Osoba.objects.all(),
    )

    neident_rok_zahajeni = RangeFilter(
        label=_("dokument.filters.dokumentFilter.neidentRokZahajeni.label"),
        method="filter_roky_range",
        widget=DateRangeWidget(
            attrs={
                "max": "2100-12-31",
                "class": "textinput textInput dateinput form-control date_roky",
            }
        ),
        distinct=True,
        field_name=["casti__neident_akce__rok_zahajeni", "casti__neident_akce__rok_ukonceni"],
    )

    neident_poznamka = CharFilter(
        method="filter_neident_poznamka",
        label=_("dokument.filters.dokumentFilter.neidentPoznamka.label"),
        distinct=True,
    )

    let_id = CharFilter(
        lookup_expr="icontains",
        label=_("dokument.filters.dokumentFilter.ledId.label"),
        field_name="let__ident_cely",
    )

    let_datum = DateFromToRangeFilter(
        label=_("dokument.filters.dokumentFilter.letDatum.label"),
        field_name="let__datum",
        widget=DateRangeWidget(attrs={"type": "text", "max": "2100-12-31"}),
        distinct=True,
    )

    let_pilot = CharFilter(
        lookup_expr="icontains",
        label=_("dokument.filters.dokumentFilter.letPilot.label"),
        field_name="let__pilot",
    )

    let_pozorovatel = ModelMultipleChoiceFilter(
        label=_("dokument.filters.dokumentFilter.letPozorovatel.label"),
        field_name="let__pozorovatel",
        widget=AutocompleteModelSelect2Multiple(url="heslar:osoba-autocomplete"),
        queryset=Osoba.objects.all(),
    )

    let_organizace = ModelMultipleChoiceFilter(
        queryset=Organizace.objects.all(),
        label=_("dokument.filters.dokumentFilter.letOrganizace.label"),
        field_name="let__organizace",
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
    )

    letiste_start = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_LETISTE),
        label=_("dokument.filters.dokumentFilter.letisteStart.label"),
        field_name="let__letiste_start",
        widget=SelectMultipleSeparator(),
    )
    letiste_cil = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_LETISTE),
        label=_("dokument.filters.dokumentFilter.letisteCil.label"),
        field_name="let__letiste_cil",
        widget=SelectMultipleSeparator(),
    )

    let_pocasi = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_POCASI),
        label=_("dokument.filters.dokumentFilter.letPocazi.label"),
        field_name="let__pocasi",
        widget=SelectMultipleSeparator(),
    )
    let_dohlednost = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_DOHLEDNOST),
        label=_("dokument.filters.dokumentFilter.letDohlednost.label"),
        field_name="let__dohlednost",
        widget=SelectMultipleSeparator(),
    )
    let_poznamka = CharFilter(
        method="filter_let_poznamka",
        label=_("dokument.filters.dokumentFilter.letPoznamka.label"),
        distinct=True,
    )

    tvary = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_LETFOTO_TVAR),
        label=_("dokument.filters.dokumentFilter.tvary.label"),
        widget=SelectMultipleSeparator(),
    )
    tvar_poznamka = CharFilter(
        field_name="tvar__poznamka",
        lookup_expr="icontains",
        label=_("dokument.filters.dokumentFilter.tvarPoznamka.label"),
        distinct=True,
    )
    # Filtry na vlastnosti souboru mají prázdnou metodu (``noop``) – nefiltrují samostatně,
    # aby nevznikal samostatný JOIN na ``soubor`` pro každý z nich. Sloučí je do jediného
    # korelovaného poddotazu ``_get_soubor_subquery`` / ``filter_queryset``.
    soubor_typ = SouborTypFilter(
        field_name="soubory__soubory__mimetype",
        method="filter_soubor_noop",
        label=_("dokument.filters.dokumentFilter.souborTyp.label"),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    soubor_velikost_od = NumberFilter(
        field_name="soubory__soubory__size_mb",
        method="filter_soubor_noop",
        label=_("dokument.filters.dokumentFilter.souborVelikost.label"),
    )

    soubor_velikost_do = NumberFilter(
        field_name="soubory__soubory__size_mb",
        method="filter_soubor_noop",
        label=" ",
    )

    soubor_pocet_stran_od = NumberFilter(
        field_name="soubory__soubory__rozsah",
        method="filter_soubor_noop",
        label=_("dokument.filters.dokumentFilter.souborPocetStran.label"),
    )

    soubor_pocet_stran_do = NumberFilter(
        field_name="soubory__soubory__rozsah",
        method="filter_soubor_noop",
        label=" ",
    )
    id_AZ = CharFilter(
        method="filter_id_AZ",
        label=_("dokument.filters.dokumentFilter.idAZ.label"),
        distinct=True,
    )

    id_projekt = CharFilter(
        method="filter_id_projekt",
        label=_("dokument.filters.dokumentFilter.idProjekt.label"),
        distinct=True,
    )

    exist_neident_akce = MultipleChoiceFilter(
        choices=[
            ("True", _("dokument.filters.dokumentFilter.existNeidentAkce.true.option")),
            ("False", _("dokument.filters.dokumentFilter.existNeidentAkce.false.option")),
        ],
        method="filter_exist_neident_akce",
        label=_("dokument.filters.dokumentFilter.existNeidentAkce.label"),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    exist_komponenty = MultipleChoiceFilter(
        choices=[
            ("True", _("dokument.filters.dokumentFilter.existKomponenta.true.option")),
            ("False", _("dokument.filters.dokumentFilter.existKomponenta.false.option")),
        ],
        method="filter_exist_komponenty",
        label=_("dokument.filters.dokumentFilter.existKomponenta.label"),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    exist_nalezy = MultipleChoiceFilter(
        choices=[
            ("True", _("dokument.filters.dokumentFilter.existNalezy.true.option")),
            ("False", _("dokument.filters.dokumentFilter.existNalezy.false.option")),
        ],
        method="filter_exist_nalezy",
        label=_("dokument.filters.dokumentFilter.existNalezy.label"),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    exist_tvary = MultipleChoiceFilter(
        choices=[
            ("True", _("dokument.filters.dokumentFilter.existTvary.true.option")),
            ("False", _("dokument.filters.dokumentFilter.existTvary.false.option")),
        ],
        method="filter_exist_tvary",
        label=_("dokument.filters.dokumentFilter.existTvary.label"),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    exist_soubory = MultipleChoiceFilter(
        choices=[
            ("True", _("dokument.filters.dokumentFilter.existSoubory.true.option")),
            ("False", _("dokument.filters.dokumentFilter.existSoubory.false.option")),
        ],
        method="filter_exist_soubory",
        label=_("dokument.filters.dokumentFilter.existSoubory.label"),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
        distinct=True,
    )

    def filter_uzemni_prislusnost(self, queryset, name, value):
        """
        Filtruje dokumenty podle územní příslušnosti.

        :param queryset: QuerySet dokumentů k filtrování.
        :param name: Jméno pole pro filtrování.
        :param value: Hodnota pro filtrování.
        :return: Filtrovaný QuerySet.
        """
        logger.debug("dokument.filters.DokumentFilter.filter_uzemni_prislusnost", extra={"value": value})
        query = reduce(operator.or_, (Q(ident_cely__contains=item) for item in value))
        return queryset.filter(query)

    def filter_popisne_udaje(self, queryset, name, value):
        """
        Filtruje dokumenty podle popisu, poznámky, odkazu a textů v komponentách.

        :param queryset: QuerySet dokumentů k filtrování.
        :param name: Jméno pole pro filtrování.
        :param value: Hodnota pro filtrování.
        :return: Filtrovaný QuerySet.
        """
        return queryset.filter(
            Q(oznaceni_originalu__icontains=value)
            | Q(popis__icontains=value)
            | Q(poznamka__icontains=value)
            | Q(licence__heslo__icontains=value)
            | Q(extra_data__cislo_objektu__icontains=value)
            | Q(extra_data__region_extra__icontains=value)
            | Q(extra_data__udalost__icontains=value)
        )

    def filter_predmet_pozn_pocet(self, queryset, name, value):
        """
        Filtruje dokumenty podle počtu poznámek v předmětech.

        :param queryset: QuerySet dokumentů k filtrování.
        :param name: Jméno pole pro filtrování.
        :param value: Hodnota pro filtrování.
        :return: Filtrovaný QuerySet.
        """
        return queryset.filter(
            Q(casti__komponenty__komponenty__predmety__poznamka__icontains=value)
            | Q(casti__komponenty__komponenty__predmety__pocet__icontains=value)
        ).distinct()

    def filter_objekt_pozn_pocet(self, queryset, name, value):
        """
        Filtruje dokumenty podle počtu poznámek v objektech.

        :param queryset: QuerySet dokumentů k filtrování.
        :param name: Jméno pole pro filtrování.
        :param value: Hodnota pro filtrování.
        :return: Filtrovaný QuerySet.
        """
        return queryset.filter(
            Q(casti__komponenty__komponenty__objekty__poznamka__icontains=value)
            | Q(casti__komponenty__komponenty__objekty__pocet__icontains=value)
        ).distinct()

    def filter_jistota(self, queryset, name, value):
        """
        Filtruje dokumenty podle míry jistoty.

        :param queryset: QuerySet dokumentů k filtrování.
        :param name: Jméno pole pro filtrování.
        :param value: Hodnota pro filtrování.
        :return: Filtrovaný QuerySet.
        """
        if "True" in value and "False" in value:
            return queryset.distinct()
        elif "True" in value:
            return queryset.filter(casti__komponenty__komponenty__jistota=True).distinct()
        elif "False" in value:
            return queryset.exclude(casti__komponenty__komponenty__jistota=True).distinct()
        else:
            return queryset.distinct()

    def filter_neident_poznamka(self, queryset, name, value):
        """
        Filtruje dokumenty podle poznámky v neidentifikované akci.

        :param queryset: QuerySet dokumentů k filtrování.
        :param name: Jméno pole pro filtrování.
        :param value: Hodnota pro filtrování.
        :return: Filtrovaný QuerySet.
        """
        return queryset.filter(
            Q(casti__neident_akce__poznamka__icontains=value)
            | Q(casti__neident_akce__popis__icontains=value)
            | Q(casti__neident_akce__pian__icontains=value)
            | Q(casti__neident_akce__lokalizace__icontains=value)
        ).distinct()

    def filter_let_poznamka(self, queryset, name, value):
        """
        Filtruje dokumenty podle poznámky v letecké akci.

        :param queryset: QuerySet dokumentů k filtrování.
        :param name: Jméno pole pro filtrování.
        :param value: Hodnota pro filtrování.
        :return: Filtrovaný QuerySet.
        """
        return queryset.filter(
            Q(let__typ_letounu__icontains=value)
            | Q(let__fotoaparat__icontains=value)
            | Q(let__uzivatelske_oznaceni__icontains=value)
            | Q(let__ucel_letu__icontains=value)
        ).distinct()

    def filter_id_AZ(self, queryset, name, value):
        """
        Filtruje dokumenty podle identifikátoru archeologické akce.

        :param queryset: QuerySet dokumentů k filtrování.
        :param name: Jméno pole pro filtrování.
        :param value: Hodnota pro filtrování.
        :return: Filtrovaný QuerySet.
        """
        return queryset.filter(Q(casti__archeologicky_zaznam__ident_cely__icontains=value)).distinct()

    def filter_id_projekt(self, queryset, name, value):
        """
        Filtruje dokumenty podle identifikátoru projektu.

        :param queryset: QuerySet dokumentů k filtrování.
        :param name: Jméno pole pro filtrování.
        :param value: Hodnota pro filtrování.
        :return: Filtrovaný QuerySet.
        """
        return queryset.filter(Q(casti__projekt__ident_cely__icontains=value)).distinct()

    def filter_exist_neident_akce(self, queryset, name, value):
        """
        Filtruje dokumenty s neidentifikovanou akcí.

        :param queryset: QuerySet dokumentů k filtrování.
        :param name: Jméno pole pro filtrování.
        :param value: Hodnota pro filtrování.
        :return: Filtrovaný QuerySet.
        """
        if len(value) == 1:
            akce = NeidentAkce.objects.filter(dokument_cast=models.OuterRef("pk"))
            if "True" in value:
                casti = DokumentCast.objects.filter(models.Exists(akce))
                return queryset.filter(casti__in=casti).distinct()
            else:
                casti = DokumentCast.objects.filter(models.Exists(akce))
                bez_casti = casti.filter(dokument=models.OuterRef("pk"))
                return queryset.exclude(models.Exists(bez_casti)).distinct()

        else:
            return queryset.distinct()

    def filter_exist_komponenty(self, queryset, name, value):
        """
        Filtruje dokumenty s komponentami.

        :param queryset: QuerySet dokumentů k filtrování.
        :param name: Jméno pole pro filtrování.
        :param value: Hodnota pro filtrování.
        :return: Filtrovaný QuerySet.
        """
        if len(value) == 1:
            komponenty = Komponenta.objects.filter(komponenta_vazby__casti_dokumentu=models.OuterRef("pk"))
            casti = DokumentCast.objects.filter(models.Exists(komponenty))
            if "True" in value:
                return queryset.filter(casti__in=casti).distinct()
            else:
                bez_casti = casti.filter(dokument=models.OuterRef("pk"))
                return queryset.exclude(models.Exists(bez_casti)).distinct()

        else:
            return queryset.distinct()

    def filter_exist_nalezy(self, queryset, name, value):
        """
        Filtruje dokumenty s nálezy.

        :param queryset: QuerySet dokumentů k filtrování.
        :param name: Jméno pole pro filtrování.
        :param value: Hodnota pro filtrování.
        :return: Filtrovaný QuerySet.
        """
        if len(value) == 1:
            objekty = NalezObjekt.objects.filter(komponenta__komponenta_vazby__casti_dokumentu=models.OuterRef("pk"))
            casti_objekty = DokumentCast.objects.filter(models.Exists(objekty))
            predmety = NalezObjekt.objects.filter(komponenta__komponenta_vazby__casti_dokumentu=models.OuterRef("pk"))
            casti_predmety = DokumentCast.objects.filter(models.Exists(predmety))
            if "True" in value:
                return queryset.filter(Q(casti__in=casti_objekty) | Q(casti__in=casti_predmety)).distinct()
            else:
                bez_casti_objekty = casti_objekty.filter(dokument=models.OuterRef("pk"))
                bez_casti_predmety = casti_predmety.filter(dokument=models.OuterRef("pk"))
                return (
                    queryset.exclude(models.Exists(bez_casti_objekty))
                    .exclude(models.Exists(bez_casti_predmety))
                    .distinct()
                )

        else:
            return queryset.distinct()

    def filter_exist_tvary(self, queryset, name, value):
        """
        Filtruje dokumenty s tvary.

        :param queryset: QuerySet dokumentů k filtrování.
        :param name: Jméno pole pro filtrování.
        :param value: Hodnota pro filtrování.
        :return: Filtrovaný QuerySet.
        """
        if len(value) == 1:
            tvar = Tvar.objects.filter(dokument=models.OuterRef("pk"))
            if "True" in value:
                return queryset.filter(models.Exists(tvar)).distinct()
            else:
                return queryset.filter(~models.Exists(tvar)).distinct()

        else:
            return queryset.distinct()

    def filter_exist_soubory(self, queryset, name, value):
        """
        Filtruje dokumenty se soubory.

        :param queryset: QuerySet dokumentů k filtrování.
        :param name: Jméno pole pro filtrování.
        :param value: Hodnota pro filtrování.
        :return: Filtrovaný QuerySet.
        """
        if len(value) == 1:
            soubor = Soubor.objects.filter(vazba__dokument_souboru=models.OuterRef("pk"))
            if "True" in value:
                return queryset.filter(models.Exists(soubor)).distinct()
            else:
                return queryset.filter(~models.Exists(soubor)).distinct()

        else:
            return queryset.distinct()

    def _get_soubor_subquery(self):
        """
        Sestaví podmínky pro filtrování podle vlastností jednoho souboru.

        Filtry typu, velikosti a počtu stran (rozsahu) se slučují do jediného korelovaného
        poddotazu, aby všechny podmínky platily pro tentýž soubor. Bez tohoto sloučení by
        každý filtr přidal samostatný JOIN na ``soubor`` (násobný JOIN téže tabulky), což
        vede k rozsáhlému kartézskému součinu a k volnější sémantice (různé soubory by mohly
        splňovat různé podmínky).

        :return: Slovník podmínek pro model ``Soubor`` nebo ``None``, není-li aktivní žádný filtr.
        """
        cd = self.form.cleaned_data
        conditions = {}
        typ = cd.get("soubor_typ")
        if typ:
            conditions["mimetype__in"] = typ
        velikost_od = cd.get("soubor_velikost_od")
        if velikost_od is not None:
            conditions["size_mb__gte"] = velikost_od
        velikost_do = cd.get("soubor_velikost_do")
        if velikost_do is not None:
            conditions["size_mb__lte"] = velikost_do
        stran_od = cd.get("soubor_pocet_stran_od")
        if stran_od is not None:
            conditions["rozsah__gte"] = stran_od
        stran_do = cd.get("soubor_pocet_stran_do")
        if stran_do is not None:
            conditions["rozsah__lte"] = stran_do
        return conditions or None

    def filter_soubor_noop(self, queryset, name, value):
        """
        Prázdný filtr pro pole vlastností souboru – vrací queryset beze změny.

        Vlastní filtrování probíhá hromadně v ``filter_queryset`` přes jeden korelovaný
        poddotaz (viz :meth:`_get_soubor_subquery`), aby nevznikal samostatný JOIN na
        ``soubor`` pro každé pole.

        :param queryset: Vstupní queryset.
        :param name: Jméno pole filtru.
        :param value: Hodnota filtru (ignoruje se).
        :return: Nezměněný queryset.
        """
        return queryset

    def filter_queryset(self, queryset):
        """
        Filtruje queryset a slučuje filtry podle vlastností souboru do jednoho poddotazu.

        :param queryset: Vstupní queryset dokumentů před filtrací.
        :return: Filtrovaný queryset.
        """
        soubor_conditions = self._get_soubor_subquery()
        queryset = super().filter_queryset(queryset)
        if soubor_conditions:
            soubory = Soubor.objects.filter(vazba__dokument_souboru=OuterRef("pk"), **soubor_conditions)
            queryset = queryset.filter(Exists(soubory))
        return queryset

    def __init__(self, *args, **kwargs):
        """
        Inicializuje instanci třídy.

        :param args: Parametr ``args`` se předává do volání ``__init__()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.
        """
        super(DokumentFilter, self).__init__(*args, **kwargs)
        self.helper = DokumentFilterFormHelper()


class DokumentFilterFormHelper(crispy_forms.helper.FormHelper):
    """Třída pro správně zobrazení filtru."""

    form_method = "GET"

    def __init__(self, form=None):
        """
        Inicializuje instanci třídy.

        :param form: Parametr ``form`` se předává do volání ``__init__()``.
        """
        history_divider = "<span class='app-divider-label'>%(translation)s</span>" % {
            "translation": _("dokument.filters.dokumentFilterFormHelper.historyDivider.label")
        }
        extra_data_divider = "<span class='app-divider-label'>%(translation)s</span>" % {
            "translation": _("dokument.filters.dokumentFilterFormHelper.extraDataDivider.label")
        }
        komponenta_divider = "<span class='app-divider-label'>%(translation)s</span>" % {
            "translation": _("dokument.filters.dokumentFilterFormHelper.komponentaNalezDivider.label")
        }
        neident_akce_divider = "<span class='app-divider-label'>%(translation)s</span>" % {
            "translation": _("dokument.filters.dokumentFilterFormHelper.neidentAkceDivider.label")
        }
        lety_tvary_divider = "<span class='app-divider-label'>%(translation)s</span>" % {
            "translation": _("dokument.filters.dokumentFilterFormHelper.letyTvaryDivider.label")
        }
        soubory_divider = "<span class='app-divider-label'>%(translation)s</span>" % {
            "translation": _("dokument.filters.dokumentFilterFormHelper.souboryDivider.label")
        }
        vazby_divider = "<span class='app-divider-label'>%(translation)s</span>" % {
            "translation": _("dokument.filters.dokumentFilterFormHelper.vazbyDivider.label")
        }
        self.layout = Layout(
            Div(
                Div(
                    Div("ident_cely", css_class="col-sm-6 col-lg-2"),
                    Div("doi", css_class="col-sm-6 col-lg-2"),
                    Div("rada", css_class="col-sm-6 col-lg-2"),
                    Div("typ_dokumentu", css_class="col-sm-6 col-lg-2"),
                    Div("material_originalu", css_class="col-sm-6 col-lg-2"),
                    Div("uzemni_prislusnost", css_class="col-sm-6 col-lg-2"),
                    Div("stav", css_class="col-sm-6 col-lg-2"),
                    Div("autor", css_class="col-sm-6 col-lg-2"),
                    Div("organizace", css_class="col-sm-6 col-lg-2"),
                    Div("rok_vzniku", css_class="col-sm-6 col-lg-4 app-daterangepicker"),
                    Div("licence", css_class="col-sm-6 col-lg-2"),
                    Div("popisne_udaje", css_class="col-sm-6 col-lg-4"),
                    Div("jazyky", css_class="col-sm-6 col-lg-2"),
                    Div("ulozeni_originalu", css_class="col-sm-6 col-lg-2"),
                    Div("posudky", css_class="col-sm-6 col-lg-2"),
                    Div("pristupnost", css_class="col-sm-6 col-lg-2"),
                    Div("datum_zverejneni", css_class="col-sm-6 col-lg-4 app-daterangepicker"),
                    Div("exist_neident_akce", css_class="col-sm-6 col-lg-2"),
                    Div("exist_komponenty", css_class="col-sm-6 col-lg-2"),
                    Div("exist_nalezy", css_class="col-sm-6 col-lg-2"),
                    Div("exist_tvary", css_class="col-sm-6 col-lg-2"),
                    Div("exist_soubory", css_class="col-sm-6 col-lg-2"),
                    css_class="row",
                ),
                Div(
                    HTML('<span class="material-icons app-icon-expand">expand_more</span>'),
                    HTML(history_divider),
                    HTML('<hr class="mt-0" />'),
                    data_bs_toggle="collapse",
                    href="#historieCollapse",
                    role="button",
                    aria_expanded="false",
                    aria_controls="historieCollapse",
                    css_class="col-sm-12 app-btn-show-more collapsed",
                ),
                Div(
                    Div("historie_typ_zmeny", css_class="col-sm-6 col-lg-2"),
                    Div("historie_datum_zmeny_od", css_class="col-sm-6 col-lg-3 app-daterangepicker"),
                    Div("historie_uzivatel", css_class="col-sm-6 col-lg-2"),
                    Div("historie_uzivatel_organizace", css_class="col-sm-6 col-lg-2"),
                    Div("historie_poznamka", css_class="col-sm-6 col-lg-3"),
                    id="historieCollapse",
                    css_class="collapse row",
                ),
                Div(
                    HTML('<span class="material-icons app-icon-expand">expand_more</span>'),
                    HTML(extra_data_divider),
                    HTML('<hr class="mt-0" />'),
                    data_bs_toggle="collapse",
                    href="#extraDataCollapse",
                    role="button",
                    aria_expanded="false",
                    aria_controls="extraDataCollapse",
                    css_class="col-sm-12 app-btn-show-more collapsed",
                ),
                Div(
                    Div("datum_vzniku", css_class="col-sm-6 col-lg-4 app-daterangepicker"),
                    Div("zachovalost", css_class="col-sm-6 col-lg-2"),
                    Div("nahrada", css_class="col-sm-6 col-lg-2"),
                    Div("format", css_class="col-sm-6 col-lg-2"),
                    Div("zeme", css_class="col-sm-6 col-lg-2"),
                    Div("udalost_typ", css_class="col-sm-6 col-lg-2"),
                    Div("rok_udalosti", css_class="col-sm-6 col-lg-4 app-daterangepicker"),
                    # Div("rok_udalosti_do", css_class="col-sm-2"),
                    Div("osoby", css_class="col-sm-6 col-lg-2"),
                    Div("duveryhodnost_od", css_class="col-sm-6 col-lg-2"),
                    Div("duveryhodnost_do", css_class="col-sm-6 col-lg-2"),
                    id="extraDataCollapse",
                    css_class="collapse row",
                ),
                Div(
                    HTML('<span class="material-icons app-icon-expand">expand_more</span>'),
                    HTML(komponenta_divider),
                    HTML('<hr class="mt-0" />'),
                    data_bs_toggle="collapse",
                    href="#komponentaCollapse",
                    role="button",
                    aria_expanded="false",
                    aria_controls="komponentaCollapse",
                    css_class="col-sm-12 app-btn-show-more collapsed",
                ),
                Div(
                    Div("obdobi", css_class="col-sm-6 col-lg-2"),
                    Div("jistota", css_class="col-sm-6 col-lg-2"),
                    Div("areal", css_class="col-sm-6 col-lg-2"),
                    Div("aktivity", css_class="col-sm-6 col-lg-2"),
                    Div("poznamka_komponenty", css_class="col-sm-6 col-lg-4"),
                    Div("predmet_druh", css_class="col-sm-6 col-lg-2"),
                    Div("predmet_specifikace", css_class="col-sm-6 col-lg-2"),
                    Div("predmet_pozn_pocet", css_class="col-sm-6 col-lg-4"),
                    Div(css_class="col-sm-6 col-lg-4"),
                    Div("objekt_druh", css_class="col-sm-6 col-lg-2"),
                    Div("objekt_specifikace", css_class="col-sm-6 col-lg-2"),
                    Div("objekt_pozn_pocet", css_class="col-sm-4"),
                    Div(css_class="col-sm-4"),
                    id="komponentaCollapse",
                    css_class="collapse row",
                ),
                Div(
                    HTML('<span class="material-icons app-icon-expand">expand_more</span>'),
                    HTML(neident_akce_divider),
                    HTML('<hr class="mt-0" />'),
                    data_bs_toggle="collapse",
                    href="#neidentAkceCollapse",
                    role="button",
                    aria_expanded="false",
                    aria_controls="neidentAkceCollapse",
                    css_class="col-sm-12 app-btn-show-more collapsed",
                ),
                Div(
                    Div("neident_katastr", css_class="col-sm-6 col-lg-2"),
                    Div("neident_vedouci", css_class="col-sm-6 col-lg-2"),
                    Div("neident_rok_zahajeni", css_class="col-sm-6 col-lg-4 app-daterangepicker"),
                    Div("neident_poznamka", css_class="col-sm-6 col-lg-2"),
                    id="neidentAkceCollapse",
                    css_class="collapse row",
                ),
                Div(
                    HTML('<span class="material-icons app-icon-expand">expand_more</span>'),
                    HTML(lety_tvary_divider),
                    HTML('<hr class="mt-0" />'),
                    data_bs_toggle="collapse",
                    href="#letyTvaryCollapse",
                    role="button",
                    aria_expanded="false",
                    aria_controls="letyTvaryCollapse",
                    css_class="col-sm-12 app-btn-show-more collapsed",
                ),
                Div(
                    Div("let_id", css_class="col-sm-6 col-lg-2"),
                    Div("let_datum", css_class="col-sm-6 col-lg-4 app-daterangepicker"),
                    Div("let_pilot", css_class="col-sm-6 col-lg-2"),
                    Div("let_pozorovatel", css_class="col-sm-6 col-lg-2"),
                    Div("let_organizace", css_class="col-sm-6 col-lg-2"),
                    Div("letiste_start", css_class="col-sm-6 col-lg-2"),
                    Div("letiste_cil", css_class="col-sm-6 col-lg-2"),
                    Div("let_pocasi", css_class="col-sm-6 col-lg-2"),
                    Div("let_dohlednost", css_class="col-sm-6 col-lg-2"),
                    Div("let_poznamka", css_class="col-sm-6 col-lg-4"),
                    Div("tvary", css_class="col-sm-6 col-lg-2"),
                    Div("tvar_poznamka", css_class="col-sm-6 col-lg-4"),
                    id="letyTvaryCollapse",
                    css_class="collapse row",
                ),
                Div(
                    HTML('<span class="material-icons app-icon-expand">expand_more</span>'),
                    HTML(soubory_divider),
                    HTML('<hr class="mt-0" />'),
                    data_bs_toggle="collapse",
                    href="#souboryCollapse",
                    role="button",
                    aria_expanded="false",
                    aria_controls="souboryCollapse",
                    css_class="col-sm-12 app-btn-show-more collapsed",
                ),
                Div(
                    Div("soubor_typ", css_class="col-sm-6 col-lg-2"),
                    Div("soubor_velikost_od", css_class="col-sm-6 col-lg-2"),
                    Div("soubor_velikost_do", css_class="col-sm-6 col-lg-2"),
                    Div("soubor_pocet_stran_od", css_class="col-sm-6 col-lg-2"),
                    Div("soubor_pocet_stran_do", css_class="col-sm-6 col-lg-2"),
                    id="souboryCollapse",
                    css_class="collapse row",
                ),
                Div(
                    HTML('<span class="material-icons app-icon-expand">expand_more</span>'),
                    HTML(vazby_divider),
                    HTML('<hr class="mt-0" />'),
                    data_bs_toggle="collapse",
                    href="#vazbyCollapse",
                    role="button",
                    aria_expanded="false",
                    aria_controls="vazbyCollapse",
                    css_class="col-sm-12 app-btn-show-more collapsed",
                ),
                Div(
                    Div("id_AZ", css_class="col-sm-6 col-lg-2"),
                    Div("id_projekt", css_class="col-sm-6 col-lg-2"),
                    id="vazbyCollapse",
                    css_class="collapse row",
                ),
            ),
        )
        self.form_tag = False
        super().__init__(form)
