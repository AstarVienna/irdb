# -*- coding: utf-8 -*-
"""Sphinx configuration for the Instrument Reference Database."""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("docs"))

project = "Instrument Reference Database"
copyright = "2024, A* Vienna Software Team"
author = "A* Vienna Software Team"

extensions = [
    "sphinx.ext.todo",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    "sphinx_copybutton",
    "myst_nb",
    "sphinx_design",
    "docs.source._ext.validation_report",
]

myst_enable_extensions = ["colon_fence"]
todo_include_todos = True

napoleon_numpy_docstring = True
napoleon_use_admonition_for_references = True

source_encoding = "utf-8"
source_suffix = {
    ".rst": "restructuredtext",
    ".myst": "myst-nb",
    ".md": "myst-nb",
    ".ipynb": "myst-nb",
}

nb_execution_mode = "off"

master_doc = "index"

exclude_patterns = [
    "_build",
    "docs/ScopeSim_guide.md",  # shared include file, not a standalone page
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/", None),
    "matplotlib": ("https://matplotlib.org/stable/", None),
    "astropy": ("https://docs.astropy.org/en/stable/", None),
    "synphot": ("https://synphot.readthedocs.io/en/latest/", None),
    "scopesim": ("https://scopesim.readthedocs.io/en/latest/", None),
    "scopesim_templates": ("https://scopesim-templates.readthedocs.io/en/latest/", None),
    "pyckles": ("https://pyckles.readthedocs.io/en/latest/", None),
    "anisocado": ("https://anisocado.readthedocs.io/en/latest/", None),
}

html_theme = "sphinx_book_theme"
html_theme_options = {
    "repository_url": "https://github.com/AstarVienna/irdb",
    "use_repository_button": True,
    "use_download_button": True,
    "home_page_in_toc": True,
}
html_logo = "docs/source/_static/logos/T_favicon.png"
html_favicon = "docs/source/_static/logos/T_favicon.png"
html_sidebars = {
    "**": [
        "navbar-logo.html",
        "search-field.html",
        "sbt-sidebar-nav.html",
    ]
}

html_static_path = ["docs/source/_static"]
html_css_files = ["validation_report.css"]
html_js_files = ["clickable_rows.js"]


def remove_inst_pkgs_symlink():
    """Remove inst_pkgs symlinks."""
    for path in list(Path(".").rglob("inst_pkgs")):
        if path.is_symlink():
            path.unlink()


remove_inst_pkgs_symlink()
