from datetime import date
from decimal import Decimal

from adb.models import VyskovyBod
from arch_z.models import ArcheologickyZaznam, ExterniOdkaz
from core.constants import ROLE_ADMIN_ID, ROLE_ARCHIVAR_ID
from core.models import Soubor
from dj.models import DokumentacniJednotka
from django.db import connection, transaction
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from dokument.models import Dokument, DokumentCast, Tvar
from ez.models import ExterniZdroj
from historie.models import Historie
from komponenta.models import Komponenta
from nalez.models import NalezObjekt, NalezPredmet
from neidentakce.models import NeidentAkce
from pas.models import SamostatnyNalez
from projekt.models import Projekt
from projekt.views import get_show_oznamovatel


def get_model(name):
    """
    Vrací model. v aplikaci.

    :param name: Vstupní hodnota ``name`` pro danou operaci.
    """
    models = {
        "tvary": Tvar,
        "dokument": Dokument,
        "dokument_casti": DokumentCast,
        "komponenty": Komponenta,
        "objekty": NalezObjekt,
        "predmety": NalezPredmet,
        "historie": Historie,
        "soubory": Soubor,
        "projekt": Projekt,
        "archeologicky_zaznam": ArcheologickyZaznam,
        "samostatny_nalez": SamostatnyNalez,
        "akce": ArcheologickyZaznam,
        "dokumentacni_jednotka": DokumentacniJednotka,
        "vb": VyskovyBod,
        "ext_odkaz": ExterniOdkaz,
        "lokalita": ArcheologickyZaznam,
        "pas": SamostatnyNalez,
        "model": Dokument,
        "ez": ExterniZdroj,
    }
    return models.get(name)


def get_gml(geom):
    """
    Vrací gml. v aplikaci.

    :param geom: Vstupní hodnota ``geom`` pro danou operaci.
    """
    try:
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute("SELECT ST_AsGML(%s)", [geom.wkt])
            row = cursor.fetchone()
        return row[0]
    except Exception:
        return None


def get_wkt(geom):
    """
    Vrací wkt. v aplikaci.

    :param geom: Vstupní hodnota ``geom`` pro danou operaci.
    """
    with connection.cursor() as cursor:
        cursor.execute("SELECT ST_AsText(ST_GeomFromText(%s))", [geom.wkt])
        row = cursor.fetchone()
        cursor.close()
        return row[0]


class SimpleSectionTemplateName:
    """Implementuje komponentu ``SimpleSectionTemplateName`` v rámci aplikace."""

    def __init__(self, name):
        """
        Inicializuje instanci třídy.

        :param name: Vstupní hodnota ``name`` pro danou operaci.
        """
        self.name = name

    def __str__(self):
        """
        Vrací textovou reprezentaci objektu.

        :return: Vrací výsledek provedené operace.
        """
        return self.name

    def get_name(self, instance):
        """
        Vrací name. v aplikaci.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        """
        return self.name

    def get_permission(self, instance, user=None):
        """
        Vrací permission. v aplikaci.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        :param user: Vstupní hodnota ``user`` pro danou operaci.
        """
        return True


class SectionNameWithAccessor(SimpleSectionTemplateName):
    """Implementuje komponentu ``SectionNameWithAccessor`` v rámci aplikace."""

    def __init__(self, name, accessor, foreign_key=None):
        """
        Inicializuje instanci třídy.

        :param name: Vstupní hodnota ``name`` pro danou operaci.
        :param accessor: Vstupní hodnota ``accessor`` pro danou operaci.
        :param foreign_key: Vstupní hodnota ``foreign_key`` pro danou operaci.
        """
        super().__init__(name)
        self.accessor = accessor
        self.foreign_key = foreign_key

    def get_name(self, instance):
        """
        Vrací name. v aplikaci.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        """
        if self.foreign_key:
            if getattr(instance, self.foreign_key):
                return f"{self.name}&nbsp;{getattr(getattr(instance, self.foreign_key), self.accessor)}"
            else:
                return None
        return f"{self.name}&nbsp;{getattr(instance, self.accessor)}"


