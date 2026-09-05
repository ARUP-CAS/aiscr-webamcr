"""Jednotkové testy pro ``cron.tasks.translation_value`` a ``core.views._translate_status_value``."""

import json

from core.views import _translate_status_value
from cron.tasks import translation_value
from django.test import SimpleTestCase


class TranslationValueTest(SimpleTestCase):
    """Ověřuje tvar obálky produkované ``translation_value`` — zejména umístění ``raw`` příznaku."""

    def test_no_params_returns_plain_message_id(self):
        """Bez parametrů se vrací přímo ID jako plain string, nikoli JSON obálka."""
        self.assertEqual(
            translation_value("cron.tasks.run_data_import.finished"), "cron.tasks.run_data_import.finished"
        )

    def test_params_without_raw_wraps_id_and_params(self):
        """Parametrizovaná zpráva (bez ``raw``) se zabalí do ``{"id", "params"}`` bez klíče ``raw``."""
        value = translation_value("cron.tasks.run_data_import.importing_record_data", n=3, total=10)

        decoded = json.loads(value)
        self.assertEqual(decoded["id"], "cron.tasks.run_data_import.importing_record_data")
        self.assertEqual(decoded["params"], {"n": 3, "total": 10})
        self.assertNotIn("raw", decoded)

    def test_raw_true_puts_raw_flag_at_top_level(self):
        """``raw=True`` musí uložit příznak na nejvyšší úroveň obálky, ne do ``params``."""
        value = translation_value("cron.tasks.run_data_import.error.raw", raw=True, message="boom")

        decoded = json.loads(value)
        self.assertIs(decoded.get("raw"), True)
        # The `raw` flag itself must not leak into params — only the actual message data belongs there.
        self.assertEqual(decoded["params"], {"message": "boom"})

    def test_raw_false_explicit_behaves_like_default(self):
        """Explicitní ``raw=False`` se chová stejně jako výchozí (bez ``raw``) parametrizovaná obálka."""
        value = translation_value("cron.tasks.run_data_import.importing_record_data", raw=False, n=1, total=2)

        decoded = json.loads(value)
        self.assertNotIn("raw", decoded)
        self.assertEqual(decoded["params"], {"n": 1, "total": 2})

    def test_raw_true_without_extra_params_still_sets_top_level_flag(self):
        """``raw=True`` bez dalších parametrů stále vytvoří obálku (nevrací se plain ID)."""
        value = translation_value("cron.tasks.run_data_import.error.raw", raw=True)

        decoded = json.loads(value)
        self.assertIs(decoded.get("raw"), True)
        self.assertEqual(decoded["params"], {})


class TranslationValueRoundTripTest(SimpleTestCase):
    """Ověřuje round-trip ``translation_value`` -> ``_translate_status_value`` pro čtenáře v core.views."""

    def test_round_trip_raw_envelope_returns_message_verbatim(self):
        """Obálka s ``raw=True`` se musí vrátit doslova — beze změny a bez pokusu o překlad."""
        message = "Simulované selhání Fedora repozitáře: Traceback (most recent call last): ..."
        value = translation_value("cron.tasks.run_data_import.error.raw", raw=True, message=message)

        self.assertEqual(_translate_status_value(value), message)

    def test_round_trip_raw_message_with_braces_is_not_treated_as_format_template(self):
        """Zprávy obsahující ``{``/``}`` (např. dict repr, traceback) se nesmí lámat na ``str.format``."""
        message = "MIME mismatch for record {pk: 42, 'extra': {'nested': True}}"
        value = translation_value("cron.tasks.run_data_import.error.raw", raw=True, message=message)

        self.assertEqual(_translate_status_value(value), message)

    def test_round_trip_formatted_envelope_interpolates_params(self):
        """Bez ``raw`` se ID přeloží (zde beze změny, žádný .po není zkompilován) a naformátuje parametry."""
        value = translation_value("Row {n}/{total}", n=3, total=10)

        self.assertEqual(_translate_status_value(value), "Row 3/10")

    def test_round_trip_plain_id_returns_translated_string(self):
        """Plain ID (bez parametrů) projde překladem beze změny, když není zkompilován žádný ``.po``."""
        value = translation_value("cron.tasks.run_data_import.finished")

        self.assertEqual(_translate_status_value(value), "cron.tasks.run_data_import.finished")

    def test_round_trip_none_returns_none(self):
        """``None`` (klíč v Redis dosud neexistuje) se musí vrátit jako ``None``, nikoli vyhodit výjimku."""
        self.assertIsNone(_translate_status_value(None))
