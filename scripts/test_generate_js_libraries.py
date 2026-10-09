"""Regresní testy metadat a stability generované tabulky JavaScript závislostí."""

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "docs"))
import generate_module_docs as generator  # noqa: E402  # pylint: disable=wrong-import-position

HOMEPAGE = "https://www.dropzone.dev/"
OLD_HOMEPAGE = "http://www.dropzonejs.com"


class JavaScriptLibrariesTests(unittest.TestCase):
    """Zastaralá instalace nesmí dodat metadata k jiné verzi z manifestu."""

    def setUp(self):
        """Připraví izolovaný projekt s přesným pinem a generovaným blokem dokumentace."""
        # unittest owns the context across setUp and the test.
        # pylint: disable-next=consider-using-with
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory(dir=os.environ.get("TEST_TEMP_ROOT"))))
        (self.root / "package.json").write_text(json.dumps({"dependencies": {"dropzone": "6.3.5"}}), encoding="utf-8")
        (self.root / "package-lock.json").write_text(
            json.dumps({"packages": {"node_modules/dropzone": {"version": "6.3.5", "license": "MIT"}}}),
            encoding="utf-8",
        )
        (self.root / "webclient").mkdir()
        (self.root / "webclient/static_vendor.json").write_text('{"libraries": []}', encoding="utf-8")
        self.output = self.root / "docs/source/12_zavislosti/javascript_knihovny.rst"
        self.output.parent.mkdir(parents=True)
        self.output.write_text(
            generator.build_rst_table([generator.JsLibrary("dropzone", "6.3.5", "MIT", HOMEPAGE)]), encoding="utf-8"
        )
        self.enterContext(patch.object(generator, "project_root", self.root))
        self.enterContext(patch.object(generator, "docs_dir", self.root / "docs"))
        self.enterContext(patch.object(generator, "changes_detected", False))

    def install_metadata(self, **values):
        """Zapíše metadata simulované instalace bez stahování či instalace balíčků.

        :param values: Pole package.json přepisující verzi, licenci či URL výchozího balíčku 6.3.5.
        """
        metadata = {"name": "dropzone", "version": "6.3.5", "license": "MIT", "homepage": HOMEPAGE}
        metadata.update(values)
        path = self.root / "node_modules/dropzone/package.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(metadata), encoding="utf-8")

    def test_stale_installation_preserves_pinned_homepage_and_license(self):
        """Verze 5.9.3 nesmí přepsat odkaz ani licenci řádku pro pin 6.3.5."""
        self.install_metadata(version="5.9.3", homepage=OLD_HOMEPAGE, license="incorrect-license")
        log = io.StringIO()
        with redirect_stdout(log):
            rows = generator.collect_libraries(
                self.root, {"dropzone": "6.3.5"}, {}, {"dropzone": HOMEPAGE}, {"dropzone": "MIT"}
            )
        self.assertEqual((rows[0].version, rows[0].homepage, rows[0].license), ("6.3.5", HOMEPAGE, "MIT"))
        self.assertIn("installed 5.9.3, expected 6.3.5; run npm ci", log.getvalue())

    def test_matching_metadata_regenerates_the_correct_homepage(self):
        """Platná metadata 6.3.5 opraví starý odkaz přímo přes vlastní generátor."""
        self.install_metadata()
        self.output.write_text(
            generator.build_rst_table([generator.JsLibrary("dropzone", "6.3.5", "MIT", OLD_HOMEPAGE)]), encoding="utf-8"
        )
        self.assertTrue(generator.generate_js_libraries_rst())
        self.assertEqual(
            generator.parse_preserved_js_library_links(self.output.read_text(encoding="utf-8")), {"dropzone": HOMEPAGE}
        )
        self.assertTrue(generator.changes_detected)

    def test_stale_or_absent_installation_keeps_repeated_generation_stable(self):
        """Bez instalace i se starou verzí zůstane uložená dokumentace při opakování stejná."""
        generator.generate_js_libraries_rst()
        expected = self.output.read_bytes()
        self.install_metadata(version="5.9.3", homepage=OLD_HOMEPAGE)
        with redirect_stdout(io.StringIO()):
            for _ in range(2):
                generator.changes_detected = False
                self.assertTrue(generator.generate_js_libraries_rst())
                self.assertEqual(self.output.read_bytes(), expected)
                self.assertFalse(generator.changes_detected)

    def test_unknown_version_does_not_supply_metadata_and_new_package_gets_npm_link(self):
        """Chybějící instalovaná verze nedodá cizí metadata ani novému řádku bez uloženého odkazu."""
        self.install_metadata(version=None, homepage=OLD_HOMEPAGE)
        with redirect_stdout(io.StringIO()):
            rows = generator.collect_libraries(self.root, {"dropzone": "6.3.5"}, {"dropzone": "MIT"})
        self.assertEqual(rows[0].homepage, generator.npm_package_page_url("dropzone"))
        self.assertEqual(rows[0].license, "MIT")

    def test_matching_metadata_supports_license_object_and_repository_fallback(self):
        """Shodná verze zachová zpracování staršího formátu licence a URL git repozitáře."""
        self.install_metadata(
            license={"type": "MIT"}, homepage="", repository={"url": "git+https://example.com/repo.git"}
        )
        self.assertEqual(
            generator.read_node_module_metadata(self.root, "dropzone", "6.3.5"), ("MIT", "https://example.com/repo")
        )
        # Existing callers may explicitly omit the version guard for generic metadata reads.
        self.assertEqual(
            generator.read_node_module_metadata(self.root, "dropzone"), ("MIT", "https://example.com/repo")
        )


if __name__ == "__main__":
    unittest.main()