class PianSectionNameWithAccessor(SectionNameWithAccessor):
    """Implementuje komponentu ``PianSectionNameWithAccessor`` v rámci aplikace."""

    def get_name(self, instance):
        """
        Vrací name. v aplikaci.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        """
        if getattr(instance, self.foreign_key):
            pian = getattr(instance, self.foreign_key)
            stav = getattr(pian, self.accessor[1])()
            return f"{self.name}&nbsp;{getattr(pian, self.accessor[0])}&nbsp;({stav})&nbsp;-&nbsp;{getattr(pian, self.accessor[2])}&nbsp;({getattr(pian, self.accessor[3])})"
        else:
            return None


class OznamovatelSectionNameWithAccessor(SectionNameWithAccessor):
    """Implementuje komponentu ``OznamovatelSectionNameWithAccessor`` v rámci aplikace."""

    def get_permission(self, instance, user=None):
        """
        Vrací permission. v aplikaci.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        :param user: Vstupní hodnota ``user`` pro danou operaci.
        """
        return get_show_oznamovatel(instance, user)


class Field:
    """Implementuje komponentu ``Field`` v rámci aplikace."""

    def __init__(self, label, accessor):
        """
        Inicializuje instanci třídy.

        :param label: Vstupní hodnota ``label`` pro danou operaci.
        :param accessor: Vstupní hodnota ``accessor`` pro danou operaci.
        """
        self.label = label
        self.accessor = accessor

    def __repr__(self):
        """
        Vrací reprezentaci objektu pro ladění.

        :return: Vrací výsledek provedené operace.
        """
        return f"Field(label={self.label}, accessor={self.accessor})"

    def __str__(self):
        """
        Vrací textovou reprezentaci objektu.

        :return: Vrací výsledek provedené operace.
        """
        return self.label

    def get_value(self, instance, user=None):
        """
        Vrací value. v aplikaci.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        :param user: Vstupní hodnota ``user`` pro danou operaci.
        """
        value = getattr(instance, self.accessor)
        if isinstance(value, date) and value:
            return value.strftime("%-d.%-m.%Y")
        if isinstance(value, Decimal) and value:
            return f"{value:.3f}"
        return getattr(instance, self.accessor)

    def get_label(self):
        """Vrací label. v aplikaci."""
        return self.label


class SouborField(Field):
    """Implementuje komponentu ``SouborField`` v rámci aplikace."""

    def __init__(self, label, accessor, key_name):
        """
        Inicializuje instanci třídy.

        :param label: Vstupní hodnota ``label`` pro danou operaci.
        :param accessor: Vstupní hodnota ``accessor`` pro danou operaci.
        :param key_name: Vstupní hodnota ``key_name`` pro danou operaci.
        """
        super().__init__(label, accessor)
        self.key_name = key_name

    def get_value(self, instance, user=None):
        """
        Vrací value. v aplikaci.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        :param user: Vstupní hodnota ``user`` pro danou operaci.
        """
        soubor = getattr(instance, self.accessor)
        if soubor:
            return reverse(
                "core:download_thumbnail",
                args=(
                    self.key_name,
                    instance.vazba.navazany_objekt.ident_cely,
                    instance.id,
                ),
            )
        return None


class SouborDownloadField(SouborField):
    """Implementuje komponentu ``SouborDownloadField`` v rámci aplikace."""

    def get_value(self, instance, user=None):
        """
        Vrací value. v aplikaci.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        :param user: Vstupní hodnota ``user`` pro danou operaci.
        """
        accessor = getattr(instance, self.accessor)
        if accessor:
            return {
                "value": accessor,
                "download": reverse(
                    "core:download_file",
                    args=(
                        self.key_name,
                        instance.vazba.navazany_objekt.ident_cely,
                        instance.id,
                    ),
                ),
            }
        return None


