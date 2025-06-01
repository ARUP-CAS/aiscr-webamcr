import logging

from core.message_constants import PIAN_NEVALIDNI_GEOMETRIE, PIAN_VALIDACE_VYPNUTA, VALIDATION_EMPTY
from core.utils import get_validation_messages
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout
from django import forms
from django.contrib.gis.db.models.functions import Centroid
from django.contrib.gis.forms import HiddenInput
from django.contrib.gis.geos import LineString, Point, Polygon
from django.db import connection
from django.utils.translation import gettext_lazy as _
from heslar.hesla_dynamicka import GEOMETRY_BOD, GEOMETRY_LINIE, GEOMETRY_PLOCHA
from heslar.models import Heslar
from pian.models import Pian, get_ZM_from_point

logger = logging.getLogger(__name__)


class PianCreateForm(forms.ModelForm):
    """
    Hlavní formulář pro vytvoření, editaci a zobrazení pianu.
    """

    class Meta:
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

    def clean_geom(self):
        validation_geom = self.data.get("geom")
        c = connection.cursor()
        logger.debug("pian.forms.clean_geom.start")
        try:
            c.execute("BEGIN")
            c.callproc("validateGeom", [validation_geom])
            validation_results = c.fetchone()[0]
            logger.debug(
                "pian.forms.clean_geom.detail",
                extra={"validation_results": validation_results, "geom": validation_geom},
            )
            c.execute("COMMIT")
        except Exception as e:
            logger.debug("pian.forms.clean_geom.detail", extra={"error": e})
            raise forms.ValidationError(PIAN_VALIDACE_VYPNUTA)
        finally:
            c.close()
        if validation_results != "valid":
            raise forms.ValidationError(
                PIAN_NEVALIDNI_GEOMETRIE + " " + get_validation_messages(VALIDATION_EMPTY),
            )
        logger.debug("pian.forms.clean_geom.form_valid")
        geom = self.cleaned_data.get("geom")
        # Assign base map references
        if type(geom) == Point:
            self.instance.typ = Heslar.objects.get(id=GEOMETRY_BOD)
            point = geom
        elif type(geom) == LineString:
            self.instance.typ = Heslar.objects.get(id=GEOMETRY_LINIE)
            point = geom.interpolate_normalized(0.5)
        elif type(geom) == Polygon:
            self.instance.typ = Heslar.objects.get(id=GEOMETRY_PLOCHA)
            point = Centroid(geom)
        else:
            raise forms.ValidationError(
                PIAN_NEVALIDNI_GEOMETRIE + " " + get_validation_messages(VALIDATION_EMPTY),
            )
        logger.debug("pian.forms.clean_geom.geom", extra={"geom": str(geom)})
        zm10, zm50 = get_ZM_from_point(point)
        if zm10 is not None and zm50 is not None:
            self.instance.zm10 = zm10
            self.instance.zm50 = zm50
        else:
            raise forms.ValidationError(
                PIAN_NEVALIDNI_GEOMETRIE + " " + get_validation_messages(VALIDATION_EMPTY),
            )
        return geom
