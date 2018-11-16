import io
import os
import re

from setuptools import find_packages, setup


def read(*path):
    """
    Cross-platform Python 2/3 file reading.
    """
    filename = os.path.join(os.path.dirname(__file__), *path)

    with io.open(filename, encoding='utf8') as f:
        return f.read()


def find_version():
    """
    Regex search __init__.py so that we do not have to import.
    """
    text = read('serde', '__init__.py')
    match = re.search(r'^__version__ = [\'"]([^\'"]*)[\'"]', text, re.M)

    if match:
        return match.group(1)

    raise RuntimeError('Unable to find version string.')


version = find_version()

url = 'https://github.com/rossmacarthur/serde'

long_description = read('README.rst')

install_requires = [
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
    name='serde',
    packages=find_packages(exclude=['docs', 'tests']),
    version=version,
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

    author='Ross MacArthur',
    author_email='macarthur.ross@gmail.com',
    maintainer='Ross MacArthur',
    maintainer_email='macarthur.ross@gmail.com',
    description=('A lightweight, general-purpose, ORM framework for defining, serializing, '
                 'deserializing, and validating data structures.'),
    long_description=long_description,
    license='MIT',
    keywords='serde serialization deserialization schema json',
    url=url,
    download_url='{url}/archive/{version}.tar.gz'.format(url=url, version=version),
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
    ]
)