class Model3dKomponentaField(Field):
    """Implementuje komponentu ``Model3dKomponentaField`` v rámci aplikace."""

    def get_value(self, instance, user=None):
        """
        Vrací value. v aplikaci.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        :param user: Vstupní hodnota ``user`` pro danou operaci.
        """
        return getattr(instance.casti.first().komponenty.komponenty.first(), self.accessor)


class Model3dKomponentaAktivityField(Model3dKomponentaField):
    """Implementuje komponentu ``Model3dKomponentaAktivityField`` v rámci aplikace."""

    def get_value(self, instance, user=None):
        """
        Vrací value. v aplikaci.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        :param user: Vstupní hodnota ``user`` pro danou operaci.
        """
        related_manager = super().get_value(instance, user)
        return "; ".join([str(v) for v in related_manager.all()])


class ChooseField(Field):
    """Implementuje komponentu ``ChooseField`` v rámci aplikace."""

    def get_value(self, instance, user=None):
        """
        Vrací value. v aplikaci.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        :param user: Vstupní hodnota ``user`` pro danou operaci.
        """
        for accessor in self.accessor:
            value = getattr(instance, accessor)
            if value:
                return mark_safe(value.get_ident_cely_link)
        return None


class StatusField(Field):
    """Implementuje komponentu ``StatusField`` v rámci aplikace."""

    def get_value(self, instance, user=None):
        """
        Vrací value. v aplikaci.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        :param user: Vstupní hodnota ``user`` pro danou operaci.
        """
        return getattr(instance, self.accessor)()


class ZjisteniField(Field):
    """Implementuje komponentu ``ZjisteniField`` v rámci aplikace."""

    def get_value(self, instance, user=None):
        """
        Vrací value. v aplikaci.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        :param user: Vstupní hodnota ``user`` pro danou operaci.
        """
        if getattr(instance, self.accessor) is not None:
            if getattr(instance, self.accessor):
                return _("vypis.vypis_config.dj.zjisteni.Ano")
            else:
                return _("vypis.vypis_config.dj.zjisteni.Ne")
        return getattr(instance, self.accessor)()


class ForeignField(Field):
    """Implementuje komponentu ``ForeignField`` v rámci aplikace."""

    def __init__(self, name, accessor, foreign_key):
        """
        Inicializuje instanci třídy.

        :param name: Vstupní hodnota ``name`` pro danou operaci.
        :param accessor: Vstupní hodnota ``accessor`` pro danou operaci.
        :param foreign_key: Vstupní hodnota ``foreign_key`` pro danou operaci.
        """
        super().__init__(name, accessor)
        self.foreign_key = foreign_key

    def get_value(self, instance, user=None):
        """
        Vrací value. v aplikaci.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        :param user: Vstupní hodnota ``user`` pro danou operaci.
        """
        accessors = self.accessor.split("__")
        new_instance = ""
        try:
            if getattr(instance, self.foreign_key):
                new_instance = getattr(instance, self.foreign_key)
                for key in accessors:
                    if getattr(new_instance, key, False) or getattr(new_instance, key) == 0:
                        new_instance = getattr(new_instance, key)
                    else:
                        new_instance = ""
                        break
        except Dokument.extra_data.RelatedObjectDoesNotExist:
            new_instance = ""
        return mark_safe(new_instance)


class GeomGmlField(Field):
    """Implementuje komponentu ``GeomGmlField`` v rámci aplikace."""

    def get_value(self, instance, user=None):
        """
        Vrací value. v aplikaci.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        :param user: Vstupní hodnota ``user`` pro danou operaci.
        """
        geom = getattr(instance, self.accessor)
        if geom:
            return get_gml(geom)
        return None


class GeomWktField(Field):
    """Implementuje komponentu ``GeomWktField`` v rámci aplikace."""

    def get_value(self, instance, user=None):
        """
        Vrací value. v aplikaci.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        :param user: Vstupní hodnota ``user`` pro danou operaci.
        """
        geom = getattr(instance, self.accessor)
        if geom:
            return get_wkt(geom)
        return None


