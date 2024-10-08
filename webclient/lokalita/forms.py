import logging

from core.forms import TwoLevelSelectField
from django import forms
from django.utils.translation import gettext_lazy as _
from heslar.hesla import HESLAR_LOKALITA_DRUH, HESLAR_LOKALITA_KAT
from heslar.models import HeslarHierarchie
from heslar.views import heslar_12

from .models import Lokalita

logger = logging.getLogger(__name__)


class LokalitaForm(forms.ModelForm):
    """
    Hlavní formulář pro vytvoření, editaci a zobrazení lokality.
    """

    typ_lokality_disp = forms.CharField(
        label=_("lokalita.forms.typLokality.label"),
        help_text=_("lokalita.forms.typLokality.tooltip"),
        required=False,
    )

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
            "typ_lokality": forms.Select(attrs={"class": "selectpicker", "data-live-search": "true"}),
            "zachovalost": forms.Select(attrs={"class": "selectpicker", "data-live-search": "true"}),
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

    def __init__(self, *args, required=None, required_next=None, readonly=False, detail=False, **kwargs):
        super(LokalitaForm, self).__init__(*args, **kwargs)
        if self.instance.pk is not None:
            nadrazene = HeslarHierarchie.objects.filter(
                heslo_nadrazene=self.instance.typ_lokality, typ="podřízenost"
            ).values_list("heslo_podrazene", flat=True)
            choices = heslar_12(HESLAR_LOKALITA_DRUH, HESLAR_LOKALITA_KAT, nadrazene)
            self.fields["typ_lokality_disp"].initial = self.instance.typ_lokality
        else:
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
                    self.fields[key].widget.attrs["class"] = str(self.fields[key].widget.attrs["class"]) + (
                        " required-next" if key in required_next else ""
                    )
                else:
                    self.fields[key].widget.attrs["class"] = "required-next" if key in required_next else ""
            if isinstance(self.fields[key].widget, forms.widgets.Select):
                self.fields[key].empty_label = ""
                if self.fields[key].disabled:
                    self.fields[key].widget.template_name = "core/select_to_text.html"
            if self.fields[key].disabled is True:
                self.fields[key].help_text = ""
        self.fields["typ_lokality_disp"].disabled = True
