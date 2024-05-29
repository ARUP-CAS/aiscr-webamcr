import logging

import crispy_forms
import django_filters
import django_filters as filters
from dal import autocomplete
from crispy_forms.layout import Div, Layout, HTML
from django.contrib.auth.models import Group
from django.db import utils
from django.db.models import Q, OuterRef, Subquery, F
from django.forms import Select, SelectMultiple
from django.utils.translation import gettext_lazy as _
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
    ROLE_ARCHEOLOG_ID, ROLE_ADMIN_ID, ROLE_ARCHIVAR_ID,
    SAMOSTATNY_NALEZ_RELATION_TYPE,
)
from heslar.hesla import (
    HESLAR_NALEZOVE_OKOLNOSTI,
    HESLAR_OBDOBI,
    HESLAR_PREDMET_DRUH,
    HESLAR_PREDMET_DRUH_KAT,
    HESLAR_PREDMET_SPECIFIKACE,
    HESLAR_OBDOBI_KAT,
    HESLAR_PRISTUPNOST,
)
from heslar.models import Heslar, RuianKatastr, RuianKraj, RuianOkres
from historie.models import Historie
from pas.models import SamostatnyNalez, UzivatelSpoluprace
from uzivatel.models import Organizace, Osoba, User
from dokument.filters import HistorieFilter
from heslar.views import heslar_12
from core.forms import SelectMultipleSeparator
from pas.forms import PasFilterForm

logger = logging.getLogger(__name__)


