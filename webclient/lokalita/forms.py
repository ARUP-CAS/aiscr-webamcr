import structlog

from django import forms
from django.utils.translation import gettext as _

from core.forms import TwoLevelSelectField
from heslar.hesla import HESLAR_LOKALITA_DRUH, HESLAR_LOKALITA_KAT
from heslar.views import heslar_12

from .models import Lokalita

logger_s = structlog.get_logger(__name__)


class LokalitaForm(forms.ModelForm):
    class Meta:
        model = Lokalita
        fields = (
            "druh",
            "nazev",
            "typ_lokality",
            "zachovalost",
            "jistota",
            "popis",
            "poznamka",
        )

        labels = {
            "nazev": _("lokalita.forms.nazev.label"),
            "typ_lokality": _("lokalita.forms.typLokality.label"),
            "zachovalost": _("lokalita.forms.zachovalost.label"),
            "jistota": _("lokalita.forms.jistota.label"),
            "popis": _("lokalita.forms.popis.label"),
            "poznamka": _("lokalita.forms.poznamka.label"),
        }

        widgets = {
            "typ_lokality": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
            "zachovalost": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
            "nazev": forms.TextInput(),
            "popis": forms.Textarea(attrs={"rows": 4, "cols": 40}),
            "poznamka": forms.Textarea(attrs={"rows": 4, "cols": 40}),
            "jistota": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"},
            ),
        }

        help_texts = {
            "nazev": _("lokalita.forms.nazev.tooltip"),
            "typ_lokality": _("lokalita.forms.typLokality.tooltip"),
            "zachovalost": _("lokalita.forms.zachovalost.tooltip"),
            "jistota": _("lokalita.forms.jistota.tooltip"),
            "popis": _("lokalita.forms.popis.tooltip"),
            "poznamka": _("lokalita.forms.poznamka.tooltip"),
        }

    def __init__(
        self,
        *args,
        required=None,
        required_next=None,
        readonly=False,
        detail=False,
        **kwargs
    ):
        super(LokalitaForm, self).__init__(*args, **kwargs)
        choices = heslar_12(HESLAR_LOKALITA_DRUH, HESLAR_LOKALITA_KAT)
        self.fields["druh"] = TwoLevelSelectField(
            label=_("lokalita.forms.druh.label"),
            widget=forms.Select(
                choices=choices,
                attrs={
                    "class": "selectpicker",
                    "data-multiple-separator": "; ",
                    "data-live-search": "true",
                },
            ),
            help_text=_("lokalita.forms.druh.tooltip"),
        )

        for key in self.fields.keys():
            if detail:
                self.fields[key].required = not detail
            self.fields[key].disabled = readonly
            if required or required_next:
                self.fields[key].required = True if key in required else False
                if "class" in self.fields[key].widget.attrs.keys():
                    self.fields[key].widget.attrs["class"] = str(
                        self.fields[key].widget.attrs["class"]
                    ) + (" required-next" if key in required_next else "")
                else:
                    self.fields[key].widget.attrs["class"] = (
                        "required-next" if key in required_next else ""
                    )
            if isinstance(self.fields[key].widget, forms.widgets.Select):
                self.fields[key].empty_label = ""
                if self.fields[key].disabled == True:
                    self.fields[key].widget.template_name = "core/select_to_text.html"
            if self.fields[key].disabled is True:
                self.fields[key].help_text = ""