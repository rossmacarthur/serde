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
