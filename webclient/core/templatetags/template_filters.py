import datetime
import logging
import os
import re

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

OSOBY_FIELD_NAMES = frozenset({"autori", "editori", "dokument_osoba", "nalezce", "vedouci"})


@register.filter
def url_to_classes(value):
    """
    Mapuje URL cestu na CSS třídy oddělené tečkami.

    :param value: URL cesta k transformaci.
    :return: Řetězec s CSS třídami.
    """
    if value == "/":
        return "app-home"
    if value.endswith("/"):
        value = value[:-1]
    classes = value.replace("/", " app-")
    return classes


@register.filter
def katastry_to_list(value):
    """
    Vrátí seznam katastrů ve formátu odděleném středníkem.

    :param value: Parametr ``value`` předává se do volání ``join()``.

        :return: Vrací proměnná ``display``.
    """
    value = [str(i) for i in value]
    display = "; ".join(value)
    return display


@register.filter
def hesla_to_list(value):
    """
    Spojí hodnoty hesel do řetězce odděleného čárkami.

    :param value: Parametr ``value`` předává se do volání ``join()``, pracuje se s atributy ``values_list``.

        :return: Vrací proměnná ``list_hesla``.
    """
    list_hesla = ", ".join(value.values_list("heslo", flat=True))
    return list_hesla


@register.filter
def autori_ordered_list(value):
    """
    Vrátí autory externího zdroje v definovaném pořadí.

    :param value: Parametr ``value`` předává se do volání ``join()``, ``filter()``, vstupuje do návratové hodnoty.

        :return: Vrací výsledek volání ``join()``.
    """
    return "; ".join(
        Osoba.objects.filter(externizdrojautor__externi_zdroj=value)
        .order_by("externizdrojautor__poradi")
        .values_list("vypis_cely", flat=True)
    )


@register.filter
def render_daterange(value):
    """
    Naformátuje PostgreSQL DateRange do čitelné textové podoby.

    :param value: Parametr ``value`` předává se do volání ``isinstance()``, ``str()``, pracuje se s atributy ``lower``, ``upper``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

        :return: Vrací hodnotu podle větve zpracování, typicky: None, hodnotu podle větve zpracování, výsledek volání ``str()``.
    """
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
    """
    Vrátí posledních ``x`` znaků ze vstupního řetězce.

    :param value: Parametr ``value`` předává se do volání ``len()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
    :param x: Číselná hodnota ``x`` použitá při výpočtu nebo transformaci.

        :return: Vrací hodnotu podle větve zpracování, typicky: vybranou hodnotu z kolekce, proměnná ``value``.
    """
    if len(value) > x:
        return value[-x:]
    else:
        return value


@register.filter(name="ifinlist")
def ifinlist(widget_optgroups, list):
    """
    Vrátí popisky voleb, jejichž hodnota je v předaném seznamu.

    :param widget_optgroups: Textový nebo strukturální vstup `widget_optgroups` používaný při sestavení nebo zpracování obsahu.
    :param list: Kolekce ``list`` zpracovávaná touto funkcí.

        :return: Vrací proměnná ``string``.
    """
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
def is_osoby_field(value):
    """
    Vrátí True, pokud je pole jedním z osobních polí zobrazovaných přes ``get_osoby_name``.

    Django odděluje prefix formuláře pomlčkou (``prefix-pole``), zatímco názvy polí
    používají podtržítka. Porovnává se proto jen základ jména bez prefixu (např.
    ``neident-vedouci`` → ``vedouci``) – jinak by readonly zobrazení prefixovaného
    formuláře selhalo a hodnota by se nezobrazila. Porovnání je přesné proti
    :data:`OSOBY_FIELD_NAMES`, nikoli podřetězcové, aby pole jako ``osoba`` nebylo
    nesprávně vyhodnoceno jako shoda s ``dokument_osoba``.

    :param value: Název pole, případně včetně prefixu formuláře.

        :return: Vrací True, pokud základ názvu pole patří mezi osobní pole.
    """
    if not value:
        return False
    return str(value).rsplit("-", 1)[-1] in OSOBY_FIELD_NAMES


@register.filter
def check_if_none(value):
    """
    Vrátí prázdný řetězec, pokud je hodnota None nebo prázdná.

    :param value: Parametr ``value`` ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

        :return: Vrací hodnotu podle větve zpracování, typicky: proměnná ``value``, str.
    """
    if value:
        return value
    else:
        return ""


@register.filter
def get_katastr_name(value):
    """
    Vrací katastr name.

    :param value: Parametr ``value`` předává se do volání ``isinstance()``, ``filter()``, ovlivňuje větvení podmínek.

        :return: Vrací hodnotu podle větve zpracování, typicky: proměnná ``list_hesla``, výsledek volání ``str()``.
    """
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
    """
    Vrátí lokalizovaný text pro hodnotu ano/ne.

    :param value: Parametr ``value`` ovlivňuje větvení podmínek.

        :return: Vrací výsledek volání ``_()``.
    """
    if value and value is True:
        return _("core.template_filters.true_false.true.label")
    else:
        return _("core.template_filters.true_false.false.label")


@register.filter
def get_osoby_name(widget):
    """
    Vrátí seznam osob vybraných ve widgetu jako text.

    :param widget: Textový nebo strukturální vstup `widget` používaný při sestavení nebo zpracování obsahu.

        :return: Vrací proměnná ``list_hesla``.
    """
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
    """
    Vrací value from heslar.

    :param nazev_heslare: Parametr ``nazev_heslare`` se předává do volání ``error()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
    :param hodnota: Parametr ``hodnota`` se předává do volání ``error()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

        :return: Vrací hodnotu podle větve zpracování, typicky: vybranou hodnotu z kolekce, str.
    """
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


@register.filter
def unlink(cell):
    """
    Django template filter, který odstraní anchor tagy z řetězce
    a nahradí je jejich vnitřním textem.

    Příklad::

        {{ '<a href="/foo">Bar</a>'|unlink }}  →  'Bar'

    :param cell: Hodnota ke zpracování (bude převedena na řetězec).
    :type cell: any
    :returns: Vstupní řetězec, kde jsou všechny ``<a href="...">...</a>``
              tagy nahrazeny jejich vnitřním textem.
    :rtype: str
    """
    s = str(cell)
    # return the inner text of the anchor tag instead of the href attribute
    return re.sub(r'<a\s+[^>]*href=["\'][^"\']+["\'][^>]*>(.*?)</a>', r"\1", s, flags=re.IGNORECASE | re.DOTALL)
