import doctest
from datetime import datetime

import serde


# Project configuration
project = 'Serde'
copyright = f' {datetime.now().year:d}, {serde.__author__}'
author = serde.__author__
version = serde.__version__
release = serde.__version__

# General configuration
default_role = 'obj'
doctest_default_flags = (
    doctest.DONT_ACCEPT_TRUE_FOR_1 | doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE
)
doctest_global_setup = 'from serde import *'
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]
intersphinx_mapping = {
    'chardet': ('https://chardet.readthedocs.io/en/latest/', None),
    'python': ('https://docs.python.org/3', None),
    'validators': ('https://validators.readthedocs.io/en/latest/', None),
}
master_doc = 'index'
autodoc_member_order = 'bysource'
napoleon_include_init_with_doc = True

# HTML configuration
html_theme = 'alabaster'
html_theme_options = {
    'fixed_sidebar': True,
    'logo_name': True,
    'github_user': 'rossmacarthur',
    'github_repo': 'serde',
}
html_sidebars = {
    '**': ['about.html', 'navigation.html', 'relations.html', 'searchbox.html']
}
html_static_path = ['_static']
