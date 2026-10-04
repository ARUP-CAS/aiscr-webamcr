import json

from scripts.check_static_vendor_manifest import collect_errors


def _write(path, content=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _library(**overrides):
    lib = {
        "name": "Leaflet Foo",
        "version": "1.0.0",
        "license": "MIT",
        "source": "https://example.org/leaflet-foo",
        "paths": ["vendor/leaflet-foo/foo.js"],
        "modified": False,
    }
    lib.update(overrides)
    return lib


def _repo(tmp_path, libraries, dependencies=None):
    _write(tmp_path / "webclient/static_vendor.json", json.dumps({"libraries": libraries}))
    _write(tmp_path / "package.json", json.dumps({"dependencies": dependencies or {}}))
    _write(tmp_path / "webclient/static/vendor/leaflet-foo/foo.js", "// foo")
    return tmp_path


def test_consistent_manifest_has_no_errors(tmp_path):
    """Manifest pokrývající všechny soubory ve vendor/ projde bez chyb.

    :param tmp_path: Dočasný adresář pytestu použitý jako kořen repozitáře.
    """
    root = _repo(tmp_path, [_library()])
    _write(root / "webclient/templates/base.html", "{% static 'vendor/leaflet-foo/foo.js' %}")

    assert collect_errors(root) == []


def test_file_in_vendor_missing_from_manifest(tmp_path):
    """Nový soubor ve vendor/ bez záznamu v manifestu je chyba.

    :param tmp_path: Dočasný adresář pytestu použitý jako kořen repozitáře.
    """
    root = _repo(tmp_path, [_library()])
    _write(root / "webclient/static/vendor/leaflet-bar/bar.js", "// bar")

    errors = collect_errors(root)

    assert len(errors) == 1
    assert "vendor/leaflet-bar/bar.js" in errors[0]


def test_missing_version_and_nonexistent_path(tmp_path):
    """Prázdná verze a neexistující cesta se hlásí zvlášť.

    :param tmp_path: Dočasný adresář pytestu použitý jako kořen repozitáře.
    """
    root = _repo(tmp_path, [_library(version="", paths=["vendor/leaflet-foo/foo.js", "vendor/leaflet-foo/x.css"])])

    errors = collect_errors(root)

    assert any("'version'" in e for e in errors)
    assert any("vendor/leaflet-foo/x.css" in e and "neexistuje" in e for e in errors)


def test_vendor_dir_duplicates_npm_dependency(tmp_path):
    """Adresář ve vendor/ se jménem npm závislosti je duplicita.

    :param tmp_path: Dočasný adresář pytestu použitý jako kořen repozitáře.
    """
    root = _repo(tmp_path, [_library()], dependencies={"leaflet-foo": "1.0.0"})

    errors = collect_errors(root)

    assert len(errors) == 1
    assert "package.json" in errors[0]


def test_template_reference_outside_manifest(tmp_path):
    """Šablona odkazující na soubor ve vendor/, který v manifestu není, je chyba.

    :param tmp_path: Dočasný adresář pytestu použitý jako kořen repozitáře.
    """
    root = _repo(tmp_path, [_library()])
    _write(root / "webclient/pas/templates/pas/coor.html", '\n<script src="{% static "vendor/gone/gone.js" %}">')

    errors = collect_errors(root)

    assert len(errors) == 1
    assert "coor.html:2" in errors[0]
    assert "vendor/gone/gone.js" in errors[0]


def test_css_url_to_missing_file(tmp_path):
    """Relativní url() v CSS z manifestu, které nemíří na existující soubor, je chyba.

    :param tmp_path: Dočasný adresář pytestu použitý jako kořen repozitáře.
    """
    css = "vendor/leaflet-foo/foo.css"
    root = _repo(tmp_path, [_library(paths=["vendor/leaflet-foo/foo.js", css])])
    _write(root / "webclient/static/img/ok.png")
    _write(
        root / "webclient/static" / css,
        ".a{background:url('../../img/ok.png')}\n.b{background:url(../img/gone.png)}\n.c{background:url(data:x)}",
    )

    errors = collect_errors(root)

    assert len(errors) == 1
    assert "foo.css:2" in errors[0]
    assert "../img/gone.png" in errors[0]


def test_path_outside_static_is_rejected(tmp_path):
    """Cesty mimo webclient/static/ (``..``, absolutní, s diskem) manifest odmítne bez čtení souboru.

    :param tmp_path: Dočasný adresář pytestu použitý jako kořen repozitáře.
    """
    bad = ["../static_vendor.json", "/etc/passwd", "C:/x.css", r"vendor\leaflet-foo\foo.js"]
    root = _repo(tmp_path, [_library(paths=["vendor/leaflet-foo/foo.js", *bad])])

    errors = collect_errors(root)

    assert len(errors) == len(bad)
    assert all("musí být relativní" in e for e in errors)