class ForeignGeomGmlField(ForeignField):
    """Implementuje komponentu ``ForeignGeomGmlField`` v rámci aplikace."""

    def get_value(self, instance, user=None):
        """
        Vrací value. v aplikaci.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        :param user: Vstupní hodnota ``user`` pro danou operaci.
        """
        try:
            geom = getattr(getattr(instance, self.foreign_key), self.accessor)
            if geom:
                return get_gml(geom)
        except Dokument.extra_data.RelatedObjectDoesNotExist:
            return None
        return None


class ForeignGeomWktField(ForeignField):
    """Implementuje komponentu ``ForeignGeomWktField`` v rámci aplikace."""

    def get_value(self, instance, user=None):
        """
        Vrací value. v aplikaci.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        :param user: Vstupní hodnota ``user`` pro danou operaci.
        """
        try:
            geom = getattr(getattr(instance, self.foreign_key), self.accessor)
            if geom:
                return get_wkt(geom)
        except Dokument.extra_data.RelatedObjectDoesNotExist:
            return None
        return None


class ManyToManyField(Field):
    """Implementuje komponentu ``ManyToManyField`` v rámci aplikace."""

    def get_value(self, instance, user=None):
        """
        Vrací value. v aplikaci.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        :param user: Vstupní hodnota ``user`` pro danou operaci.
        """
        related_manager = getattr(instance, self.accessor)
        return "; ".join([str(v) for v in related_manager.all()])


class ForeignManyToManyField(ForeignField):
    """Implementuje komponentu ``ForeignManyToManyField`` v rámci aplikace."""

    def get_value(self, instance, user=None):
        """
        Vrací value. v aplikaci.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        :param user: Vstupní hodnota ``user`` pro danou operaci.
        """
        if getattr(instance, self.foreign_key, False):
            related_manager = getattr(getattr(instance, self.foreign_key), self.accessor)
            return "; ".join([v.vypis_name() for v in related_manager.all()])
        return None


class DoubleField(Field):
    """Implementuje komponentu ``DoubleField`` v rámci aplikace."""

    def get_value(self, instance, user=None):
        """
        Vrací value. v aplikaci.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        :param user: Vstupní hodnota ``user`` pro danou operaci.
        """
        values = []
        for accessor in self.accessor:
            value = getattr(instance, accessor)
            if value:
                if isinstance(value, date):
                    values.append(value.strftime("%-d.%-m.%Y"))
                else:
                    values.append(str(value))
        if values:
            return " - ".join(values)
        return None


class DoubleFieldNum(Field):
    """Implementuje komponentu ``DoubleFieldNum`` v rámci aplikace."""

    def get_value(self, instance, user=None):
        """
        Vrací value. v aplikaci.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        :param user: Vstupní hodnota ``user`` pro danou operaci.
        """
        values = []
        for accessor in self.accessor:
            value = getattr(instance, accessor)
            if value:
                values.append(str(value))
        if values:
            return " - ".join(values)
        return None


class ForeignDoubleField(ForeignField):
    """Implementuje komponentu ``ForeignDoubleField`` v rámci aplikace."""

    def get_value(self, instance, user=None):
        """
        Vrací value. v aplikaci.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        :param user: Vstupní hodnota ``user`` pro danou operaci.
        """
        if getattr(instance, self.foreign_key, False):
            values = []
            for accessor in self.accessor:
                value = getattr(getattr(instance, self.foreign_key), accessor)
                if value:
                    values.append(str(value))
            if values:
                return " - ".join(values)
        return None


class ForeignDoubleFieldNum(ForeignField):
    """Implementuje komponentu ``ForeignDoubleFieldNum`` v rámci aplikace."""

    def get_value(self, instance, user=None):
        """
        Vrací value. v aplikaci.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        :param user: Vstupní hodnota ``user`` pro danou operaci.
        """
        if getattr(instance, self.foreign_key, False):
            values = []
            for accessor in self.accessor:
                value = getattr(getattr(instance, self.foreign_key), accessor)
                if value:
                    values.append(str(value))
            if values:
                return "-".join(values)
        return None


