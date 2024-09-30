from django.urls import reverse


from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import AppendedText
from crispy_forms.layout import Div, Layout
from dal import autocomplete

from arch_z.models import ArcheologickyZaznam, ExterniOdkaz
from dokument.forms import AutoriField
from uzivatel.models import Osoba

from .models import ExterniZdroj

import logging


logger = logging.getLogger(__name__)


class ExterniZdrojForm(forms.ModelForm):
    """
    Hlavní formulář pro vytvoření, editaci a zobrazení externího zdroju.
    """
    autori = AutoriField(Osoba.objects.all(), widget=autocomplete.Select2Multiple(
                url="heslar:osoba-autocomplete",
            ),
            label=_("ez.forms.externiZdrojForm.autori.label"),
            help_text=_("ez.forms.externiZdrojForm.autori.tooltip"),
            )
    editori = AutoriField(Osoba.objects.all(), widget=autocomplete.Select2Multiple(
                url="heslar:osoba-autocomplete",
            ),
            label=_("ez.forms.externiZdrojForm.editori.label"),
            help_text=_("ez.forms.externiZdrojForm.editori.tooltip"),)
    class Meta:
        model = ExterniZdroj
        fields = (
            "typ",
            "autori",
            "editori",
            "rok_vydani_vzniku",
            "nazev",
            "casopis_denik_nazev",
            "casopis_rocnik",
            "datum_rd",
            "paginace_titulu",
            "sbornik_nazev",
            "edice_rada",
            "misto",
            "vydavatel",
            "isbn",
            "issn",
            "typ_dokumentu",
            "organizace",
            "link",
            "poznamka",
        )

        labels = {
            "typ": _("ez.forms.externiZdrojForm.typ.label"),
            "rok_vydani_vzniku": _("ez.forms.externiZdrojForm.rokVydaniVzniku.label"),
            "nazev": _("ez.forms.externiZdrojForm.nazev.label"),
            "casopis_denik_nazev": _("ez.forms.externiZdrojForm.casopisNazev.label"),
            "casopis_rocnik": _("ez.forms.externiZdrojForm.casopisRocnik.label"),
            "datum_rd": _("ez.forms.externiZdrojForm.datumRd.label"),
            "paginace_titulu": _("ez.forms.externiZdrojForm.paginaceTitulu.label"),
            "sbornik_nazev": _("ez.forms.externiZdrojForm.sbornikNazev.label"),
            "edice_rada": _("ez.forms.externiZdrojForm.ediceRada.label"),
            "misto": _("ez.forms.externiZdrojForm.misto.label"),
            "vydavatel": _("ez.forms.externiZdrojForm.vydavatel.label"),
            "isbn": _("ez.forms.externiZdrojForm.isbn.label"),
            "issn": _("ez.forms.externiZdrojForm.issn.label"),
            "typ_dokumentu": _("ez.forms.externiZdrojForm.typDokumentu.label"),
            "organizace": _("ez.forms.externiZdrojForm.organizace.label"),
            "link": _("ez.forms.externiZdrojForm.link.label"),
            "poznamka": _("ez.forms.externiZdrojForm.poznamka.label"),
        }

        widgets = {
            "typ": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true",
                       "data-container": ".content-with-table-responsive-container"}
            ),
            "typ_dokumentu": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true",
                       "data-container": ".content-with-table-responsive-container"}
            ),
            "rok_vydani_vzniku": forms.TextInput(),
            "nazev": forms.Textarea(attrs={"rows": 1}),
            "casopis_denik_nazev": forms.Textarea(attrs={"rows": 1}),
            "casopis_rocnik": forms.TextInput(),
            "datum_rd": forms.DateInput(),
            "paginace_titulu": forms.TextInput(),
            "sbornik_nazev": forms.Textarea(attrs={"rows": 1}),
            "edice_rada": forms.TextInput(),
            "misto": forms.TextInput(),
            "vydavatel": forms.TextInput(),
            "isbn": forms.TextInput(),
            "issn": forms.TextInput(),
            "organizace": forms.TextInput(),
            "link": forms.TextInput(),
            "poznamka": forms.TextInput(),
        }

        help_texts = {
            "typ": _("ez.forms.externiZdrojForm.typ.tooltip"),
            "rok_vydani_vzniku": _("ez.forms.externiZdrojForm.rokVydaniVzniku.tooltip"),
            "nazev": _("ez.forms.externiZdrojForm.nazev.tooltip"),
            "casopis_denik_nazev": _("ez.forms.externiZdrojForm.casopisNazev.tooltip"),
            "casopis_rocnik": _("ez.forms.externiZdrojForm.casopisRocnik.tooltip"),
            "datum_rd": _("ez.forms.externiZdrojForm.datumRd.tooltip"),
            "paginace_titulu": _("ez.forms.externiZdrojForm.paginaceTitulu.tooltip"),
            "sbornik_nazev": _("ez.forms.externiZdrojForm.sbornikNazev.tooltip"),
            "edice_rada": _("ez.forms.externiZdrojForm.ediceRada.tooltip"),
            "misto": _("ez.forms.externiZdrojForm.misto.tooltip"),
            "vydavatel": _("ez.forms.externiZdrojForm.vydavatel.tooltip"),
            "isbn": _("ez.forms.externiZdrojForm.isbn.tooltip"),
            "issn": _("ez.forms.externiZdrojForm.issn.tooltip"),
            "typ_dokumentu": _("ez.forms.externiZdrojForm.typDokumentu.tooltip"),
            "organizace": _("ez.forms.externiZdrojForm.organizace.tooltip"),
            "link": _("ez.forms.externiZdrojForm.link.tooltip"),
            "poznamka": _("ez.forms.externiZdrojForm.poznamka.tooltip"),
        }

    def __init__(
        self, *args, required=None, required_next=None, readonly=False, **kwargs
    ):
        super(ExterniZdrojForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        if readonly:
            autori = Div(
                "autori",
                css_class="col-sm-4",
            )
            editori = Div("editori", css_class="col-sm-4")
        else:
            autori = Div(
                AppendedText(
                    "autori",
                    mark_safe('<button id="create-autor" class="btn btn-sm app-btn-in-form" type="button" name="button"><span class="material-icons">add</span></button>'),
                ),
                css_class="col-sm-4 input-osoba select2-input",
            )
            editori = Div(
                AppendedText(
                    "editori",
                    mark_safe('<button id="create-editor" class="btn btn-sm app-btn-in-form" type="button" name="button"><span class="material-icons">add</span></button>'),
                ),
                css_class="col-sm-4 input-osoba select2-input",
            )

        self.helper.layout = Layout(
            Div(
                Div("typ", css_class="col-sm-2"),
                autori,
                editori,
                Div("rok_vydani_vzniku", css_class="col-sm-2"),
                Div("nazev", css_class="col-sm-12"),
                Div("casopis_denik_nazev", css_class="col-sm-6"),
                Div(
                    "casopis_rocnik",
                    css_class="col-sm-2",
                ),
                Div("datum_rd", css_class="col-sm-2"),
                Div("paginace_titulu", css_class="col-sm-2"),
                Div("sbornik_nazev", css_class="col-sm-12"),
                Div("edice_rada", css_class="col-sm-4"),
                Div("misto", css_class="col-sm-2"),
                Div("vydavatel", css_class="col-sm-2"),
                Div("isbn", css_class="col-sm-2"),
                Div("issn", css_class="col-sm-2"),
                Div("typ_dokumentu", css_class="col-sm-2"),
                Div("organizace", css_class="col-sm-2"),
                Div("link", css_class="col-sm-8"),
                Div("poznamka", css_class="col-sm-10"),
                css_class="row",
            ),
        )
        self.helper.form_tag = False
        self.fields["autori"].widget.choices = list(Osoba.objects.filter(
            externizdrojautor__externi_zdroj__pk=self.instance.pk
        ).order_by("externizdrojautor__poradi").values_list("id", "vypis_cely"))
        self.fields["editori"].widget.choices = list(Osoba.objects.filter(
            externizdrojeditor__externi_zdroj__pk=self.instance.pk
        ).order_by("externizdrojeditor__poradi").values_list("id", "vypis_cely"))
        for key in self.fields.keys():
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
                if self.fields[key].disabled is True:
                    if key in ["autori", "editori"]:
                        self.fields[key].widget = forms.widgets.SelectMultiple()
                        self.fields[key].widget.attrs.update(
                            {"name_id": str(key) + ";" + str(self.instance) + ";ez"}
                        )
                    self.fields[key].widget.template_name = "core/select_to_text.html"
            if self.fields[key].disabled is True:
                self.fields[key].help_text = ""
        for key in self.fields.keys():
            # logger.info(key=self.fields[key], widget=self.fields[key].widget)
            if isinstance(self.fields[key].widget, forms.widgets.Textarea) \
                    and hasattr(self.fields[key].widget.attrs, "class"):
                self.fields[key].widget.attrs["class"] = str(self.fields[key].widget.attrs["class"]) \
                                                         + " disabled-text-area"

class ExterniOdkazForm(forms.ModelForm):
    """
    Hlavní formulář pro vytvoření, editaci externího odkazu.
    """
    class Meta:
        model = ExterniOdkaz
        fields = ("paginace",)
        labels = {
            "paginace": _("ez.forms.ExterniOdkazForm.paginace.label"),
        }
        widgets = {
            "paginace": forms.TextInput(),
        }
        help_texts = {
            "paginace": _("ez.forms.ExterniOdkazForm.paginace.tooltip"),
        }

    def __init__(self, type_arch=None, *args, **kwargs):
        super(ExterniOdkazForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False


class PripojitArchZaznamForm(forms.Form, ExterniOdkazForm):
    """
    Hlavní formulář pro připojení archeologického záznamu.
    """
    def __init__(self, type_arch=None, dok=False, *args, **kwargs):
        super(PripojitArchZaznamForm, self).__init__(*args, **kwargs)
        self.fields["paginace"].required = False
        if dok:
            ez_label = _("ez.forms.pripojitArchZaznamForm.dokument.vyberArchz.label")
            ez_tooltip = _("ez.forms.pripojitArchZaznamForm.dokument.vyberArchz.tooltip")
            pagin = Div()
        else:
            ez_label = _("ez.forms.pripojitArchZaznamForm.ez.vyberArchz.label")
            ez_tooltip = _("ez.forms.pripojitArchZaznamForm.ez.vyberArchz.tooltip")
            pagin = Div("paginace", css_class="col-sm-4")
        if type_arch == "akce":
            new_choices = list(
                ArcheologickyZaznam.objects.filter(
                    typ_zaznamu=ArcheologickyZaznam.TYP_ZAZNAMU_AKCE
                ).values_list("id", "ident_cely")
            )
            arch_z_width = "col-sm-10"
        else:
            new_choices = list(
                ArcheologickyZaznam.objects.filter(
                    typ_zaznamu=ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA
                ).values_list("id", "ident_cely")
            )
            arch_z_width = "col-sm-6"
        self.fields["arch_z"] = forms.ChoiceField(
            label=ez_label,
            choices=new_choices,
            widget=autocomplete.ListSelect2(
                url=reverse("arch_z:arch-z-autocomplete", kwargs={"type": type_arch})
            ),
            help_text=ez_tooltip,
        )
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div("arch_z", css_class=arch_z_width),
                pagin,
                css_class="row",
            ),
        )
        self.helper.form_tag = False


class PripojitExterniOdkazForm(forms.Form, ExterniOdkazForm):
    """
    Hlavní formulář pro připojení externího zdroju.
    """
    def __init__(self, *args, **kwargs):
        super(PripojitExterniOdkazForm, self).__init__(*args, **kwargs)
        self.fields["paginace"].required = False
        new_choices = list(
            ExterniZdroj.objects.filter().values_list("id", "ident_cely")
        )
        self.fields["ez"] = forms.ChoiceField(
            label=_("ez.forms.pripojitExterniOdkazForm.vyberEZ.label"),
            help_text=_("ez.forms.pripojitExterniOdkazForm.vyberEZ.tooltip"),
            choices=new_choices,
            widget=autocomplete.ListSelect2(url=reverse("ez:ez-autocomplete")),
        )
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div("ez", css_class="col-sm-8"),
                Div("paginace", css_class="col-sm-4"),
                css_class="row",
            ),
        )
        self.helper.form_tag = False
