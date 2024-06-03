# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Python modules --
# system

import pathlib
import sys

FACILERS = pathlib.Path(__file__).parents[3]
sys.path.insert(0, FACILERS.resolve().as_posix())

# 3rd party

from sphinx_pyproject import SphinxConfig
from facile_rs import __version__ as myproject_version

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

config = SphinxConfig("../../../pyproject.toml", globalns=globals(), config_overrides = {"version": myproject_version})

project = config.name
author = config.author
description = config.description

# project = 'FACILE-RS'
# copyright = '2024, FACILE-RS'
# author = 'FACILE-RS'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
  'sphinx.ext.duration',
  'sphinx.ext.doctest',
  'autodoc2',
  'sphinx.ext.autosummary',
  'myst_parser',
  ]

autodoc2_packages = ["../../../facile_rs",]

autodoc2_render_plugin = "myst"  # render files as Markdown with ".md" extension

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = 'traditional'
html_theme = 'classic'
html_theme_options = {
  # 'nosidebar': False,
  'sidebarwidth': '350px',
  'collapsiblesidebar': True,
  }
html_copy_source = False
globaltoc_collapse = True
modindex_common_prefix = [
  'facile_rs.',
  'facile_rs.utils.',
  'facile_rs.utils.metadata.'
  ]


# These two options don't seem to have any effect
add_module_names = False
# python_use_unqualified_type_names = True

html_static_path = ['_static']