Serde
=====

.. image:: https://img.shields.io/pypi/v/serde.svg?style=flat-square&colorB=4c1
    :target: https://pypi.org/project/serde/
    :alt: PyPI Version

.. image:: https://img.shields.io/badge/docs-passing-brightgreen.svg?style=flat-square
    :target: https://ross.macarthur.io/project/serde/
    :alt: Documentation Status

.. image:: https://img.shields.io/travis/rossmacarthur/serde/master.svg?style=flat-square
    :target: https://travis-ci.org/rossmacarthur/serde
    :alt: Build Status

.. image:: https://img.shields.io/codecov/c/github/rossmacarthur/serde.svg?style=flat-square
    :target: https://codecov.io/gh/rossmacarthur/serde
    :alt: Code Coverage

Serde is a lightweight, general-purpose, powerful ORM framework for defining,
serializing, deserializing, and validating data structures in Python.

Getting started
---------------

Install this package with

::

    pip install serde


Example usage
-------------

Define your data structures in a clean and obvious way.

.. code:: python

    >>> from serde import Model, fields

    >>> class Dog(Model):
    ...     name = fields.Str()
    ...     hates_cats = fields.Optional(fields.Bool, default=True)

    >>> class Owner(Model):
    ...     name = fields.Str()
    ...     birthday = fields.Date()
    ...     dog = fields.Nested(Dog)

Easily serialize and deserialize arbitrary data to and from Python objects.

.. code:: python

    >>> owner = Owner.from_json('''{
    ...     "name": "Paris Hilton",
    ...     "birthday": "1981-02-17",
    ...     "dog": {"name": "Tinkerbell"}
    ... }''')

    >>> owner.name
    'Paris Hilton'
    >>> owner.birthday
    datetime.date(1981, 2, 17)
    >>> owner.dog
    Dog(name='Tinkerbell', hates_cats=True)

View the latest usage and API documentation
`here <https://ross.macarthur.io/project/serde/api.html>`_.

License
-------

This project is licensed under the MIT License.
