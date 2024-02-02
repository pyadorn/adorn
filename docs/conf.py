"""Sphinx configuration."""

from datetime import datetime

project = "Adorn"
author = "Jacob Baumbach"
copyright = f"{datetime.now().year}, {author}"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinxcontrib.apidoc",
    "sphinx_rtd_theme",
]
autodoc_typehints = "description"
html_theme = "sphinx_rtd_theme"
napoleon_google_docstring = True
apidoc_module_dir = "../src/adorn"
apidoc_output_dir = "reference"
apidoc_separate_modules = True
