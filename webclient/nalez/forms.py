from core.forms import HeslarChoiceFieldField, TwoLevelSelectField
from crispy_forms.helper import FormHelper
from django import forms
from django.utils.translation import gettext_lazy as _
from nalez.models import NalezObjekt, NalezPredmet


class NalezFormSetHelper(FormHelper):
    """Implementuje komponentu ``NalezFormSetHelper`` v rámci aplikace."""

    def __init__(self, typ=None, typ_vazby="dokument", *args, **kwargs):
        """
        Inicializuje instanci třídy.

        :param typ: Vstupní hodnota ``typ`` pro danou operaci.
        :param typ_vazby: Vstupní hodnota ``typ_vazby`` pro danou operaci.
        :param args: Dodatečné poziční argumenty předané voláním.
        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        """
        super().__init__(*args, **kwargs)
        self.template = "inline_formset.html"
        self.form_tag = False
        self.form_id = typ
        self.typ_vazby = typ_vazby


# Funkce bude podtříděna, aby šlo předat volby do formsetů při volání formsetfactory.
def create_nalez_objekt_form(druh_obj_choices, spec_obj_choices, not_readonly=True):
    """
    Funkce která vrací formulář nálezu objekty pro formset.

    :param druh_obj_choices: Popis parametru ``druh_obj_choices``.
    :param spec_obj_choices: Popis parametru ``spec_obj_choices``.
    :param not_readonly: Popis parametru ``not_readonly``.
    """

    class CreateNalezObjektForm(forms.ModelForm):
        """Implementuje komponentu ``CreateNalezObjektForm`` v rámci aplikace."""

        typ = forms.CharField(widget=forms.HiddenInput())

        class Meta:
            """Implementuje komponentu ``Meta`` v rámci aplikace."""

            model = NalezObjekt
            fields = ["druh", "specifikace", "pocet", "poznamka"]
            labels = {
                "pocet": _("nalez.forms.nalezObjekt.pocet.label"),
                "poznamka": _("nalez.forms.nalezObjekt.poznamka.label"),
            }
            widgets = {
                "poznamka": forms.TextInput(),
                "pocet": forms.TextInput(),
            }
            help_texts = {
                "pocet": _("nalez.forms.nalezObjekt.pocet.tooltip"),
                "poznamka": _("nalez.forms.nalezObjekt.poznamka.tooltip"),
            }

        def __init__(
            self, druh_objekt_choices=druh_obj_choices, specifikace_objekt_choices=spec_obj_choices, *args, **kwargs
        ):
            """
            Inicializuje instanci třídy.

            :param druh_objekt_choices: Vstupní hodnota ``druh_objekt_choices`` pro danou operaci.
            :param specifikace_objekt_choices: Vstupní hodnota ``specifikace_objekt_choices`` pro danou operaci.
            :param args: Dodatečné poziční argumenty předané voláním.
            :param kwargs: Dodatečné pojmenované argumenty předané voláním.
            """
            super(CreateNalezObjektForm, self).__init__(*args, **kwargs)
            self.fields["druh"] = TwoLevelSelectField(
                label=_("nalez.forms.nalezObjekt.druh.label"),
                widget=forms.Select(
                    choices=druh_objekt_choices,
                    attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"},
                ),
                help_text=_("nalez.forms.nalezObjekt.druh.tooltip"),
            )
            self.fields["specifikace"] = TwoLevelSelectField(
                label=_("nalez.forms.nalezObjekt.specifikace.label"),
                widget=forms.Select(
                    choices=specifikace_objekt_choices,
                    attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"},
                ),
                help_text=_("nalez.forms.nalezObjekt.specifikace.tooltip"),
            )
            self.fields["specifikace"].required = False

            self.fields["typ"].initial = "objekt"

            for key in self.fields.keys():
                self.fields[key].disabled = not not_readonly
                if self.fields[key].disabled:
                    if isinstance(self.fields[key].widget, forms.widgets.Select):
                        self.fields[key].widget.template_name = "core/select_to_text.html"
                    self.fields[key].help_text = ""

            if not not_readonly:
                self.fields["druh"].required = False

    return CreateNalezObjektForm


def create_nalez_predmet_form(druh_projekt_choices, specifikce_predmetu_choices, not_readonly=True):
    """
    Funkce která vrací formulář nálezu předměty pro formset.

    :param druh_projekt_choices: Popis parametru ``druh_projekt_choices``.
    :param specifikce_predmetu_choices: Popis parametru ``specifikce_predmetu_choices``.
    :param not_readonly: Popis parametru ``not_readonly``.
    """

    class CreateNalezPredmetForm(forms.ModelForm):
        """Implementuje komponentu ``CreateNalezPredmetForm`` v rámci aplikace."""

        typ = forms.CharField(widget=forms.HiddenInput())

        class Meta:
            """Implementuje komponentu ``Meta`` v rámci aplikace."""

            model = NalezPredmet

            fields = ["druh", "specifikace", "pocet", "poznamka"]

            labels = {
                "pocet": _("nalez.forms.nalezPredmet.pocet.label"),
                "poznamka": _("nalez.forms.nalezPredmet.poznamka.label"),
            }

            widgets = {
                "poznamka": forms.TextInput(),
                "pocet": forms.TextInput(),
            }
            help_texts = {
                "pocet": _("nalez.forms.nalezPredmet.pocet.tooltip"),
                "poznamka": _("nalez.forms.nalezPredmet.poznamka.tooltip"),
            }

        def __init__(self, *args, **kwargs):
            """
            Inicializuje instanci třídy.

            :param args: Dodatečné poziční argumenty předané voláním.
            :param kwargs: Dodatečné pojmenované argumenty předané voláním.
            """
            super(CreateNalezPredmetForm, self).__init__(*args, **kwargs)
            self.fields["druh"] = TwoLevelSelectField(
                label=_("nalez.forms.nalezPredmet.druh.label"),
                widget=forms.Select(
                    choices=druh_projekt_choices,
                    attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"},
                ),
                help_text=_("nalez.forms.nalezPredmet.druh.tooltip"),
            )
            self.fields["specifikace"] = HeslarChoiceFieldField(
                label=_("nalez.forms.nalezPredmet.specifikace.label"),
                choices=[("", "")] + specifikce_predmetu_choices,
                help_text=_("nalez.forms.nalezPredmet.specifikace.tooltip"),
            )
            self.fields["specifikace"].widget.attrs = {
                "class": "selectpicker",
                "data-multiple-separator": "; ",
                "data-live-search": "true",
            }
            self.fields["specifikace"].required = True

            self.fields["typ"].initial = "predmet"

            for key in self.fields.keys():
                self.fields[key].disabled = not not_readonly
                if self.fields[key].disabled:
                    if isinstance(self.fields[key].widget, forms.widgets.Select):
                        self.fields[key].widget.template_name = "core/select_to_text.html"
                    self.fields[key].help_text = ""
            if not not_readonly:
                self.fields["druh"].required = False
                self.fields["specifikace"].required = False

    return CreateNalezPredmetForm