class RepeatableField(ForeignField):
    """Implementuje komponentu ``RepeatableField`` v rámci aplikace."""

    def __init__(self, name, accessor, foreign_key, template_name=None, model_name=None):
        """
        Inicializuje instanci třídy.

        :param name: Vstupní hodnota ``name`` pro danou operaci.
        :param accessor: Vstupní hodnota ``accessor`` pro danou operaci.
        :param foreign_key: Vstupní hodnota ``foreign_key`` pro danou operaci.
        :param template_name: Vstupní hodnota ``template_name`` pro danou operaci.
        :param model_name: Vstupní hodnota ``model_name`` pro danou operaci.
        """
        super().__init__(name, accessor, foreign_key)
        self.template_name = template_name
        self.model_name = model_name

    def get_related_manager(self, instance):
        """
        Vrací related manager.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        """
        if self.model_name:
            return get_model(self.foreign_key).objects.filter(**{self.model_name: instance})
        return get_model(self.foreign_key).objects.filter(**{instance._meta.model_name: instance})

    def get_value(self, instance, user=None):
        """
        Vrací value. v aplikaci.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        :param user: Vstupní hodnota ``user`` pro danou operaci.
        """
        related_manager = self.get_related_manager(instance)
        data = {
            "template_name": self.template_name,
        }
        if related_manager.count() > 0:
            data["zaznamy"] = []
            for v in related_manager.all():
                item = {}
                for accessor in self.accessor:
                    accessors = accessor.split("__")
                    new_v = v
                    for a in accessors:
                        new_v = getattr(new_v, a)
                    item[accessors[-1]] = new_v
                data["zaznamy"].append(item)
            return data
        return None


class VbRepeatableField(RepeatableField):
    """Implementuje komponentu ``VbRepeatableField`` v rámci aplikace."""

    def get_value(self, instance, user=None):
        """
        Vrací value. v aplikaci.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        :param user: Vstupní hodnota ``user`` pro danou operaci.
        """
        related_manager = self.get_related_manager(instance)
        data = {
            "template_name": self.template_name,
            "label": self.label,
        }
        if related_manager.count() > 0:
            data["zaznamy"] = []
            for v in related_manager.all():
                acc3_2 = get_wkt(getattr(v, "geom"))
                acc3_3 = get_gml(getattr(v, "geom"))
                item = {}
                item[self.accessor[0]] = getattr(v, self.accessor[0])
                item[self.accessor[1]] = getattr(v, self.accessor[1])
                item[self.accessor[2]] = f"GML (EPSG:5514): {acc3_3}"
                item[self.accessor[3]] = f"WKT (EPSG:5514): {acc3_2}"
                data["zaznamy"].append(item)
            return data
        return None


class HistorieRepeatableField(RepeatableField):
    """Implementuje komponentu ``HistorieRepeatableField`` v rámci aplikace."""

    def get_related_manager(self, instance):
        """
        Vrací related manager.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        """
        return Historie.objects.filter(**{"vazba": instance.historie})

    def get_value(self, instance, user=None):
        """
        Vrací value. v aplikaci.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        :param user: Vstupní hodnota ``user`` pro danou operaci.
        """
        related_manager = self.get_related_manager(instance)
        data = {
            "template_name": self.template_name,
        }
        if related_manager.count() > 0:
            data[self.foreign_key] = []
            for v in related_manager.all():
                item = {}
                for accessor in self.accessor:
                    if accessor == "uzivatel_protected":
                        item[accessor] = v.uzivatel_protected(
                            user.hlavni_role.pk not in (ROLE_ADMIN_ID, ROLE_ARCHIVAR_ID)
                        )
                    elif accessor.endswith("display"):
                        item[accessor] = getattr(v, accessor)()
                    else:
                        item[accessor] = getattr(v, accessor)
                data[self.foreign_key].append(item)
            return data
        return None