class SamostatnyNalezFilter(HistorieFilter, filters.FilterSet):
    """
    Třída pro zakladní filtrování samostatného nálezu a jejich potomků.
    """

    TYP_VAZBY = SAMOSTATNY_NALEZ_RELATION_TYPE
    HISTORIE_TYP_ZMENY_STARTS_WITH = "SN"

    ident_cely = CharFilter(
        lookup_expr="icontains",
        label=_("pas.filters.pasFilter.ident_cely.label")
    )

    stav = MultipleChoiceFilter(
        choices=SamostatnyNalez.PAS_STATES,
        label=_("pas.filters.samostatnyNalezFilter.stav.label"),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
    )

    predano = django_filters.ChoiceFilter(
        choices=SamostatnyNalez.PREDANO_BOOLEAN,
        label=_("pas.filters.samostatnyNalezFilter.predano.label"),
        widget=Select(attrs={"class": "selectpicker", "data-live-search": "true"}),
    )

    kraj = MultipleChoiceFilter(
        choices=RuianKraj.objects.all().values_list("id", "nazev"),
        label=_("pas.filters.samostatnyNalezFilter.kraj.label"),
        field_name="katastr__okres__kraj",
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
    )

    okres = MultipleChoiceFilter(
        choices=RuianOkres.objects.all().values_list("id", "nazev"),
        label=_("pas.filters.samostatnyNalezFilter.okres.label"),
        field_name="katastr__okres",
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
    )

    katastr = ModelMultipleChoiceFilter(
        queryset=RuianKatastr.objects.all(),
        field_name="katastr",
        label=_("pas.filters.samostatnyNalezFilter.katastr.label"),
        widget=autocomplete.ModelSelect2Multiple(url="heslar:katastr-autocomplete")
    )

    vlastnik = ModelMultipleChoiceFilter(
        queryset=User.objects.select_related("organizace").all(),
        field_name="historie__historie__uzivatel",
        label=_("pas.filters.samostatnyNalezFilter.vlastnik.label"),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
    )
    popisne_udaje = CharFilter(
        method="filter_popisne_udaje",
        label=_("pas.filters.samostatnyNalezFilter.popisne_udaje.label"),
    )

    nalezce = ModelMultipleChoiceFilter(
        widget=autocomplete.ModelSelect2Multiple(url="heslar:osoba-autocomplete"),
        label=_("pas.filters.samostatnyNalezFilter.nalezce.label"),
        queryset=Osoba.objects.all(),
    )

    predano_organizace = ModelMultipleChoiceFilter(
        queryset=Organizace.objects.all(),
        label=_("pas.filters.samostatnyNalezFilter.predanoOrganizace.label"),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
    )

    okolnosti = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_NALEZOVE_OKOLNOSTI),
        label=_("pas.filters.samostatnyNalezFilter.okolnosti.label"),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
    )

    specifikace = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_PREDMET_SPECIFIKACE),
        label=_("pas.filters.samostatnyNalezFilter.specifikace.label"),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
    )

    datum_nalezu = DateFromToRangeFilter(
        label=_("pas.filters.samostatnyNalezFilter.datumNalezu.label"),
        field_name="datum_nalezu",
        widget=DateRangeWidget(attrs={"type": "text", "max": "2100-12-31"}),
        distinct=True,
    )

    hloubka_od = NumberFilter(
        field_name="hloubka",
        label=_("pas.filters.samostatnyNalezFilter.hloubkaOd.label"),
        lookup_expr="gte"
    )

    hloubka_do = NumberFilter(field_name="hloubka", label=" ", lookup_expr="lte")

    # Filters by historie
    historie_typ_zmeny = MultipleChoiceFilter(
        choices=filter(lambda x: x[0].startswith("SN") or x[0].startswith("KAT"), Historie.CHOICES),
        label=_("pas.filters.samostatnyNalezFilter.historie_typ_zmeny.label"),
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

    pristupnost = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_PRISTUPNOST),
        label=_("pas.filters.samostatnyNalezFilter.pristupnost.label"),
        field_name="pristupnost",
        widget=SelectMultipleSeparator(),
    )

    projekt_organizace = ModelMultipleChoiceFilter(
        queryset=Organizace.objects.all(),
        field_name="projekt__organizace",
        label=_("arch_z.filters.samostatnyNalezFilter.projekt_roganizace.label"),
        widget=SelectMultipleSeparator(),
        distinct=True,
    )

    obdobi = MultipleChoiceFilter(
            method="filter_obdobi",
            label=_("pas.filters.samostatnyNalezFilter.obdobi.label"),
            choices=heslar_12(HESLAR_OBDOBI, HESLAR_OBDOBI_KAT)[1:],
            widget=SelectMultiple(
                attrs={
                    "class": "selectpicker",
                    "data-multiple-separator": "; ",
                    "data-live-search": "true",
                }
            ),
        )
    
    oblast = django_filters.ChoiceFilter(
            choices=OBLAST_CHOICES,
            label=_("pas.filters.samostatnyNalezFilter.oblast.label"),
            method="filter_by_oblast",
            widget=Select(
                attrs={
                    "class": "selectpicker",
                    "data-multiple-separator": "; ",
                    "data-live-search": "true",
                }
            ),
        )
    
    druh_nalezu = MultipleChoiceFilter(
            method="filter_druh_nalezu",
            label=_("pas.filters.samostatnyNalezFilter.druhNalezu.label"),
            choices=heslar_12(HESLAR_PREDMET_DRUH, HESLAR_PREDMET_DRUH_KAT)[1:],
            widget=SelectMultiple(
                attrs={
                    "class": "selectpicker",
                    "data-multiple-separator": "; ",
                    "data-live-search": "true",
                }
            ),
        )

    class Meta:
        model = SamostatnyNalez
        fields = {
            "predano": ["exact"],
        }
        form = PasFilterForm

    def __init__(self, *args, **kwargs):
        super(SamostatnyNalezFilter, self).__init__(*args, **kwargs)
        user: User = kwargs.get("request").user
        self.filters["obdobi"].extra["choices"]=heslar_12(HESLAR_OBDOBI, HESLAR_OBDOBI_KAT)[1:]
            
        self.filters["druh_nalezu"].extra["choices"] =heslar_12(HESLAR_PREDMET_DRUH, HESLAR_PREDMET_DRUH_KAT)[1:]
        
        self.filters["oblast"].extra["choices"]= OBLAST_CHOICES

        self.set_filter_fields(user)
        self.helper = SamostatnyNalezFilterFormHelper()

    def filter_queryset(self, queryset):
        logger.debug("pas.filters.SamostatnyNalezFilter.filter_queryset.start")
        historie = self._get_history_subquery()
        queryset = super(SamostatnyNalezFilter, self).filter_queryset(queryset)
        if historie:
            queryset_history = Q(historie__typ_vazby=historie["typ_vazby"])
            if "uzivatel" in historie:
                queryset_history &= Q(historie__historie__uzivatel__in=historie["uzivatel"])
            if "uzivatel_organizace" in historie:
                queryset_history &= Q(historie__historie__organizace_snapshot__in
                                      =historie["uzivatel_organizace"])
            if "datum_zmeny__gte" in historie:
                queryset_history &= Q(historie__historie__datum_zmeny__gte=historie["datum_zmeny__gte"])
            if "datum_zmeny__lte" in historie:
                queryset_history &= Q(historie__historie__datum_zmeny__lte=historie["datum_zmeny__lte"])
            if "typ_zmeny" in historie:
                queryset_history &= Q(historie__historie__typ_zmeny__in=historie["typ_zmeny"])
            queryset = queryset.filter(queryset_history)
        logger.debug("pas.filters.SamostatnyNalezFilter.filter_queryset.end", extra={"query": str(queryset.query)})
        return queryset

    def filter_obdobi(self, queryset, name, value):
        """
        Metóda pro filtrování podle období.
        """
        return queryset.filter(obdobi__in=value)

    def filter_druh_nalezu(self, queryset, name, value):
        """
        Metóda pro filtrování podle druhu nálezu.
        """
        return queryset.filter(druh_nalezu__in=value)

    def filter_popisne_udaje(self, queryset, name, value):
        """
        Metóda pro filtrování podle lokalizace, poznámek a evidenčního čísla.
        """
        return queryset.filter(
            Q(lokalizace__icontains=value)
            | Q(poznamka__icontains=value)
            | Q(evidencni_cislo__icontains=value)
        )

    def filter_by_oblast(self, queryset, name, value):
        """
        Metóda pro filtrování podle oblasti.
        """
        if value == OBLAST_CECHY:
            return queryset.filter(ident_cely__contains="C-")
        if value == OBLAST_MORAVA:
            return queryset.filter(ident_cely__contains="M-")
        return queryset


