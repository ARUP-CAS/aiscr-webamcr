import logging

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout
from dal import autocomplete
from django.db.models import Q

from dj.models import DokumentacniJednotka
from django import forms
from django.utils.translation import gettext as _
from heslar.models import Heslar
from heslar.hesla import HESLAR_DJ_TYP

logger = logging.getLogger(__name__)

class MyAutocompleteWidget(autocomplete.ModelSelect2):
    def media(self):
        return ()


class CreateDJForm(forms.ModelForm):
    def get_typ_queryset(self, jednotky, instance: DokumentacniJednotka=None):
        queryset = Heslar.objects.filter(nazev_heslare=HESLAR_DJ_TYP)
        logger.debug(jednotky)
        if instance is not None and jednotky is not None and hasattr(instance, "typ") \
                and instance.typ is not None and instance.typ.heslo.lower() == "část akce":
            queryset = queryset.filter(Q(heslo__iexact="část akce"))
        elif jednotky is not None:
            if jednotky.filter(typ__heslo__iexact="sonda").count() > 0:
                if instance.ident_cely is None:
                    queryset = queryset.filter(heslo__iexact="sonda")
                elif jednotky.filter(Q(typ__heslo__iexact="sonda") & Q(ident_cely__lt=instance.ident_cely)).count() > 0:
                    queryset = queryset.filter(heslo__iexact="sonda")
                else:
                    queryset = queryset.filter(Q(heslo__iexact="sonda") | Q(heslo__iexact="celek akce"))
            elif hasattr(instance, "typ") and instance.typ.heslo == "Celek akce":
                queryset = queryset.filter(Q(heslo__iexact="sonda") | Q(heslo__iexact="celek akce"))
            elif jednotky.filter(typ__heslo__iexact="část akce").count() > 0:
                if jednotky.filter(typ__heslo__iexact="celek akce").count() > 0:
                    queryset = queryset.filter(heslo__iexact="část akce")
                else:
                    queryset = queryset.filter(Q(heslo__iexact="část akce") | Q(heslo__iexact="celek akce"))
            elif jednotky.filter(typ__heslo__iexact="celek akce").count() > 0:
                queryset = queryset.filter(heslo__iexact="část akce")

        logger.debug(queryset)
        return queryset

    class Meta:
        model = DokumentacniJednotka
        fields = ("typ", "negativni_jednotka", "nazev", "pian")

        labels = {
            "typ": _("Typ"),
            "negativni_jednotka": _("Negativní zjištění"),
            "nazev": _("Název"),
            "pian": _("Pian"),
        }

        widgets = {
            "nazev": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "pian": MyAutocompleteWidget(url="pian:pian-autocomplete"),
        }

    def __init__(
        self,
        *args,
        not_readonly=True,
        **kwargs,
    ):
        jednotky = kwargs.pop("jednotky", None)
        super(CreateDJForm, self).__init__(*args, **kwargs)
        self.fields["typ"] = forms.ModelChoiceField(queryset=self.get_typ_queryset(jednotky, self.instance))
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Div("typ", css_class="col-sm-3"),
                Div("nazev", css_class="col-sm-3"),
                Div("negativni_jednotka", css_class="col-sm-3"),
                Div("pian", css_class="col-sm-3"),
                css_class="row align-items-end",
            ),
        )
        for key in self.fields.keys():
            self.fields[key].disabled = not not_readonly
            if isinstance(self.fields[key].widget, forms.widgets.Select):
                self.fields[key].empty_label = ""
                if self.fields[key].disabled == True:
                    self.fields[key].widget.template_name = "core/select_to_text.html"
