import io
import os
import re

from setuptools import find_packages, setup


here = os.path.abspath(os.path.dirname(__file__))

with io.open(os.path.join(here, 'src', 'serde', '__init__.py'), encoding='utf8') as f:
    about_text = f.read()

metadata = {
    key: re.search(r'__' + key + r'__ = ["\'](.*?)["\']', about_text).group(1)
    for key in ('title', 'version', 'url', 'author', 'author_email', 'license', 'description')
}

metadata['name'] = metadata.pop('title')

with io.open(os.path.join(here, 'README.rst'), encoding='utf8') as f:
    metadata['long_description'] = f.read()

install_requires = [
    'isodate>=0.6.0<0.7.0',
    'validators>=0.12.0<0.13.0'
]

toml_requires = [
    'toml>=0.10.0<0.11.0'
]

yaml_requires = [
    'ruamel.yaml>=0.15.0<0.16.0'
]

lint_requires = [
    'flake8',
    'flake8-docstrings',
    'flake8-isort',
    'flake8-per-file-ignores',
    'flake8-quotes',
    'pep8-naming'
]

test_requires = [
    'pytest>=3.3.0',
    'pytest-cov',
    'pytest-doctest-import'
]

document_requires = [
    'sphinx'
]

package_requires = [
    'twine'
]

setup(
    # Options
    install_requires=install_requires,
    extras_require={
        'toml': toml_requires,
        'yaml': yaml_requires,
        'linting': lint_requires,
        'testing': test_requires,
        'documenting': document_requires,
        'packaging': package_requires
    },
    python_requires='>=3.4',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=['serde'],

    # Metadata
    download_url='{url}/archive/{version}.tar.gz'.format(**metadata),
    project_urls={
        'Documentation': 'https://serde.readthedocs.io',
        'Issue Tracker': '{url}/issues'.format(**metadata)
    },
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    keywords='serde serialization deserialization schema json',
    **metadata
)
