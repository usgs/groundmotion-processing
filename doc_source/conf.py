# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#

import os
import sys
from setuptools_scm import get_version

sys.path.insert(0, os.path.abspath(".."))


# -- Project information -----------------------------------------------------

project = 'gmprocess'
copyright = 'Unlicense'

# The full version, including alpha/beta/rc tags
base_dir = os.path.join(os.path.dirname(__file__), os.pardir)
release = get_version(root=os.path.join(base_dir))
version = release

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'autoapi.extension',
    'sphinx.ext.autosummary',
    'sphinx.ext.napoleon',
    'sphinx.ext.todo',
    'sphinx.ext.viewcode',
    'sphinx.ext.autosectionlabel',
    'sphinx_inline_tabs',
    'sphinxcontrib.programoutput',
    'myst_nb'
]

autoapi_dirs = ['../gmprocess']
autoapi_add_toctree_entry = False

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
html_static_path = [os.path.abspath('_static')]

todo_include_todos = True

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'furo'
html_logo = '_static/gmprocess_logo.png'

base_url = 'https://usgs.github.io/groundmotion-processing'

announcement_html = """
    <a href='https://www.usgs.gov/' style='text-decoration: none'>
        <img id="announcement_left_img" valign="middle" src="%s/_static/usgs.png""></a>
    Ground-Motion Processing Software
    <a href='https://github.com/usgs/groundmotion-processing' style='text-decoration: none'>
        <img id="announcement_right_img" valign="middle"
            src="%s/_static/GitHub-Mark/PNG/GitHub-Mark-Light-120px-plus.png"></a>
""" % (base_url, base_url)

html_theme_options = {
    "sidebar_hide_name": True,
    "announcement": announcement_html
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".

source_suffix = ['.rst', '.md']


def setup(app):
    app.add_css_file('css/custom.css')
