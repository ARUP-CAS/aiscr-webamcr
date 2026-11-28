"""Regrese signatur funkcí, které generátor dokumentace vypisuje na stránkách skriptů."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "docs"))
import generate_module_docs as generator  # noqa: E402  # pylint: disable=wrong-import-position


class ScriptSignatureTests(unittest.TestCase):
    """Ověří, že signatura zachová všechny druhy parametrů funkce v jejich pořadí."""

    def test_signatures_keep_every_parameter_kind(self):
        """Poziční, ``*args``, pouze pojmenované a ``**kwargs`` parametry zůstanou v signatuře."""
        source = (
            '"""Ukázkový modul."""\n\n\n'
            'def plain(a, b=1):\n    """Jen poziční parametry."""\n\n\n'
            'def variadic(*args, deadline=None):\n    """Proměnný počet a pouze pojmenovaný parametr."""\n\n\n'
            'def keyword_only(a, *, b, c=2):\n    """Pouze pojmenované parametry bez ``*args``."""\n\n\n'
            'def everything(a, /, b, *rest, c, **options):\n    """Všechny druhy parametrů."""\n'
        )
        with tempfile.TemporaryDirectory(dir=os.environ.get("TEST_TEMP_ROOT")) as directory:
            path = Path(directory) / "sample.py"
            path.write_text(source, encoding="utf-8")
            _, _, functions = generator.extract_docstrings(path)
        self.assertEqual(
            {function["name"]: function["args"] for function in functions},
            {
                "plain": ["a", "b"],
                "variadic": ["*args", "deadline"],
                "keyword_only": ["a", "*", "b", "c"],
                "everything": ["a", "/", "b", "*rest", "c", "**options"],
            },
        )


if __name__ == "__main__":
    unittest.main()
