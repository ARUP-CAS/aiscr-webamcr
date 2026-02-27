import logging

from core.widgets import AutocompleteListSelect2, AutocompleteModelSelect2
from dal import forward
from django import forms
from django.utils.translation import gettext_lazy as _
from heslar.models import HeslarHierarchie, HeslarNazev, HeslarOdkaz
from pid.fields import OrcidAutocompleteField, RorAutocompleteField, WikiDataAutocompleteField
from pid.forms import FormWithOrcid, FormWithWikidata
from pid.views import WikiDataAutocompleteView
from uzivatel.models import Organizace, Osoba

logger = logging.getLogger(__name__)


class HeslarHierarchieForm(forms.ModelForm):
    """Implementuje komponentu ``HeslarHierarchieForm`` v rámci aplikace."""

    heslar_nazev_podrazene = forms.ModelChoiceField(
        empty_label=None,
        label=_("heslar.forms.heslarOdkazForm.heslar_nazev_podrazene.label"),
        help_text=_("heslar.forms.heslarOdkazForm.heslar_nazev_podrazene.tooltip"),
        widget=AutocompleteModelSelect2(url="heslar:heslar_nazev-autocomplete"),
        queryset=HeslarNazev.objects.all(),
        required=False,
    )
    heslar_nazev_nadrazene = forms.ModelChoiceField(
        empty_label=None,
        label=_("heslar.forms.heslarOdkazForm.heslar_nazev_nadrazene.label"),
        help_text=_("heslar.forms.heslarOdkazForm.heslar_nazev_nadrazene.tooltip"),
        widget=AutocompleteModelSelect2(url="heslar:heslar_nazev-autocomplete"),
        queryset=HeslarNazev.objects.all(),
        required=False,
    )

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        model = HeslarHierarchie
        fields = (
            "heslo_podrazene",
            "heslo_nadrazene",
            "typ",
        )
        widgets = {
            "heslo_podrazene": AutocompleteModelSelect2(
                url="heslar:heslar-autocomplete", forward=(forward.Field("heslar_nazev_podrazene", "heslar_nazev"),)
            ),
            "heslo_nadrazene": AutocompleteModelSelect2(
                url="heslar:heslar-autocomplete", forward=(forward.Field("heslar_nazev_nadrazene", "heslar_nazev"),)
            ),
        }

    def __init__(self, *args, **kwargs):
        """Inicializuje instanci třídy.

        :param args: Dodatečné poziční argumenty předané voláním.
        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        :return: Funkce nevrací hodnotu (``None``)."""
        super(HeslarHierarchieForm, self).__init__(*args, **kwargs)
        logger.debug(self.instance)
        if self.instance.pk is not None:
            self.fields["heslar_nazev_podrazene"].initial = self.instance.heslo_podrazene.nazev_heslare
            self.fields["heslar_nazev_nadrazene"].initial = self.instance.heslo_nadrazene.nazev_heslare


class HeslarOdkazForm(forms.ModelForm):
    """Implementuje komponentu ``HeslarOdkazForm`` v rámci aplikace."""

    heslar_nazev = forms.ModelChoiceField(
        empty_label=None,
        label=_("heslar.forms.heslarOdkazForm.heslar_nazev.label"),
        help_text=_("heslar.forms.heslarOdkazForm.heslar_nazev.tooltip"),
        widget=AutocompleteModelSelect2(url="heslar:heslar_nazev-autocomplete"),
        queryset=HeslarNazev.objects.all(),
        required=False,
    )

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        model = HeslarOdkaz
        fields = "heslo", "zdroj", "nazev_kodu", "kod", "uri", "skos_mapping_relation"
        widgets = {"heslo": AutocompleteModelSelect2(url="heslar:heslar-autocomplete", forward=["heslar_nazev"])}

    def __init__(self, *args, **kwargs):
        """Inicializuje instanci třídy.

        :param args: Dodatečné poziční argumenty předané voláním.
        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        :return: Funkce nevrací hodnotu (``None``)."""
        super(HeslarOdkazForm, self).__init__(*args, **kwargs)
        logger.debug(self.instance)
        if self.instance.pk is not None:
            self.fields["heslar_nazev"].initial = self.instance.heslo.nazev_heslare


class OsobaAdminForm(forms.ModelForm, FormWithOrcid, FormWithWikidata):
    """Implementuje komponentu ``OsobaAdminForm`` v rámci aplikace."""

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        model = Osoba
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        """Inicializuje instanci třídy.

        :param args: Dodatečné poziční argumenty předané voláním.
        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        :return: Funkce nevrací hodnotu (``None``)."""
        super().__init__(*args, **kwargs)
        self.fields["orcid"] = OrcidAutocompleteField(
            widget=AutocompleteListSelect2(url="pid:orcid-autocomplete"),
            label=_("heslar.forms.OsobaAdminForm.orcid.label"),
            instance=self.instance,
            initial_value=args[0].get("orcid") if args else None,
            help_text=_("heslar.forms.OsobaAdminForm.orcid.tooltip"),
        )
        try:
            WikiDataAutocompleteView.api_call("test")
            self.fields["wikidata"] = WikiDataAutocompleteField(
                widget=AutocompleteListSelect2(url="pid:wikidata-autocomplete"),
                label=_("heslar.forms.OsobaAdminForm.wikidata.label"),
                instance=self.instance,
                initial_value=args[0].get("wikidata") if args else None,
                help_text=_("heslar.forms.OsobaAdminForm.wikidata.tooltip"),
            )
        except Exception as err:
            logger.warning("heslar.admin.OsobaAdminForm.__init__.wikidata_error", extra={"error": err})


class OrganizaceAdminForm(forms.ModelForm):
    """Implementuje komponentu ``OrganizaceAdminForm`` v rámci aplikace."""

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        model = Organizace
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        """Inicializuje instanci třídy.

        :param args: Dodatečné poziční argumenty předané voláním.
        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        :return: Funkce nevrací hodnotu (``None``)."""
        super().__init__(*args, **kwargs)
        self.fields["ror"] = RorAutocompleteField(
            widget=AutocompleteListSelect2(url="pid:ror-autocomplete"),
            label=_("heslar.forms.OrganizaceAdminForm.ror.label"),
            instance=self.instance,
            required=False,
        )
