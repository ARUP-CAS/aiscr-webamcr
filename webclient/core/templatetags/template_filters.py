import datetime
import logging


from django import template
from psycopg2._range import DateRange
from heslar.models import RuianKatastr
from django.utils.translation import gettext_lazy as _

from uzivatel.models import Osoba
from dokument.models import DokumentAutor
from ez.models import ExterniZdrojAutor, ExterniZdrojEditor
from heslar import hesla

register = template.Library()

logger = logging.getLogger(__name__)
import logging
import logstash

logger_s = logging.getLogger('python-logstash-logger')


@register.filter
def url_to_classes(value):
    if value == "/":
        return "app-home"
    if value.endswith("/"):
        value = value[:-1]
    classes = value.replace("/", " app-")
    return classes


@register.filter
def katastry_to_list(value):
    value = [str(i) for i in value]
    display = ", ".join(value)
    # for katastr in value:
    #     display += (katastr.__str__()) + ", "
    return display


@register.filter
def hesla_to_list(value):
    list_hesla = ", ".join(value.values_list("heslo", flat=True))
    return list_hesla


@register.filter
def osoby_to_list(value):
    list_hesla = "; ".join(value.values_list("vypis_cely", flat=True))
    return list_hesla


@register.filter
def render_daterange(value):
    if value == "" or value is None:
        return None
    if isinstance(value, DateRange):
        if value.lower and value.upper:
            return (
                value.lower.strftime("%d.%m.%Y")
                + " - "
                + (value.upper - datetime.timedelta(days=1)).strftime("%d.%m.%Y")
            )
    return str(value)


@register.filter
def last_x_letters(value, x):
    if len(value) > x:
        return value[-x:]
    else:
        return value


@register.filter(name="ifinlist")
def ifinlist(widget_optgroups, list):
    string = ""
    for group_name, group_choices, group_index in widget_optgroups:
        for option in group_choices:
            if str(option["value"]) in list and str(option["value"]) != "":
                if string == "":
                    string = str(option["label"])
                else:
                    string += "; " + str(option["label"])
    return string


@register.filter
def check_if_none(value):
    if value:
        return value
    else:
        return ""


@register.filter
def get_katastr_name(value):
    if isinstance(value, list):
        katastre = RuianKatastr.objects.filter(pk__in=value)
        katastr_str = []
        for katastr in katastre:
            katastr_str.append(katastr.nazev + " (" + katastr.okres.nazev + ")")
        list_hesla = "; ".join(katastr_str)
        return list_hesla
    else:
        katastr = RuianKatastr.objects.get(pk=value)
    return katastr.nazev + " (" + katastr.okres.nazev + ")"


@register.filter
def true_false(value):
    if value and value == True:
        return _("Ano")
    else:
        return _("Ne")


@register.filter
def get_osoby_name(widget):
    list_hesla = ""
    if not widget["value"] or widget["value"] == [""]:
        return list_hesla
    if "name_id" in widget["attrs"]:
        if "ez" in widget["attrs"]["name_id"]:
            if "autori" in widget["name"]:
                objekt = ExterniZdrojAutor
            else:
                objekt = ExterniZdrojEditor
            arg_list = [arg.strip() for arg in widget["attrs"]["name_id"].split(";")]
            i = 1
            dok_autory = objekt.objects.filter(
                externi_zdroj__ident_cely=arg_list[1]
            ).order_by("poradi")
            for item in dok_autory:
                if i == 1:
                    list_hesla = item.get_osoba()
                else:
                    list_hesla = list_hesla + "; " + item.get_osoba()
                i = i + 1
        elif "autori" in widget["name"]:
            arg_list = [arg.strip() for arg in widget["attrs"]["name_id"].split(";")]
            i = 1
            dok_autory = DokumentAutor.objects.filter(
                dokument__ident_cely=arg_list[1]
            ).order_by("poradi")
            list_hesla = ""
            for item in dok_autory:
                if i == 1:
                    list_hesla = item.autor.vypis_cely
                else:
                    list_hesla = list_hesla + "; " + item.autor.vypis_cely
                i = i + 1
    else:
        osoby = Osoba.objects.filter(pk__in=widget["value"])
        list_hesla = "; ".join(osoby.values_list("vypis_cely",flat=True))
    return list_hesla


@register.simple_tag
def get_value_from_heslar(nazev_heslare, hodnota):
    values = {
        ("externi_zdroj_typ", "kniha"): hesla.EXTERNI_ZDROJ_TYP_KNIHA,
        ("externi_zdroj_typ", "cast_knihy"): hesla.EXTERNI_ZDROJ_TYP_CAST_KNIHY,
        ("externi_zdroj_typ", "clanek_v_casopise"): hesla.EXTERNI_ZDROJ_TYP_CLANEK_V_CASOPISE,
        ("externi_zdroj_typ", "clanek_v_novinach"): hesla.EXTERNI_ZDROJ_TYP_CLANEK_V_NOVINACH,
        ("externi_zdroj_typ", "nepublikovana_zprava"): hesla.EXTERNI_ZDROJ_TYP_NEPUBLIKOVANA_ZPRAVA,
    }
    if (nazev_heslare, hodnota) in values:
        return values[(nazev_heslare, hodnota)]
    else:
        logger_s.error("template_filters.get_value_from_heslar.error", nazev_heslare=nazev_heslare, hodnota=hodnota)
        return ""