class RepeatableSectionField(RepeatableField):
    """Implementuje komponentu ``RepeatableSectionField`` v rámci aplikace."""

    def get_label(self):
        """Vrací label. v aplikaci."""
        return super().get_label()

    def get_sections(self, instance):
        """
        Vrací sections. v aplikaci.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        """
        related_manager = (
            get_model(self.foreign_key).objects.filter(**{instance._meta.model_name: instance}).order_by("ident_cely")
        )
        if related_manager.count() > 0:
            return related_manager
        return None

    def get_value(self, instance, user=None):
        """
        Vrací value. v aplikaci.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        :param user: Vstupní hodnota ``user`` pro danou operaci.
        """
        related_manager = get_model(self.foreign_key).objects.filter(**{instance._meta.model_name: instance})
        data = {
            "template_name": self.template_name,
        }
        if related_manager.count() > 0:
            data[self.foreign_key] = []
            for v in related_manager.all():
                item = {}
                for accessor in self.accessor:
                    item[accessor] = getattr(v, accessor)
                data[self.foreign_key].append(item)
            return data
        return None


class SectionField(Field):
    """Implementuje komponentu ``SectionField`` v rámci aplikace."""

    def __init__(self, name, accessor, foreign_key):
        """
        Inicializuje instanci třídy.

        :param name: Vstupní hodnota ``name`` pro danou operaci.
        :param accessor: Vstupní hodnota ``accessor`` pro danou operaci.
        :param foreign_key: Vstupní hodnota ``foreign_key`` pro danou operaci.
        """
        super().__init__(name, accessor)
        self.foreign_key = foreign_key


class RepeatableSectionNameWithAccessor(SectionNameWithAccessor):
    """Implementuje komponentu ``RepeatableSectionNameWithAccessor`` v rámci aplikace."""

    def __init__(self, name, accessor, foreign_key, model_name=None):
        """
        Inicializuje instanci třídy.

        :param name: Vstupní hodnota ``name`` pro danou operaci.
        :param accessor: Vstupní hodnota ``accessor`` pro danou operaci.
        :param foreign_key: Vstupní hodnota ``foreign_key`` pro danou operaci.
        :param model_name: Vstupní hodnota ``model_name`` pro danou operaci.
        """
        super().__init__(name, accessor, foreign_key)
        self.model_name = model_name

    def get_sections(self, instance):
        """
        Vrací sections. v aplikaci.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        """
        related_manager = (
            get_model(self.foreign_key).objects.filter(**{self.model_name: instance}).order_by("ident_cely")
        )
        if related_manager.count() > 0:
            return related_manager
        return None

    def get_name(self, instance):
        """
        Vrací name. v aplikaci.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        """
        if len(self.accessor) > 2:
            new_name = f"{self.name}&nbsp;{getattr(instance, self.accessor[0])}&nbsp;-&nbsp;{getattr(instance, self.accessor[1])}"
        else:
            new_name = f"{self.name}&nbsp;{getattr(instance, self.accessor[0])}"
        if getattr(instance, self.accessor[-1]):
            return f"{new_name} ({getattr(instance, self.accessor[-1])})"
        return new_name


class SouboryRepeatableSectionNameWithAccessor(RepeatableSectionNameWithAccessor):
    """Implementuje komponentu ``SouboryRepeatableSectionNameWithAccessor`` v rámci aplikace."""

    def get_sections(self, instance):
        """
        Vrací sections. v aplikaci.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        """
        related_manager = get_model(self.foreign_key).objects.filter(**{"vazba": instance.soubory}).order_by("pk")
        if related_manager.count() > 0:
            return related_manager
        return None

    def get_name(self, instance):
        """
        Vrací name. v aplikaci.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        """
        new_name = f"{self.name} {getattr(instance, self.accessor[0])}"
        if getattr(instance, self.accessor[-1]):
            return f"{new_name}<div class='mime-type' style='white-space: pre;'> ({getattr(instance, self.accessor[-1])})</div>"
        return new_name


