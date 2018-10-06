from recommonmark.parser import CommonMarkParser
from recommonmark.transform import AutoStructify

import serde


# Project configuration
project = 'Serde'
copyright = '2018, Ross MacArthur'
author = 'Ross MacArthur'
version = serde.__version__
release = serde.__version__

# General configuration
default_role = 'obj'
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode'
]
intersphinx_mapping = {'python': ('https://docs.python.org/3', None)}
master_doc = 'index'
napoleon_include_init_with_doc = True
source_parsers = {'.md': CommonMarkParser}
source_suffix = ['.rst', '.md']


def setup(app):
    app.add_config_value('recommonmark_config', {
        'auto_toc_tree_section': 'API Reference',
        'enable_eval_rst': True,
        'enable_auto_doc_ref': True,
    }, True)
    app.add_transform(AutoStructify)


# HTML configuration
html_theme = 'alabaster'
html_theme_options = {
    'fixed_sidebar': True,
    'logo_name': True,
    'github_user': 'rossmacarthur',
    'github_repo': 'serde'
}
html_sidebars = {
    '**': [
        'about.html',
        'navigation.html',
        'relations.html',
        'searchbox.html'
    ]
}
