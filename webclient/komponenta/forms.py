import logging

from core.forms import TwoLevelSelectField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout
from django import forms
from django.utils.translation import gettext_lazy as _
from heslar.hesla import HESLAR_AKTIVITA
from heslar.models import Heslar
from komponenta.models import Komponenta

logger = logging.getLogger(__name__)


class CreateKomponentaForm(forms.ModelForm):
    """
    Hlavní formulář pro vytvoření, editaci a zobrazení komponenty.
    """

    class Meta:
        model = Komponenta
        fields = ("presna_datace", "poznamka", "jistota", "aktivity", "obdobi", "areal")

        labels = {
            "presna_datace": _("komponenta.forms.createKomponentaForm.presna_datace.label"),
            "jistota": _("komponenta.forms.createKomponentaForm.jistota.label"),
            "aktivity": _("komponenta.forms.createKomponentaForm.aktivity.label"),
            "poznamka": _("komponenta.forms.createKomponentaForm.poznamka.label"),
        }

        widgets = {
            "poznamka": forms.TextInput(),
            "presna_datace": forms.TextInput(),
            "jistota": forms.Select(
                choices=[
                    (True, _("komponenta.forms.createKomponentaForm.choices.true")),
                    (False, _("komponenta.forms.createKomponentaForm.choices.false")),
                ],
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"},
            ),
            "aktivity": forms.SelectMultiple(
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
            ),
        }
        help_texts = {
            "presna_datace": _("komponenta.forms.createKomponentaForm.presna_datace.tooltip"),
            "jistota": _("komponenta.forms.createKomponentaForm.jistota.tooltip"),
            "aktivity": _("komponenta.forms.createKomponentaForm.aktivity.tooltip"),
            "poznamka": _("komponenta.forms.createKomponentaForm.poznamka.tooltip"),
        }

    def __init__(
        self, obdobi_choices, areal_choices, *args, readonly=False, required=None, required_next=None, **kwargs
    ):
        super(CreateKomponentaForm, self).__init__(*args, **kwargs)
        self.fields["obdobi"] = TwoLevelSelectField(
            label=_("komponenta.form.createKomponentaForm.obdobi.label"),
            widget=forms.Select(
                choices=obdobi_choices,
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"},
            ),
            help_text=_("komponenta.form.createKomponentaForm.obdobi.tooltip"),
        )
        self.fields["areal"] = TwoLevelSelectField(
            label=_("komponenta.form.createKomponentaForm.areal.label"),
            widget=forms.Select(
                choices=areal_choices,
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"},
            ),
            help_text=_("komponenta.form.createKomponentaForm.areal.tooltip"),
        )
        self.fields["aktivity"].queryset = Heslar.objects.filter(nazev_heslare=HESLAR_AKTIVITA)
        self.fields["aktivity"].required = False
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div("obdobi", css_class="col-sm-2"),
                Div("jistota", css_class="col-sm-2"),
                Div("presna_datace", css_class="col-sm-2"),
                Div("areal", css_class="col-sm-2"),
                Div("aktivity", css_class="col-sm-4"),
                Div("poznamka", css_class="col-sm-12"),
                css_class="row",
            ),
        )
        self.helper.form_tag = False
        for key in self.fields.keys():
            self.fields[key].disabled = readonly
            if self.fields[key].disabled:
                if isinstance(self.fields[key].widget, forms.widgets.Select):
                    self.fields[key].widget.template_name = "core/select_to_text.html"
                self.fields[key].help_text = ""
                self.fields[key].required = False
            if required or required_next:
                self.fields[key].required = True if key in required else False
                if "class" in self.fields[key].widget.attrs.keys():
                    self.fields[key].widget.attrs["class"] = str(self.fields[key].widget.attrs["class"]) + (
                        " required-next" if key in required_next else ""
                    )
                else:
                    self.fields[key].widget.attrs["class"] = "required-next" if key in required_next else ""
