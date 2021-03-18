from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Layout, Submit
from django import forms
from django.utils.translation import gettext as _
from dokument.models import Dokument


class EditDokumentForm(forms.ModelForm):
    class Meta:
        model = Dokument
        fields = (
            "organizace",
            "rok_vzniku",
            "material_originalu",
            "typ_dokumentu",
            "popis",
            "poznamka",
            "ulozeni_originalu",
            "oznaceni_originalu",
            "pristupnost",
            "datum_zverejneni",
            "posudky",
            "jazyky",
        )
        widgets = {}
        labels = {
            "organizace": _("Organizace"),
            "rok_vzniku": _("Rok vzniku"),
            "material_originalu": _("Materiál originálu"),
            "typ_dokumentu": _("Typ dokumentu"),
            "popis": _("Popis"),
            "poznamka": _("Poznámka"),
            "ulozeni_originalu": _("Uložení originálu"),
            "oznaceni_originalu": _("Označení originálu"),
            "pristupnost": _("Přístupnost"),
            "datum_zverejneni": _("Datum zveřejnění"),
        }

    def __init__(self, *args, **kwargs):
        super(EditDokumentForm, self).__init__(*args, **kwargs)
        # self.fields["jazyky"] = forms.MultipleChoiceField(
        #     label=_("Jazyky"),
        #     required=False,
        #     choices=Heslar.objects.filter(nazev_heslare=HESLAR_JAZYK_DOKUMENTU).values_list("id", "heslo"),
        # )
        # self.fields["posudky"] = forms.MultipleChoiceField(
        #     label=_("Posudky"),
        #     required=False,
        #     choices=Heslar.objects.filter(nazev_heslare=HESLAR_POSUDEK).values_list("id", "heslo"),
        # )
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div(
                    HTML(_("Editace dokumentu")),
                    css_class="card-header",
                ),
                Div(
                    Div(
                        Div("organizace", css_class="col-sm-6"),
                        Div("rok_vzniku", css_class="col-sm-6"),
                        css_class="row",
                    ),
                    Div(
                        Div("material_originalu", css_class="col-sm-6"),
                        Div("typ_dokumentu", css_class="col-sm-6"),
                        css_class="row",
                    ),
                    Div(
                        Div("popis", css_class="col-sm-6"),
                        Div("poznamka", css_class="col-sm-6"),
                        css_class="row",
                    ),
                    Div(
                        Div("ulozeni_originalu", css_class="col-sm-6"),
                        Div("oznaceni_originalu", css_class="col-sm-6"),
                        css_class="row",
                    ),
                    Div(
                        Div("pristupnost", css_class="col-sm-6"),
                        Div("datum_zverejneni", css_class="col-sm-6"),
                        css_class="row",
                    ),
                    "jazyky",
                    "posudky",
                    Div(
                        FormActions(
                            Submit("save", "Upravit"),
                        )
                    ),
                    css_class="card-body",
                ),
                css_class="card",
            )
        )
