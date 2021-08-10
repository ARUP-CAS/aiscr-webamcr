import logging

import crispy_forms
import django_filters as filters
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
    HESLAR_OBDOBI,
    HESLAR_OBDOBI_KAT,
    HESLAR_DOKUMENT_TYP,
    HESLAR_DOKUMENT_FORMAT,
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

logger = logging.getLogger(__name__)


class DokumentFilter(filters.FilterSet):

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

    autor = MultipleChoiceFilter(
        choices=Osoba.objects.all().values_list("id", "vypis_cely"),
        label=_("Autor"),
        field_name="autori",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
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
    )
    popisne_udaje = CharFilter(
        label=_("Popisné údaje"),
        method="filter_popisne_udaje",
    )

    zeme = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_ZEME),
        field_name="extra_data__zeme",
        label=_("Země"),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )

    obdobi = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(
            nazev_heslare=HESLAR_OBDOBI
        ),  # nezda se mi pouziti obou hesel - plati i pro create a edit
        field_name="casti__komponenty__komponenty__obdobi",
        label=_("Období"),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )

    areal = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(
            nazev_heslare=HESLAR_AREAL
        ),  # nezda se mi pouziti obou hesel - plati i pro create a edit
        field_name="casti__komponenty__komponenty__areal",
        label=_("Areál"),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
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
    )

    predmet_druh = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(
            nazev_heslare=HESLAR_PREDMET_DRUH
        ),  # nezda se mi pouziti obou hesel - plati i pro create a edit
        field_name="casti__komponenty__komponenty__predmety__druh",
        label=_("Druh předmětu"),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
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
    )
    objekt_druh = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(
            nazev_heslare=HESLAR_OBJEKT_DRUH
        ),  # nezda se mi pouziti obou hesel - plati i pro create a edit
        field_name="casti__komponenty__komponenty__objekty__druh",
        label=_("Druh objektu"),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )

    objekt_specifikace = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(
            nazev_heslare=HESLAR_OBJEKT_SPECIFIKACE
        ),  # nezda se mi pouziti obou hesel - plati i pro create a edit
        field_name="casti__komponenty__komponenty__objekty__specifikace",
        label=_("Specifikace objektu"),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
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
    )

    historie_datum_zmeny_od = DateFromToRangeFilter(
        label="Datum změny (od-do)",
        field_name="historie__historie__datum_zmeny",
        widget=DateRangeWidget(attrs={"type": "date"}),
    )

    historie_uzivatel = MultipleChoiceFilter(
        choices=[(user.id, str(user)) for user in User.objects.all()],
        field_name="historie__historie__uzivatel",
        label="Uživatel",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
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
                HTML(_('<span class="app-divider-label">Výběr podle historie</span>')),
                HTML(_('<hr class="mt-0" />')),
                css_class="col-sm-12",
            ),
            Div(
                Div("historie_typ_zmeny", css_class="col-sm-2"),
                Div(
                    "historie_datum_zmeny_od", css_class="col-sm-4 app-daterangepicker"
                ),
                Div("historie_uzivatel", css_class="col-sm-2"),
                css_class="row",
            ),
        ),
    )
    form_tag = False
