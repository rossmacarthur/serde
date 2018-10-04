import io
import os
import re

from setuptools import setup


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

package_requirements = [
    'twine'
]

setup(
    name='serde',
    packages=['serde'],
    version=version,
    extras_require={'linting': lint_requirements,
                    'testing': test_requirements,
                    'packaging': package_requirements},
    python_requires='>=3.4',

    author='Ross MacArthur',
    author_email='macarthur.ross@gmail.com',
    description='A framework for serializing and deserializing Python objects.',
    long_description=long_description,
    license='MIT',
    keywords='serde',
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
