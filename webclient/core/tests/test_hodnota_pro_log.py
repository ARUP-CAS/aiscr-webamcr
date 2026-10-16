"""Testy helperu ``core.utils.hodnota_pro_log`` (issue #4397)."""

import json
import logging
from decimal import Decimal

from core.utils import hodnota_pro_log
from django import forms
from django.forms import formset_factory
from django.http import QueryDict
from django.test import SimpleTestCase
from django.utils.translation import gettext_lazy
from logstash.formatter import LogstashFormatterVersion1


class _Formular(forms.Form):
    """Formulář s jedním povinným polem pro vyvolání chyb validace."""

    nazev = forms.CharField()


class HodnotaProLogTest(SimpleTestCase):
    """Výsledek musí být vždy řetězec, aby ho Elasticsearch přijal do pole typu ``text``."""

    def test_chyby_formulare_zachovaji_zpravy(self):
        """``ErrorDict`` se převede přes ``get_json_data()``, ne na prázdné seznamy."""
        formular = _Formular(data={})
        self.assertFalse(formular.is_valid())

        vysledek = json.loads(hodnota_pro_log(formular.errors))

        self.assertEqual(list(vysledek), ["nazev"])
        self.assertEqual(vysledek["nazev"][0]["code"], "required")

    def test_chyby_formsetu(self):
        """``formset.errors`` je seznam ``ErrorDict`` - každý se převede zvlášť."""
        formset = formset_factory(_Formular, min_num=1, validate_min=True)(
            data={"form-TOTAL_FORMS": "1", "form-INITIAL_FORMS": "0", "form-0-nazev": ""}
        )
        self.assertFalse(formset.is_valid())

        vysledek = json.loads(hodnota_pro_log(formset.errors))

        self.assertEqual(vysledek[0]["nazev"][0]["code"], "required")

    def test_querydict_lazy_preklad_a_decimal(self):
        """Neserializovatelné hodnoty se převedou přes ``str()`` a ``QueryDict`` jako dict."""
        vysledek = json.loads(
            hodnota_pro_log({"post": QueryDict("a=1&b=2"), "zprava": gettext_lazy("Test"), "cislo": Decimal("1.50")})
        )

        self.assertEqual(vysledek, {"post": {"a": "1", "b": "2"}, "zprava": "Test", "cislo": "1.50"})

    def test_vnoreny_json_retezec_se_rozbali(self):
        """Řetězec s JSON objektem uvnitř (``optimistic_lock_data``) se nezakóduje podruhé."""
        vysledek = hodnota_pro_log({"vedouci": 1, "optimistic_lock_data": '{"vedouci": 1, "organizace": 2}'})

        self.assertEqual(vysledek, '{"vedouci": 1, "optimistic_lock_data": {"vedouci": 1, "organizace": 2}}')
        self.assertNotIn("\\", vysledek)

    def test_text_zacinajici_zavorkou_zustane(self):
        """Text, který jen začíná závorkou a není to JSON, zůstane beze změny."""
        self.assertEqual(json.loads(hodnota_pro_log({"a": "[poznámka"})), {"a": "[poznámka"})

    def test_logstash_posle_retezec(self):
        """Po průchodu formatterem ``python-logstash`` je pole řetězec, ne JSON objekt."""
        zaznam = logging.LogRecord("test", logging.DEBUG, __file__, 1, "zprava", None, None)
        zaznam.data = hodnota_pro_log({"cadastre": "Andělka", "akce_ident_cely": "C-201121404A01"})

        udalost = json.loads(LogstashFormatterVersion1().format(zaznam))

        self.assertIsInstance(udalost["data"], str)
        self.assertIn("Andělka", udalost["data"])
