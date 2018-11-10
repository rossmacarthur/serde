Serde
=====

.. image:: https://img.shields.io/pypi/v/serde.svg?style=flat-square&colorB=4c1
    :target: https://pypi.org/project/serde/
    :alt: PyPI Version

.. image:: https://img.shields.io/readthedocs/serde/latest.svg?style=flat-square
    :target: https://serde.readthedocs.io/en/latest/
    :alt: Documentation Status

.. image:: https://img.shields.io/travis/rossmacarthur/serde.svg?style=flat-square
    :target: https://travis-ci.org/rossmacarthur/serde
    :alt: Build Status

.. image:: https://img.shields.io/codecov/c/github/rossmacarthur/serde.svg?style=flat-square
    :target: https://codecov.io/gh/rossmacarthur/serde
    :alt: Code Coverage

Serde is a general-purpose, extendable framework for serializing and
deserializing Python objects. Objects are defined with a Model schema and can be
converted to and from dictionaries and other data formats.

Installing
----------

Install this package with

::

    pip install serde


Example usage
-------------

First describe your data

.. code:: python

    class Version(Model):
        major = Integer()
        minor = Integer()
        patch = Integer(required=False, default=0)

    class Package(Model):
        name = String(rename='packageName')
        version = Nested(Version)

Easily instantiate and use a model

.. code:: python

    package = Package('requests', Version(2, 19, 1))

    assert package.name == 'requests'
    assert package.version.major == 2
    assert package.version.minor == 19
    assert package.version.patch == 1

Serialize the Model as a dictionary

.. code:: python

    assert package.to_dict() == {
        'packageName': 'requests',
        'version': {
            'major': 2,
            'minor': 19,
            'patch': 1
        }
    }

Deserialize another Model from a dictionary

.. code:: python

    package = Package.from_dict({
        'packageName': 'click',
        'version': {
            'major': 7,
            'minor': 0
        }
    })

    assert package.name == 'click'
    assert package.version.major == 7
    assert package.version.minor == 0
    assert package.version.patch == 0

License
-------

This project is licensed under the MIT License.
