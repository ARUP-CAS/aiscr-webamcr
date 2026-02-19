# Konfigurační soubor pro generátor dokumentace Sphinx.
#
# Úplný seznam vestavěných konfiguračních hodnot je v dokumentaci:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

sys.path.insert(0, os.path.abspath("../../webclient"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webclient.settings.docs")

# Setup Django
import django  # noqa: E402

django.setup()

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "aiscr-webamcr"
copyright = "CC BY 4.0"
author = "CC BY 4.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinxcontrib.googleanalytics",
    "sphinxcontrib.mermaid",
]

templates_path = ["_templates"]
exclude_patterns = []

language = "cs"

# -- Nastavení HTML výstupu --------------------------------------------------


html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_css_files = ["mermaid.css"]

autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "exclude-members": "DoesNotExist, MultipleObjectsReturned, media, render, order",
}

autodoc_mock_imports = ["django_prometheus"]

googleanalytics_id = "G-7RC46X5Q29"
