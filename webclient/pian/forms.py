import logging

from core.forms import OptimisticLockingMixin
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


#: Pole DJ, která mohou být přepsána při ``dj.save()`` v operacích nad PIANem
#: (vytvoření, odpojení). Snapshot těchto polí se ukládá do skrytého pole formuláře
#: a kontroluje před uložením, aby se zabránilo tichému přepsání souběžné editace DJ.
DJ_LOCK_FIELDS = ["typ", "nazev", "negativni_jednotka", "pian"]

#: Název skrytého pole pro secondary lock proti instanci DJ.
DJ_LOCK_FIELD_NAME = "optimistic_lock_data_dj"


class PianCreateForm(OptimisticLockingMixin, forms.ModelForm):
    """Hlavní formulář pro vytvoření, editaci a zobrazení pianu."""

    optimistic_lock_exclude = ["geom_sjtsk", "geom_system"]

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        model = Pian
        fields = ("presnost", "geom", "geom_sjtsk", "geom_system")
        labels = {
            "presnost": _("pian.forms.pianCreateForm.presnost.label"),
            "geom": _("pian.forms.pianCreateForm.geom.label"),
        }
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

    def __init__(self, *args, dj=None, **kwargs):
        """
        Inicializuje instanci třídy.

        :param args: Parametr ``args`` se předává do volání ``__init__()``.
        :param dj: Volitelná instance dokumentační jednotky pro secondary lock — sleduje
            souběžné změny polí DJ, které by mohly být přepsány při ``dj.save()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.
        """
        super(PianCreateForm, self).__init__(*args, **kwargs)
        self.add_secondary_lock(dj, DJ_LOCK_FIELD_NAME, DJ_LOCK_FIELDS)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Div(
                    "presnost",
                    css_class="col-sm-6 col-lg-2",
                ),
                Div("geom", css_class="col-sm-6 col-lg-2"),
                Div("geom_sjtsk", css_class="col-sm-6 col-lg-2"),
                Div("geom_system", css_class="col-sm-6 col-lg-2"),
                css_class="row",
            ),
        )
        hidden_fields = []
        if self.optimistic_lock_field_name in self.fields:
            hidden_fields.append(self.optimistic_lock_field_name)
        if DJ_LOCK_FIELD_NAME in self.fields:
            hidden_fields.append(DJ_LOCK_FIELD_NAME)
        if hidden_fields:
            self.helper.layout[0].append(Div(*hidden_fields, css_class="d-none"))

    def get_dj_conflicting_fields(self):
        """
        Vrátí seznam polí DJ, která byla v DB změněna od renderu formuláře.

        :return: Seznam názvů polí (``typ``, ``nazev``, ``negativni_jednotka``, ``pian``).
        """
        return self.get_secondary_conflicting_fields(DJ_LOCK_FIELD_NAME)

    def _instance_geom_wkt(self, field_name):
        """
               Provádí operaci instance geom wkt.

               :param field_name: Textový název nebo klíč ``field_name`` používaný v rámci operace.
        :return: Výstup funkce odpovídající implementované logice.
        """
        g = getattr(self.instance, field_name, None)
        if not g:
            return None
        return g.wkt if hasattr(g, "wkt") else str(g)

    def run_loaded_validation(self):
        """
        Metoda pro validaci geometrií při potvrzení PIANu.

        :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
        """
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
        """
        Provádí operaci clean.

        :raises forms.ValidationError: Vyvolá se při splnění podmínky ``isinstance(geom, Polygon)``; nebo při splnění podmínky ``zm10 is not None and zm50 is not None``.
        """
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

        :param geom: Parametr ``geom`` předává se do volání ``callproc()``, ``debug()``.
        :param epsg: Parametr ``epsg`` se předává do volání ``callproc()``.

            :raises forms.ValidationError: Vyvolá se při zpracování zachycené výjimky typu ``Exception``; nebo při splnění podmínky ``validation_results != 'valid'``.
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


class PianOdpojitForm(OptimisticLockingMixin, forms.Form):
    """
    Minimální formulář pro modál odpojení PIANu od DJ.

    Nese pouze secondary lock proti instanci DJ, aby šlo detekovat souběžnou editaci
    polí DJ (např. ``typ``) předtím, než je v ``pian/views.py:odpojit`` zavolán
    ``dj.save()``.
    """

    def __init__(self, *args, dj=None, **kwargs):
        """
        Inicializuje formulář se snapshotem polí DJ.

        :param args: Parametr ``args`` se předává do volání ``__init__()``.
        :param dj: Volitelná instance dokumentační jednotky pro secondary lock.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.
        """
        super().__init__(*args, **kwargs)
        self.add_secondary_lock(dj, DJ_LOCK_FIELD_NAME, DJ_LOCK_FIELDS)
        self.helper = FormHelper(self)
        self.helper.form_tag = False

    def get_dj_conflicting_fields(self):
        """
        Vrátí seznam polí DJ, která byla v DB změněna od renderu formuláře.

        :return: Seznam názvů polí (``typ``, ``nazev``, ``negativni_jednotka``, ``pian``).
        """
        return self.get_secondary_conflicting_fields(DJ_LOCK_FIELD_NAME)