class UzivatelSpolupraceFilter(HistorieFilter, filters.FilterSet):
    """
    Třída pro zakladní filtrování uživatelské spolupráce a jejich potomků.
    """
    vedouci = ModelMultipleChoiceFilter(
        queryset=User.objects.select_related("organizace"),
        field_name="vedouci",
        label=_("pas.filters.uzivatelSpolupraceFilter.vedouci.label"),
        widget=autocomplete.ModelSelect2Multiple(url="uzivatel:uzivatel-autocomplete"),
    )

    spolupracovnik = ModelMultipleChoiceFilter(
        queryset=User.objects.select_related("organizace"),
        field_name="spolupracovnik",
        label=_("pas.filters.uzivatelSpolupraceFilter.spolupracovnik.label"),
        widget=autocomplete.ModelSelect2Multiple(url="uzivatel:uzivatel-autocomplete"),
    )

    stav = MultipleChoiceFilter(
        choices=UzivatelSpoluprace.SPOLUPRACE_STATES,
        label=_("pas.filters.UzivatelSpolupraceFilter.stav.label"),
        widget=SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
        ),
    )

    class Meta:
        model = UzivatelSpoluprace
        fields = ["stav"]

    def __init__(self, *args, **kwargs):
        super(UzivatelSpolupraceFilter, self).__init__(*args, **kwargs)
        user: User = kwargs.get("request").user
        if user.hlavni_role.pk in (ROLE_ADMIN_ID, ROLE_ARCHIVAR_ID):
            self.filters["vedouci"] = ModelMultipleChoiceFilter(
                queryset=User.objects.select_related("organizace"),
                field_name="vedouci",
                label=_("pas.filters.spolupraceFilter.vedouci.label"),
                widget=autocomplete.ModelSelect2Multiple(url="uzivatel:uzivatel-autocomplete")
            )
            self.filters["spolupracovnik"] = ModelMultipleChoiceFilter(
                queryset=User.objects.select_related("organizace"),
                field_name="spolupracovnik",
                label=_("pas.filters.spolupraceFilter.spolupracovnik.label"),
                widget=autocomplete.ModelSelect2Multiple(url="uzivatel:uzivatel-autocomplete")
            )
        else:
            self.filters["vedouci"] = ModelMultipleChoiceFilter(
                queryset=User.objects.select_related("organizace"),
                field_name="vedouci",
                label=_("pas.filters.spolupraceFilter.vedouci.label"),
                widget=autocomplete.ModelSelect2Multiple(url="uzivatel:uzivatel-autocomplete-public"),
            )
            self.filters["spolupracovnik"] = ModelMultipleChoiceFilter(
                queryset=User.objects.select_related("organizace"),
                field_name="spolupracovnik",
                label=_("pas.filters.spolupraceFilter.spolupracovnik.label"),
                widget=autocomplete.ModelSelect2Multiple(url="uzivatel:uzivatel-autocomplete-public"),
            )
        try:
            self.filters["vedouci"].extra.update(
                {
                    "queryset": User.objects.select_related("organizace").filter(
                        groups__id=Group.objects.get(id=ROLE_ARCHEOLOG_ID).pk
                    )
                }
            )
        except utils.ProgrammingError as err:
            self.filters["vedouci"].extra.update({"queryset": None})
        self.helper = UzivatelSpolupraceFilterFormHelper()


class SamostatnyNalezFilterFormHelper(crispy_forms.helper.FormHelper):
    """
    Třída pro správne zobrazení filtru.
    """
    form_method = "GET"
    def __init__(self, form=None):
        history_divider = u"<span class='app-divider-label'>%(translation)s</span>" % {
            "translation": _(u"pas.filters.samostatnyNalezFilterFormHelper.history.divider.label")
        }
        self.layout = Layout(
            Div(
                Div(
                    Div("ident_cely", css_class="col-sm-2"),
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
                    Div("historie_uzivatel_organizace", css_class="col-sm-3"),
                    id="historieCollapse",
                    css_class="collapse row",
                ),
            ),
        )
        self.form_tag = False
        super().__init__(form)


class UzivatelSpolupraceFilterFormHelper(crispy_forms.helper.FormHelper):
    """
    Třída pro správne zobrazení filtru.
    """
    form_method = "GET"
    def __init__(self, form=None):
        self.layout = Layout(
            Div(
                Div("vedouci", css_class="col-sm-4"),
                Div("spolupracovnik", css_class="col-sm-4"),
                Div("stav", css_class="col-sm-4"),
                css_class="row",
            ),
        )
        self.form_tag = False
        super().__init__(form)
