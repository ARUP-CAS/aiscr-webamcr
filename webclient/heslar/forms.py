import logging

from dal import autocomplete, forward
from django import forms
from django.utils.translation import gettext_lazy as _
from heslar.models import HeslarHierarchie, HeslarNazev, HeslarOdkaz

logger = logging.getLogger(__name__)


class HeslarHierarchieForm(forms.ModelForm):
    heslar_nazev_podrazene = forms.ModelChoiceField(
        empty_label=None,
        label=_("heslar.forms.heslarOdkazForm.heslar_nazev_podrazene.label"),
        help_text=_("heslar.forms.heslarOdkazForm.heslar_nazev_podrazene.tooltip"),
        widget=autocomplete.ModelSelect2(url="heslar:heslar_nazev-autocomplete"),
        queryset=HeslarNazev.objects.all(),
        required=False,
    )
    heslar_nazev_nadrazene = forms.ModelChoiceField(
        empty_label=None,
        label=_("heslar.forms.heslarOdkazForm.heslar_nazev_nadrazene.label"),
        help_text=_("heslar.forms.heslarOdkazForm.heslar_nazev_nadrazene.tooltip"),
        widget=autocomplete.ModelSelect2(url="heslar:heslar_nazev-autocomplete"),
        queryset=HeslarNazev.objects.all(),
        required=False,
    )

    class Meta:
        model = HeslarHierarchie
        fields = (
            "heslo_podrazene",
            "heslo_nadrazene",
            "typ",
        )
        widgets = {
            "heslo_podrazene": autocomplete.ModelSelect2(
                url="heslar:heslar-autocomplete", forward=(forward.Field("heslar_nazev_podrazene", "heslar_nazev"),)
            ),
            "heslo_nadrazene": autocomplete.ModelSelect2(
                url="heslar:heslar-autocomplete", forward=(forward.Field("heslar_nazev_nadrazene", "heslar_nazev"),)
            ),
        }

    def __init__(self, *args, **kwargs):
        super(HeslarHierarchieForm, self).__init__(*args, **kwargs)
        logger.debug(self.instance)
        if self.instance.pk is not None:
            self.fields["heslar_nazev_podrazene"].initial = self.instance.heslo_podrazene.nazev_heslare
            self.fields["heslar_nazev_nadrazene"].initial = self.instance.heslo_nadrazene.nazev_heslare


class HeslarOdkazForm(forms.ModelForm):
    heslar_nazev = forms.ModelChoiceField(
        empty_label=None,
        label=_("heslar.forms.heslarOdkazForm.heslar_nazev.label"),
        help_text=_("heslar.forms.heslarOdkazForm.heslar_nazev.tooltip"),
        widget=autocomplete.ModelSelect2(url="heslar:heslar_nazev-autocomplete"),
        queryset=HeslarNazev.objects.all(),
        required=False,
    )

    class Meta:
        model = HeslarOdkaz
        fields = "heslo", "zdroj", "nazev_kodu", "kod", "uri", "skos_mapping_relation"
        widgets = {"heslo": autocomplete.ModelSelect2(url="heslar:heslar-autocomplete", forward=["heslar_nazev"])}

    def __init__(self, *args, **kwargs):
        super(HeslarOdkazForm, self).__init__(*args, **kwargs)
        logger.debug(self.instance)
        if self.instance.pk is not None:
            self.fields["heslar_nazev"].initial = self.instance.heslo.nazev_heslare
