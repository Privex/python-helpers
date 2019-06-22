# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))

import os
import sys

# Add base directory of the project to the path
sys.path.insert(0, os.path.abspath('../..'))

# -- Project information -----------------------------------------------------

project = 'Privex Python Helpers'
copyright = '2019, Privex Inc.'
author = 'Privex Inc.'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    'sphinx.ext.ifconfig',
    'sphinx.ext.viewcode',
]

autosummary_generate = True

autodoc_default_flags = ['members']

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = None

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

html_style = 'css/custom.css'

html_logo = '_static/brand_text_nofont.svg'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
html_theme_options = {
    'navigation_depth': 7,
    'collapse_navigation': False,
    'style_nav_header_background': '#473E53',
}


# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

html_theme_path = ["_themes", ]

# -- Options for HTMLHelp output ---------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'PrivexHelpersDoc'


# -- Options for LaTeX output ------------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',

    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',

    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',

    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, 'PrivexHelpers.tex', 'Privex Python Helpers Documentation',
     'Privex Inc., Chris (Someguy123)', 'manual'),
]


# -- Options for manual page output ------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, 'privexhelpers', 'Privex Python Helpers Documentation',
     [author], 1)
]


# -- Options for Texinfo output ----------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (master_doc, 'PrivexHelpers', 'CryptoToken Converter Documentation',
     author, 'PrivexHelpers', 'One line description of project.',
     'Miscellaneous'),
]


# -- Options for Epub output -------------------------------------------------

# Bibliographic Dublin Core info.
epub_title = project

# The unique identifier of the text. This can be a ISBN number
# or the project homepage.
#
# epub_identifier = ''

# A unique identification for the text.
#
# epub_uid = ''

# A list of files that should not be packed into the epub file.
epub_exclude_files = ['search.html']


# -- Extension configuration -------------------------------------------------

# -- Options for intersphinx extension ---------------------------------------

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {'https://docs.python.org/': None}



"""
Taken from https://stackoverflow.com/a/30783465/2648583
"""
# from sphinx.ext.autosummary import Autosummary
# from sphinx.ext.autosummary import get_documenter
# from docutils.parsers.rst import directives
# from sphinx.util.inspect import safe_getattr
# import re

# class AutoAutoSummary(Autosummary):

#     option_spec = {
#         'methods': directives.unchanged,
#         'attributes': directives.unchanged
#     }

#     required_arguments = 1

#     @staticmethod
#     def get_members(obj, typ, include_public=None):
#         if not include_public:
#             include_public = []
#         items = []
#         for name in dir(obj):
#             try:
#                 documenter = get_documenter(safe_getattr(obj, name), obj)
#             except AttributeError:
#                 continue
#             if documenter.objtype == typ:
#                 items.append(name)
#         public = [x for x in items if x in include_public or not x.startswith('_')]
#         return public, items

#     def run(self):
#         clazz = str(self.arguments[0])
#         try:
#             (module_name, class_name) = clazz.rsplit('.', 1)
#             m = __import__(module_name, globals(), locals(), [class_name])
#             c = getattr(m, class_name)
#             if 'methods' in self.options:
#                 _, methods = self.get_members(c, 'method', ['__init__'])

#                 self.content = ["~%s.%s" % (clazz, method) for method in methods if not method.startswith('_')]
#             if 'attributes' in self.options:
#                 _, attribs = self.get_members(c, 'attribute')
#                 self.content = ["~%s.%s" % (clazz, attrib) for attrib in attribs if not attrib.startswith('_')]
#         finally:
#             return super(AutoAutoSummary, self).run()
# def setup(app):
#     app.add_directive('autoautosummary', AutoAutoSummary)