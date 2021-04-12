import logging

from core.forms import TwoLevelSelectField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Layout
from django import forms
from django.utils.translation import gettext as _
from heslar.hesla import (
    HESLAR_AKTIVITA,
    HESLAR_AREAL,
    HESLAR_AREAL_KAT,
    HESLAR_OBDOBI,
    HESLAR_OBDOBI_KAT,
)
from heslar.models import Heslar
from heslar.views import heslar_12
from komponenta.models import Komponenta

logger = logging.getLogger(__name__)


class CreateKomponentaForm(forms.ModelForm):
    class Meta:
        model = Komponenta
        fields = ("presna_datace", "poznamka", "jistota", "aktivity", "obdobi", "areal")

        labels = {
            "presna_datace": _("Přesná datace"),
            "poznamka": _("Poznámka"),
            "jistota": _("Jistota"),
            "aktivity": _("Aktivity"),
        }

        widgets = {}

    def __init__(self, *args, **kwargs):
        super(CreateKomponentaForm, self).__init__(*args, **kwargs)
        obdobi_choices = heslar_12(HESLAR_OBDOBI, HESLAR_OBDOBI_KAT)
        areal_choices = heslar_12(HESLAR_AREAL, HESLAR_AREAL_KAT)
        self.fields["obdobi"] = TwoLevelSelectField(
            label=_("Období"),
            widget=forms.Select(
                choices=obdobi_choices,
                attrs={"class": "selectpicker", "data-live-search": "true"},
            ),
        )
        self.fields["areal"] = TwoLevelSelectField(
            label=_("Areál"),
            widget=forms.Select(
                choices=areal_choices,
                attrs={"class": "selectpicker", "data-live-search": "true"},
            ),
        )
        self.fields["aktivity"].queryset = Heslar.objects.filter(
            nazev_heslare=HESLAR_AKTIVITA
        )
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div(
                    Div(
                        Div(
                            HTML(_("Komponenta")),
                            css_class="app-fx app-left",
                        ),
                        css_class="card-header",
                    ),
                    Div(
                        Div(
                            Div("obdobi", css_class="col-sm-6"),
                            Div("presna_datace", css_class="col-sm-6"),
                            css_class="row",
                        ),
                        Div(
                            Div("areal", css_class="col-sm-6"),
                            Div("aktivity", css_class="col-sm-6"),
                            css_class="row",
                        ),
                        Div(
                            Div("poznamka", css_class="col"),
                            css_class="row",
                        ),
                        css_class="card-body",
                    ),
                ),
                css_class="card app-card-form",
            )
        )
        self.helper.form_tag = False