class KomponentaRepeatableSectionNameWithAccessor(RepeatableSectionNameWithAccessor):
    """Implementuje komponentu ``KomponentaRepeatableSectionNameWithAccessor`` v rámci aplikace."""

    def get_name(self, instance):
        """
        Vrací name. v aplikaci.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        """
        obdobi = getattr(instance, self.accessor[1])
        jistota = getattr(instance, self.accessor[2])
        presna_datace = getattr(instance, self.accessor[3])
        areal = getattr(instance, self.accessor[4])
        aktivity = getattr(instance, self.accessor[5]).all()
        second_part = ""
        third_part = ""
        vypis_jistota_translated_ne = _("vypis.vypis_config.komponenta.jistota.Ne")
        vypis_jistota_translated_ano = _("vypis.vypis_config.komponenta.jistota.Ano")
        if jistota is not None:
            if jistota:
                second_part += f"&nbsp;({vypis_jistota_translated_ano}"
            else:
                second_part += f"&nbsp;({vypis_jistota_translated_ne}"
            if presna_datace:
                second_part += f";&nbsp;{presna_datace})"
            else:
                second_part += ")"
        elif presna_datace:
            second_part += f"&nbsp;({presna_datace})"
        if aktivity:
            third_part = f"&nbsp;({';&nbsp;'.join([str(a) for a in aktivity])})"
        return f"{self.name}&nbsp;{getattr(instance, self.accessor[0])}&nbsp;-&nbsp;{obdobi}{second_part}&nbsp;-&nbsp;{areal}{third_part}"


class SubSectionField:
    """Implementuje komponentu ``SubSectionField`` v rámci aplikace."""

    def __init__(self, config, foreign_key=None):
        """
        Inicializuje instanci třídy.

        :param config: Vstupní hodnota ``config`` pro danou operaci.
        :param foreign_key: Vstupní hodnota ``foreign_key`` pro danou operaci.
        """
        self.config = config
        self.foreign_key = foreign_key

    def get_config(self):
        """Vrací config. v aplikaci."""
        return self.config

    def get_instance(self, instance):
        """
        Vrací instance. v aplikaci.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        """
        if self.foreign_key:
            try:
                return getattr(instance, self.foreign_key)
            except Exception:
                return None
        return instance


class NeidentAkceSubSectionField(SubSectionField):
    """Implementuje komponentu ``NeidentAkceSubSectionField`` v rámci aplikace."""

    def get_instance(self, instance):
        """
        Vrací instance. v aplikaci.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        """
        try:
            neident_akce = NeidentAkce.objects.get(dokument_cast=instance)
            return neident_akce
        except Exception:
            return None


def get_historie_config(label_key):
    """
    Vrací historie config.

    :param label_key: Vstupní hodnota ``label_key`` pro danou operaci.
    """
    return {
        "section_name": SimpleSectionTemplateName(label_key),
        "template": SimpleSectionTemplateName("vypis/simple_section_with_name.html"),
        "historie": HistorieRepeatableField(
            label_key,
            ["datum_zmeny", "uzivatel_protected", "get_typ_zmeny_display", "poznamka"],
            "historie",
            "vypis/historie.html",
        ),
    }


class HistorieSubSectionField(SubSectionField):
    """Implementuje komponentu ``HistorieSubSectionField`` v rámci aplikace."""

    def __init__(self, foreign_key=None, label_key="vypis.historie.section_name"):
        """
        Inicializuje instanci třídy.

        :param foreign_key: Vstupní hodnota ``foreign_key`` pro danou operaci.
        :param label_key: Vstupní hodnota ``label_key`` pro danou operaci.
        """
        self.label_key = label_key
        self.foreign_key = foreign_key

    def get_config(self):
        """Vrací config. v aplikaci."""
        return get_historie_config(self.label_key)
