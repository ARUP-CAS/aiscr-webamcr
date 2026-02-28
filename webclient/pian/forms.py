import logging

from core.message_constants import (
    PIAN_NEVALIDNI_GEOMETRIE,
    PIAN_VALIDACE_VYPNUTA,
    VALIDATION_NENALEZEN_KLAD,
    VALIDATION_NOT_SIMPLE,
)
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout
from django import forms
from django.contrib.gis.forms import HiddenInput
from django.contrib.gis.geos import LineString, Point, Polygon
from django.db import connections
from django.forms.utils import ErrorDict
from django.utils.translation import gettext_lazy as _
from heslar.hesla_dynamicka import GEOMETRY_BOD, GEOMETRY_LINIE, GEOMETRY_PLOCHA
from heslar.models import Heslar
from pian.models import Pian, get_ZM_from_point

logger = logging.getLogger(__name__)


class PianCreateForm(forms.ModelForm):
    """Hlavní formulář pro vytvoření, editaci a zobrazení pianu."""

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        model = Pian
        fields = ("presnost", "geom", "geom_sjtsk", "geom_system")
        labels = {"presnost": _("pian.forms.pianCreateForm.presnost.label")}
        help_texts = {
            "presnost": _("pian.forms.pianCreateForm.presnost.tooltip"),
        }
        widgets = {
            "geom": HiddenInput(),
            "geom_sjtsk": HiddenInput(),
            "geom_system": HiddenInput(),
            "presnost": forms.Select(
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
            ),
        }

    def __init__(self, *args, **kwargs):
        """
        Inicializuje instanci třídy.

        :param args: Dodatečné poziční argumenty předané voláním.
        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        """
        super(PianCreateForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Div(
                    "presnost",
                    css_class="col-sm-2",
                ),
                Div("geom", css_class="col-sm-2"),
                Div("geom_sjtsk", css_class="col-sm-2"),
                Div("geom_system", css_class="col-sm-2"),
                css_class="row",
            ),
        )

    def _instance_geom_wkt(self, field_name):
        """
        Provádí operaci instance geom wkt.

        :param field_name: Vstupní hodnota ``field_name`` pro danou operaci.
        :return: Vrací výsledek provedené operace.
        """
        g = getattr(self.instance, field_name, None)
        if not g:
            return None
        return g.wkt if hasattr(g, "wkt") else str(g)

    def run_loaded_validation(self):
        """Metoda pro validaci geometrií při potvrzení PIANu."""
        self._errors = ErrorDict()
        self.cleaned_data = {}
        geom_wkt = self._instance_geom_wkt("geom")
        geom_sjtsk_wkt = self._instance_geom_wkt("geom_sjtsk")
        if geom_wkt:
            try:
                self.validate_geom(geom_wkt, "4326")
            except forms.ValidationError as e:
                self.add_error("geom", e)
        if geom_sjtsk_wkt:
            try:
                self.validate_geom(geom_sjtsk_wkt, "5514")
            except forms.ValidationError as e:
                self.add_error("geom_sjtsk", e)
        return not bool(self.errors)

    def clean(self):
        """Provádí operaci clean."""
        validation_geom = self.data.get("geom")
        self.validate_geom(validation_geom, "4326")
        validation_geom_jtsk = self.data.get("geom_sjtsk")
        self.validate_geom(validation_geom_jtsk, "5514")
        geom = self.cleaned_data.get("geom")
        # Přiřaď referenční mapové listy.
        if isinstance(geom, Point):
            self.instance.typ = Heslar.objects.get(id=GEOMETRY_BOD)
            point = geom
        elif isinstance(geom, LineString):
            self.instance.typ = Heslar.objects.get(id=GEOMETRY_LINIE)
            point = geom.interpolate_normalized(0.5)
        elif isinstance(geom, Polygon):
            self.instance.typ = Heslar.objects.get(id=GEOMETRY_PLOCHA)
            point = geom.centroid
        else:
            raise forms.ValidationError(PIAN_NEVALIDNI_GEOMETRIE + " " + VALIDATION_NOT_SIMPLE)
        zm10, zm50 = get_ZM_from_point(point)
        if zm10 is not None and zm50 is not None:
            self.instance.zm10 = zm10
            self.instance.zm50 = zm50
        else:
            raise forms.ValidationError(PIAN_NEVALIDNI_GEOMETRIE + " " + VALIDATION_NENALEZEN_KLAD)

    def validate_geom(self, geom, epsg):
        """
        Metoda pro validaci PIAN pomocí funkce v postgres databázi.

        :param geom: Popis parametru ``geom``.
        :param epsg: Popis parametru ``epsg``.
        """
        c = connections["urgent"].cursor()
        logger.debug("pian.forms.validate_geom.start")
        try:
            c.execute("BEGIN")
            c.callproc("validateGeom", [geom, epsg])
            validation_results = c.fetchone()[0]
            logger.debug(
                "pian.forms.validate_geom.detail",
                extra={"validation_results": validation_results, "geom": geom},
            )
            c.execute("COMMIT")
        except Exception as e:
            logger.debug("pian.forms.validate_geom.detail", extra={"error": e})
            raise forms.ValidationError(PIAN_VALIDACE_VYPNUTA)
        finally:
            c.close()
        if validation_results != "valid":
            raise forms.ValidationError(
                _(validation_results),
            )
        logger.debug("pian.forms.validate_geom.form_valid")
