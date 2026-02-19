import datetime
import logging
import os

from core import constants
from django import template
from django.utils.translation import gettext_lazy as _
from dokument.models import DokumentAutor
from ez.models import ExterniZdrojAutor, ExterniZdrojEditor
from heslar import hesla_dynamicka
from heslar.models import RuianKatastr
from psycopg2._range import DateRange
from uzivatel.models import Osoba

register = template.Library()

logger = logging.getLogger(__name__)


@register.filter
def url_to_classes(value):
    """Převede URL cestu na CSS třídy používané v navigaci."""
    if value == "/":
        return "app-home"
    if value.endswith("/"):
        value = value[:-1]
    classes = value.replace("/", " app-")
    return classes


@register.filter
def katastry_to_list(value):
    """Vrátí seznam katastrů ve formátu odděleném středníkem."""
    value = [str(i) for i in value]
    display = "; ".join(value)
    return display


@register.filter
def hesla_to_list(value):
    """Spojí hodnoty hesel do řetězce odděleného čárkami."""
    list_hesla = ", ".join(value.values_list("heslo", flat=True))
    return list_hesla


@register.filter
def autori_ordered_list(value):
    """Vrátí autory externího zdroje v definovaném pořadí."""
    return "; ".join(
        Osoba.objects.filter(externizdrojautor__externi_zdroj=value)
        .order_by("externizdrojautor__poradi")
        .values_list("vypis_cely", flat=True)
    )


@register.filter
def render_daterange(value):
    """Naformátuje PostgreSQL DateRange do čitelné textové podoby."""
    if value == "" or value is None:
        return None
    if isinstance(value, DateRange):
        if value.lower and value.upper:
            format_str = "%-d.%-m.%Y"
            if os.name == "nt":
                format_str = "%#d.%#m.%Y"
            return (
                value.lower.strftime(format_str)
                + " - "
                + (value.upper - datetime.timedelta(days=1)).strftime(format_str)
            )
    return str(value)


@register.filter
def last_x_letters(value, x):
    """Vrátí posledních ``x`` znaků ze vstupního řetězce."""
    if len(value) > x:
        return value[-x:]
    else:
        return value


@register.filter(name="ifinlist")
def ifinlist(widget_optgroups, list):
    """Vrátí popisky voleb, jejichž hodnota je v předaném seznamu."""
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
    """Vrátí prázdný řetězec, pokud je hodnota None nebo prázdná."""
    if value:
        return value
    else:
        return ""


@register.filter
def get_katastr_name(value):
    """Převede identifikátor(y) katastru na textový název."""
    if isinstance(value, list):
        katastre = RuianKatastr.objects.filter(pk__in=value)
        katastr_str = []
        for katastr in katastre:
            katastr_str.append(katastr.nazev + " (" + katastr.okres.nazev + ")")
        list_hesla = "; ".join(katastr_str)
        return list_hesla
    else:
        katastr = RuianKatastr.objects.get(pk=value)
    return str(katastr)


@register.filter
def true_false(value):
    """Vrátí lokalizovaný text pro hodnotu ano/ne."""
    if value and value is True:
        return _("core.template_filters.true_false.true.label")
    else:
        return _("core.template_filters.true_false.false.label")


@register.filter
def get_osoby_name(widget):
    """Vrátí seznam osob vybraných ve widgetu jako text."""
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
            dok_autory = objekt.objects.filter(externi_zdroj__ident_cely=arg_list[1]).order_by("poradi")
            for item in dok_autory:
                if i == 1:
                    list_hesla = item.get_osoba()
                else:
                    list_hesla = list_hesla + "; " + item.get_osoba()
                i = i + 1
        elif "autori" in widget["name"]:
            arg_list = [arg.strip() for arg in widget["attrs"]["name_id"].split(";")]
            i = 1
            dok_autory = DokumentAutor.objects.filter(dokument__ident_cely=arg_list[1]).order_by("poradi")
            list_hesla = ""
            for item in dok_autory:
                if i == 1:
                    list_hesla = item.autor.vypis_cely
                else:
                    list_hesla = list_hesla + "; " + item.autor.vypis_cely
                i = i + 1
    else:
        osoby = Osoba.objects.filter(pk__in=widget["value"])
        list_hesla = "; ".join(osoby.values_list("vypis_cely", flat=True))
    return list_hesla


@register.simple_tag
def get_value_from_heslar(nazev_heslare, hodnota):
    """Převede klíč hesláře a hodnotu na odpovídající interní konstantu."""
    values = {
        ("externi_zdroj_typ", "kniha"): hesla_dynamicka.EXTERNI_ZDROJ_TYP_KNIHA,
        ("externi_zdroj_typ", "cast_knihy"): hesla_dynamicka.EXTERNI_ZDROJ_TYP_CAST_KNIHY,
        ("externi_zdroj_typ", "clanek_v_casopise"): hesla_dynamicka.EXTERNI_ZDROJ_TYP_CLANEK_V_CASOPISE,
        ("externi_zdroj_typ", "clanek_v_novinach"): hesla_dynamicka.EXTERNI_ZDROJ_TYP_CLANEK_V_NOVINACH,
        ("externi_zdroj_typ", "nepublikovana_zprava"): hesla_dynamicka.EXTERNI_ZDROJ_TYP_NEPUBLIKOVANA_ZPRAVA,
        ("projekt_stav", "oznameny"): constants.PROJEKT_STAV_OZNAMENY,
        ("projekt_stav", "zapsany"): constants.PROJEKT_STAV_ZAPSANY,
        ("projekt_stav", "prihlaseny"): constants.PROJEKT_STAV_PRIHLASENY,
        ("projekt_stav", "zahajeny_v_terenu"): constants.PROJEKT_STAV_ZAHAJENY_V_TERENU,
        ("projekt_stav", "ukonceny_v_terenu"): constants.PROJEKT_STAV_UKONCENY_V_TERENU,
        ("projekt_stav", "uzavreny"): constants.PROJEKT_STAV_UZAVRENY,
        ("projekt_stav", "navrzen_ke_zruseni"): constants.PROJEKT_STAV_NAVRZEN_KE_ZRUSENI,
        ("az_stav", "odeslany"): constants.AZ_STAV_ODESLANY,
        ("samostatny_nalez_stav", "odeslany"): constants.SN_ODESLANY,
        ("samostatny_nalez_stav", "potvrzeny"): constants.SN_POTVRZENY,
        ("kulturni_pamatky", "kp"): hesla_dynamicka.KULTURNI_PAMATKA_KP,
        ("kulturni_pamatky", "nkp"): hesla_dynamicka.KULTURNI_PAMATKA_NKP,
        ("kulturni_pamatky", "pz"): hesla_dynamicka.KULTURNI_PAMATKA_PZ,
        ("kulturni_pamatky", "pr"): hesla_dynamicka.KULTURNI_PAMATKA_PR,
        ("projekt_typ", "zachranny"): hesla_dynamicka.TYP_PROJEKTU_ZACHRANNY_ID,
    }
    if (nazev_heslare, hodnota) in values:
        return values[(nazev_heslare, hodnota)]
    else:
        logger.error("template_filters.get_value_from_heslar.error", extra={"heslar": nazev_heslare, "value": hodnota})
        return ""
