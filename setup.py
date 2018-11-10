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

install_requirements = [
    'validators>=0.12.0<0.13.0'
]

toml_requirements = [
    'toml>=0.10.0<0.11.0'
]

yaml_requirements = [
    'ruamel.yaml>=0.15.0<0.16.0'
]

lint_requirements = [
    'flake8',
    'flake8-docstrings',
    'flake8-isort',
    'flake8-per-file-ignores',
    'flake8-quotes',
    'mccabe',
    'pep8-naming'
]

test_requirements = [
    'pytest',
    'pytest-cov'
]

document_requirements = [
    'sphinx'
]

package_requirements = [
    'twine'
]

setup(
    name='serde',
    packages=find_packages(exclude=['docs', 'tests']),
    version=version,
    install_requires=install_requirements,
    extras_require={
        'toml': toml_requirements,
        'yaml': yaml_requirements,
        'linting': lint_requirements,
        'testing': test_requirements,
        'documenting': document_requirements,
        'packaging': package_requirements
    },
    python_requires='>=3.4',

    author='Ross MacArthur',
    author_email='macarthur.ross@gmail.com',
    description='A framework for serializing and deserializing Python objects.',
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
        'Programming Language :: Python :: 3.7'
    ]
)
