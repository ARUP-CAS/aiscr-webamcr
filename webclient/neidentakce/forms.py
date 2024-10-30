import logging

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout
from dal import autocomplete
from django import forms
from django.utils.translation import gettext_lazy as _

from .models import NeidentAkce

logger = logging.getLogger(__name__)


class NeidentAkceForm(forms.ModelForm):
    """
    Hlavní formulář pro editaci a zobrazení neident akce.
    """

    class Meta:
        model = NeidentAkce
        fields = (
            "katastr",
            "vedouci",
            "rok_zahajeni",
            "rok_ukonceni",
            "pian",
            "lokalizace",
            "popis",
            "poznamka",
        )
        widgets = {
            "katastr": autocomplete.ModelSelect2(
                url="heslar:katastr-autocomplete",
            ),
            "vedouci": autocomplete.ModelSelect2Multiple(
                url="heslar:osoba-autocomplete",
            ),
            "pian": forms.TextInput(),
            "lokalizace": forms.TextInput(),
            "popis": forms.TextInput(),
            "poznamka": forms.TextInput(),
            "rok_zahajeni": forms.DateInput(
                attrs={
                    "class": "dateinput form-control date_roky",
                }
            ),
            "rok_ukonceni": forms.DateInput(
                attrs={
                    "class": "dateinput form-control date_roky",
                }
            ),
        }
        labels = {
            "katastr": _("neidentAkce.forms.neidentAkceForm.katastr.label"),
            "vedouci": _("neidentAkce.forms.neidentAkceForm.vedouci.label"),
            "rok_zahajeni": _("neidentAkce.forms.neidentAkceForm.rok_zahajeni.label"),
            "rok_ukonceni": _("neidentAkce.forms.neidentAkceForm.rok_ukonceni.label"),
            "pian": _("neidentAkce.forms.neidentAkceForm.pian.label"),
            "lokalizace": _("neidentAkce.forms.neidentAkceForm.lokalizace.label"),
            "popis": _("neidentAkce.forms.neidentAkceForm.popis.label"),
            "poznamka": _("neidentAkce.forms.neidentAkceForm.poznamka.label"),
        }
        help_texts = {
            "katastr": _("neidentAkce.forms.neidentAkceForm.katastr.tooltip"),
            "vedouci": _("neidentAkce.forms.neidentAkceForm.vedouci.tooltip"),
            "rok_zahajeni": _("neidentAkce.forms.neidentAkceForm.rok_zahajeni.tooltip"),
            "rok_ukonceni": _("neidentAkce.forms.neidentAkceForm.rok_ukonceni.tooltip"),
            "pian": _("neidentAkce.forms.neidentAkceForm.pian.tooltip"),
            "lokalizace": _("neidentAkce.forms.neidentAkceForm.lokalizace.tooltip"),
            "popis": _("neidentAkce.forms.neidentAkceForm.popis.tooltip"),
            "poznamka": _("neidentAkce.forms.neidentAkceForm.poznamka.tooltip"),
        }

    class Media:
        js = ["/static/static/js/create_osoba_modal.js"]

    def __init__(self, *args, readonly=False, **kwargs):
        super(NeidentAkceForm, self).__init__(*args, **kwargs)
        self.fields["katastr"].required = True
        self.fields["vedouci"].required = False
        self.fields["vedouci"].widget.attrs["id"] = "id_vedouci_modal"
        if readonly is False:
            if "class" in self.fields["katastr"].widget.attrs.keys():
                self.fields["katastr"].widget.attrs["class"] = (
                    str(self.fields["katastr"].widget.attrs["class"]) + " required-next"
                )
            else:
                self.fields["katastr"].widget.attrs["class"] = "required-next"
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div("katastr", css_class="col-sm-4"),
                Div("vedouci", css_class="col-sm-4"),
                Div(css_class="col-sm-4"),
                Div("rok_zahajeni", css_class="col-sm-4"),
                Div("rok_ukonceni", css_class="col-sm-4"),
                Div("pian", css_class="col-sm-4"),
                Div("lokalizace", css_class="col-sm-12"),
                Div("popis", css_class="col-sm-12"),
                Div("poznamka", css_class="col-sm-12"),
                css_class="row",
            ),
        )
        self.helper.form_tag = False
        self.readonly = readonly
        for key in self.fields.keys():
            self.fields[key].disabled = readonly
            if isinstance(self.fields[key].widget, forms.widgets.Select):
                self.fields[key].empty_label = ""
                if self.fields[key].disabled is True:
                    self.fields[key].widget = forms.widgets.Select()
                    self.fields[key].widget.template_name = "core/select_to_text.html"
            if self.fields[key].disabled is True:
                self.fields[key].help_text = ""
                self.fields[key].required = False
