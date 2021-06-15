import logging

import crispy_forms
import django_filters as filters
from crispy_forms.layout import Div, Layout
from django.forms import SelectMultiple
from django_filters import CharFilter, ModelMultipleChoiceFilter, MultipleChoiceFilter
from pas.models import SamostatnyNalez
from uzivatel.models import User

logger = logging.getLogger(__name__)


class SamostatnyNalezFilter(filters.FilterSet):

    ident_cely = CharFilter(lookup_expr="icontains")
    stav = MultipleChoiceFilter(
        choices=SamostatnyNalez.PAS_STATES,
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )
    vlastnik = ModelMultipleChoiceFilter(
        queryset=User.objects.select_related("organizace").all(),
        field_name="historie__historie__uzivatel",
        label="Vlastník",
        widget=SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )

    class Meta:
        model = SamostatnyNalez
        fields = ["ident_cely", "predano_organizace"]

    def __init__(self, *args, **kwargs):
        super(SamostatnyNalezFilter, self).__init__(*args, **kwargs)
        self.helper = SamostatnyNalezFilterFormHelper()


class SamostatnyNalezFilterFormHelper(crispy_forms.helper.FormHelper):
    form_method = "GET"
    layout = Layout(
        Div(
            Div("ident_cely", css_class="col-sm-4"),
            Div("stav", css_class="col-sm-4"),
            Div("predano_organizace", css_class="col-sm-4"),
            css_class="row",
        ),
    )
    form_tag = False
