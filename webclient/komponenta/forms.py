import logging

from core.forms import TwoLevelSelectField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout
from django import forms
from django.utils.translation import gettext as _
from heslar.hesla import HESLAR_AKTIVITA
from heslar.models import Heslar
from komponenta.models import Komponenta

logger = logging.getLogger(__name__)


class CreateKomponentaForm(forms.ModelForm):
    class Meta:
        model = Komponenta
        fields = ("presna_datace", "poznamka", "jistota", "aktivity", "obdobi", "areal")

        labels = {
            "presna_datace": _("Přesná datace"),
            "jistota": _("Nejistá datace"),
            "aktivity": _("Aktivity"),
            "poznamka": _("Poznámka"),
        }

        widgets = {
            "poznamka": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "presna_datace": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "jistota": forms.CheckboxInput(),
            "aktivity": forms.SelectMultiple(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
        }

    def __init__(self, obdobi_choices, areal_choices, *args, readonly=False, **kwargs):
        super(CreateKomponentaForm, self).__init__(*args, **kwargs)
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
        self.fields["aktivity"].required = False
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div("obdobi", css_class="col-sm-6"),
                Div("jistota", css_class="col-sm-6"),
                Div("presna_datace", css_class="col-sm-6"),
                Div("areal", css_class="col-sm-6"),
                Div("aktivity", css_class="col-sm-6"),
                Div("poznamka", css_class="col-sm-12"),
                css_class="row",
            ),
        )
        self.helper.form_tag = False
        for key in self.fields.keys():
            self.fields[key].disabled = readonly
            if self.fields[key].disabled == True:
                if isinstance(self.fields[key].widget, forms.widgets.Select):
                    self.fields[key].widget.template_name = "core/select_to_text.html"
