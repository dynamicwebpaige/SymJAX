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
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))


# -- Project information -----------------------------------------------------

project = 'symjax'
copyright = '2020, Randall Balestriero'
author = 'Randall Balestriero'

# The full version, including alpha/beta/rc tags
release = '0.0.1'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['sphinx_rtd_theme',
              'matplotlib.sphinxext.plot_directive',
              'sphinx.ext.todo', 'sphinx.ext.viewcode',
              'sphinx.ext.autodoc', 'sphinx.ext.napoleon',
              'sphinx.ext.coverage', 'sphinx.ext.autosummary']

# See https://github.com/rtfd/readthedocs.org/issues/283
mathjax_path = ('https://cdn.mathjax.org/mathjax/latest/MathJax.js?'
                'config=TeX-AMS-MML_HTMLorMML')

# see http://stackoverflow.com/q/12206334/562769
numpydoc_show_class_members = False


# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']
# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#

#html_theme = 'alabaster'
#html_sidebars = {'**': ['localtoc.html']}
# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
#html_sidebars = {"**": ['localtoc.html']}
#import sphinx_glpi_theme

html_theme = "sphinx_rtd_theme"
#html_theme_path = sphinx_glpi_theme.get_html_themes_path()
#https://www.freelogodesign.org/preview?lang=en&name=SymJAX&logo=63cb0e66-1cfe-4204-a865-418af1550e09
html_logo = 'img/logo.png'
html_theme_options = {'logo_only': True}
import os
import sys
sys.path.insert(0, os.path.abspath('../'))
sys.setrecursionlimit(1500)
