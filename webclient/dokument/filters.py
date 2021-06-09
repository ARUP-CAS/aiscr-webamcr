import logging

import crispy_forms
import django_filters as filters
from crispy_forms.layout import Div, Layout
from django.forms import SelectMultiple
from django_filters import CharFilter, ModelMultipleChoiceFilter, MultipleChoiceFilter
from dokument.models import Dokument
from heslar.hesla import HESLAR_OBDOBI
from heslar.models import Heslar
from uzivatel.models import Organizace, User

logger = logging.getLogger(__name__)


class DokumentFilter(filters.FilterSet):

    ident_cely = CharFilter(lookup_expr="icontains")

    stav = MultipleChoiceFilter(
        choices=Dokument.STATES,
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )

    organizace = ModelMultipleChoiceFilter(
        # queryset=Organizace.objects.filter(oao=True),
        queryset=Organizace.objects.all(),
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )

    obdobi = ModelMultipleChoiceFilter(
        queryset=Heslar.objects.filter(nazev_heslare=HESLAR_OBDOBI),
        field_name="casti",  # TODO fix
        label="Období",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )

    vlastnik = ModelMultipleChoiceFilter(
        queryset=User.objects.all(),
        field_name="historie__historie__uzivatel",
        label="Vlastník",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )

    class Meta:
        model = Dokument
        fields = [
            "ident_cely",
            "typ_dokumentu",
            "extra_data__duveryhodnost",
            "popis",
        ]

    def __init__(self, *args, **kwargs):
        super(DokumentFilter, self).__init__(*args, **kwargs)
        self.helper = DokumentFilterFormHelper()


class DokumentFilterFormHelper(crispy_forms.helper.FormHelper):
    form_method = "GET"
    layout = Layout(
        Div(
            Div("ident_cely", css_class="col-sm-6"),
            Div("stav", css_class="col-sm-6"),
            Div("typ_dokumentu", css_class="col-sm-6"),
            Div("extra_data__duveryhodnost", css_class="col-sm-6"),
            Div("popis", css_class="col-sm-6"),
            Div("organizace", css_class="col-sm-6"),
            Div("obdobi", css_class="col-sm-6"),
            Div("vlastnik", css_class="col-sm-6"),
            css_class="row",
        ),
    )
    form_tag = False
