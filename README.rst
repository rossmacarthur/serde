Serde
=====

.. image:: https://img.shields.io/pypi/v/serde.svg?style=flat-square&colorB=4c1
    :target: https://pypi.org/project/serde/
    :alt: PyPI Version

.. image:: https://img.shields.io/badge/docs-passing-brightgreen.svg?style=flat-square
    :target: https://ross.macarthur.io/project/serde/
    :alt: Documentation Status

.. image:: https://img.shields.io/github/workflow/status/rossmacarthur/serde/build/master?style=flat-square
    :target: https://github.com/rossmacarthur/serde/actions?query=workflow%3Abuild
    :alt: Build Status

.. image:: https://img.shields.io/codecov/c/github/rossmacarthur/serde.svg?style=flat-square
    :target: https://codecov.io/gh/rossmacarthur/serde
    :alt: Code Coverage

.. image:: https://img.shields.io/badge/code%20style-black-101010.svg?style=flat-square
    :target: https://github.com/psf/black
    :alt: Code Style

Serde is a lightweight, general-purpose framework for defining, serializing,
deserializing, and validating data structures in Python.

.. contents::
    :backlinks: none
    :local:
    :depth: 2

Getting started
---------------

Installation
^^^^^^^^^^^^

Serde is available on PyPI, you can install it using

.. code-block:: sh

    pip install serde


Extended features can be installed with the ``ext`` feature.

.. code-block:: sh

    pip install serde[ext]

Introduction
^^^^^^^^^^^^

In Serde *models* are containers for *fields*. Data structures are defined by
subclassing ``Model`` and assigning ``Field`` instances as class annotations.
These fields handle serialization, deserialization, normalization, and
validation for the corresponding model attributes.

.. code-block:: python

    from datetime import date
    from serde import Model, fields

    class Artist(Model):
        name: fields.Str()

    class Album(Model):
        title: fields.Str()
        release_date: fields.Optional(fields.Date)
        artist: fields.Nested(Artist)

    album = Album(
        title='Dangerously in Love',
        release_date=date(2003, 6, 23),
        artist=Artist(name='Beyoncé')
    )
    assert album.to_dict() == {
        'title': 'Dangerously in Love',
        'release_date': '2003-06-23',
        'artist': {
            'name': 'Beyoncé'
        }
    }

    album = Album.from_json("""{
        "title": "Lemonade",
        "artist": {"name": "Beyoncé"}}"
    """)
    assert album == Album(title='Lemonade', artist=Artist(name='Beyoncé'))

Basic usage
-----------

Below we create a ``User`` model by subclassing ``Model`` and adding the
``name`` and ``email`` fields.

.. code-block:: python

    >>> from datetime import datetime
    >>> from serde import Model, fields
    >>>
    >>> class User(Model):
    ...     name: fields.Str(rename='username')
    ...     email: fields.Email()

The corresponding attribute names are used to instantiate the model object and
access the values on the model instance.

.. code-block:: python

    >>> user = User(name='Linus Torvalds', email='torvalds@linuxfoundation.org')
    >>> user.name
    'Linus Torvalds'
    >>> user.email
    'torvalds@linuxfoundation.org'

Models are validated when they are instantiated and a ``ValidationError`` is
raised if you provide invalid values.

.. code-block:: python

    >>> User(name='Linus Torvalds', email='not an email')
    Traceback (most recent call last):
    ...
    serde.exceptions.ValidationError: {'email': 'invalid email'}

Models are serialized into primitive Python types using the ``to_dict()`` method
on the model instance.

.. code-block:: python

    >>> user.to_dict()
    OrderedDict([('username', 'Linus Torvalds'), ('email', 'torvalds@linuxfoundation.org')])

Or to JSON using the ``to_json()`` method.

.. code-block:: python

    >>> user.to_json()
    '{"username": "Linus Torvalds", "email": "torvalds@linuxfoundation.org"}'

Models are also validated when they are deserialized. Models are deserialized
from primitive Python types using the reciprocal ``from_dict()`` class method.

.. code-block:: python

    >>> user = User.from_dict({
    ...     'username': 'Donald Knuth',
    ...     'email': 'noreply@stanford.edu'
    ... })

Or from JSON using the ``from_json()`` method.

.. code-block:: python

    >>> user = User.from_json('''{
    ...     "username": "Donald Knuth",
    ...     "email": "noreply@stanford.edu"
    ... }''')

Attempting to deserialize invalid data will result in a ``ValidationError``.

.. code-block:: python

    >>> User.from_dict({'username': 'Donald Knuth'})
    Traceback (most recent call last):
    ...
    serde.exceptions.ValidationError: {'email': "missing data, expected field 'email'"}

Models
------

Models can be nested and used in container-like fields.  Below we create a
``Blog`` with an author and a list of subscribers which must all be ``User``
instances.

.. code-block:: python

    >>> class Blog(Model):
    ...     title: fields.Str()
    ...     author: fields.Nested(User)
    ...     subscribers: fields.List(User)

When instantiating you have to supply instances of the nested models.

.. code-block:: python

    >>> blog = Blog(
    ...     title="sobolevn's personal blog",
    ...     author=User(name='Nikita Sobolev', email='mail@sobolevn.me'),
    ...     subscribers=[
    ...         User(name='Ned Batchelder', email='ned@nedbatchelder.com')
    ...     ]
    ... )

Serializing a ``Blog`` would serialize the entire nested structure.

.. code-block:: python

    >>> print(blog.to_json(indent=2))
    {
      "title": "sobolevn's personal blog",
      "author": {
        "username": "Nikita Sobolev",
        "email": "mail@sobolevn.me"
      },
      "subscribers": [
        {
          "username": "Ned Batchelder",
          "email": "ned@nedbatchelder.com"
        }
      ]
    }

Similiarly deserializing a ``Blog`` would deserialize the entire nested
structure, and create instances of all the submodels.

Subclassed models
^^^^^^^^^^^^^^^^^

Models can be subclassed. The subclass will have all the fields of the parent
and any additional ones. Consider the case where we define a ``SuperUser`` model
which is a subclass of a ``User``. Simply a ``User`` that has an extra ``level``
field.

.. code-block:: python

    >>> class SuperUser(User):
    ...     # inherits name and email fields from User
    ...     level: fields.Choice(['admin', 'read-only'])

We instantiate a subclassed model as normal by passing in each field value.

.. code-block:: python

    >>> superuser = SuperUser(
    ...     name='Linus Torvalds',
    ...     email='torvalds@linuxfoundation.org',
    ...     level='admin'
    ... )

This is great for many cases, however, a commonly desired paradigm is to be able
to have the ``User.from_dict()`` class method be able to deserialize a
``SuperUser`` as well. This can be made possible through *model tagging*.

Model tagging
-------------

Model tagging is a way to mark serialized data in order to show that it is a
particular *variant* of a model. Serde provides three types of model tagging,
but you can also define you own custom ``Tag``. A ``Tag`` can be thought of in
the same way as a ``Field`` but instead of deserializing data into an attribute
on a model instance, it deserializes data into a model class.

Internally tagged
^^^^^^^^^^^^^^^^^

Internally tagged data stores a tag value inside the serialized data.

Let us consider an example where we define a ``Pet`` model with a ``tag``. We
can then subclass this model and deserialize arbitrary subclasses using the
tagged model.

.. code-block:: python

    >>> from serde import Model, fields, tags
    >>>
    >>> class Pet(Model):
    ...     name: fields.Str()
    ...
    ...     class Meta:
    ...         tag = tags.Internal(tag='species')
    ...
    >>> class Dog(Pet):
    ...     hates_cats: fields.Bool()
    ...
    >>> class Cat(Pet):
    ...     hates_dogs: fields.Bool()

We refer to the ``Dog`` and ``Cat`` subclasses as *variants* of ``Pet``. When
serializing all parent model tag serialization is done after field
serialization.

.. code-block:: python

    >>> Cat(name='Fluffy', hates_dogs=True).to_dict()
    OrderedDict([('name', 'Fluffy'), ('hates_dogs', True), ('species', '__main__.Cat')])

When deserializing, tag deserialization is done first to determine which model
to use for the deserialization.

.. code-block:: python

    >>> milo = Pet.from_dict({
    ...     'name': 'Milo',
    ...     'hates_cats': False,
    ...     'species': '__main__.Dog'
    ... })
    >>> milo.__class__
    <class '__main__.Dog'>
    >>> milo.name
    'Milo'
    >>> milo.hates_cats
    False

An invalid or missing tag will raise a ``ValidationError``.

.. code-block:: python

    >>> Pet.from_dict({'name': 'Milo', 'hates_cats': False})
    Traceback (most recent call last):
    ...
    serde.exceptions.ValidationError: missing data, expected tag 'species'
    >>>
    >>> Pet.from_dict({'name': 'Duke', 'species': '__main__.Horse'})
    Traceback (most recent call last):
    ...
    serde.exceptions.ValidationError: no variant found

Externally tagged
^^^^^^^^^^^^^^^^^

Externally tagged data uses the tag value as a key and nests the content
underneath that key. All other processes behave similarly to the internally
tagged example above.

.. code-block:: python

    >>> class Pet(Model):
    ...     name: fields.Str()
    ...
    ...     class Meta:
    ...         tag = tags.External()
    ...
    >>> class Dog(Pet):
    ...     hates_cats: fields.Bool()
    ...
    >>> Dog(name='Max', hates_cats=True).to_dict()
    OrderedDict([('__main__.Dog', OrderedDict([('name', 'Max'), ('hates_cats', True)]))])

Adjacently tagged
^^^^^^^^^^^^^^^^^

Adjacently tagged data data stores the tag value and the content underneath two
separate keys. All other processes behave similarly to the internally tagged
example.

.. code-block:: python

    >>> class Pet(Model):
    ...     name: fields.Str()
    ...
    ...     class Meta:
    ...         tag = tags.Adjacent(tag='species', content='data')
    ...
    >>> class Dog(Pet):
    ...     hates_cats: fields.Bool()
    ...
    >>> Dog(name='Max', hates_cats=True).to_dict()
    OrderedDict([('species', '__main__.Dog'), ('data', OrderedDict([('name', 'Max'), ('hates_cats', True)]))])

Abstract models
^^^^^^^^^^^^^^^

By default model tagging still allows deserialization of the base model. It is
common to have this model be abstract. You can do this by setting the
``abstract`` Meta field to ``True``. This will make it uninstantiatable and it
won't be included in the variant list during deserialization.

.. code-block:: python

    >>> class Fruit(Model):
    ...     class Meta:
    ...         abstract = True
    ...
    >>> Fruit()
    Traceback (most recent call last):
    ...
    TypeError: unable to instantiate abstract model 'Fruit'

Custom tags
^^^^^^^^^^^

It is possible to create your own custom tag class by subclassing any of
``tags.External``, ``tags.Internal``, ``tags.Adjacent`` or even the base
``tags.Tag``. This will allow customization of how the variants are looked up,
how the tag values are generated for variants, and how the data is serialized.

Consider an example where we use a class attribute ``code`` as the tag value.

.. code-block:: python

    >>> class Custom(tags.Internal):
    ...     def lookup_tag(self, variant):
    ...         return variant.code
    ...
    >>> class Pet(Model):
    ...     name: fields.Str()
    ...
    ...     class Meta:
    ...         abstract = True
    ...         tag = Custom(tag='code')
    ...
    >>> class Dog(Pet):
    ...     code = 1
    ...     hates_cats: fields.Bool()
    ...
    >>> Dog(name='Max', hates_cats=True).to_dict()
    OrderedDict([('name', 'Max'), ('hates_cats', True), ('code', 1)])
    >>> max = Pet.from_dict({'name': 'Max', 'hates_cats': True, 'code': 1})
    >>> max.__class__
    <class '__main__.Dog'>
    >>> max.name
    'Max'
    >>> max.hates_cats
    True

Fields
------

Fields do the work of serializing, deserializing, normalizing, and validating
the input values. Fields are always assigned to a model as *instances* , and
they support extra serialization, deserialization, normalization, and validation
of values without having to subclass ``Field``. For example

.. code-block:: python

    from serde import Model, fields, validators

    class Album(Model):
        title: fields.Str(normalizers=[str.strip])
        released: fields.Date(
            rename='release_date',
            validators=[validators.Min(datetime.date(1912, 4, 15))]
        )

In the above example we define an ``Album`` class. The ``title`` field is of
type `str` , and we apply the ``str.strip`` normalizer to automatically strip
the input value when instantiating or deserializing the ``Album``. The
``released`` field is of type ``datetime.date`` and we apply an extra validator
to only accept dates after 15th April 1912. Note: the ``rename`` argument only
applies to the serializing and deserializing of the data, the ``Album`` class
would still be instantiated using ``Album(released=...)``.

If these methods of creating custom ``Field`` classes are not satisfactory, you
can always subclass a ``Field`` and override the relevant methods.

.. code-block:: python

    >>> class Percent(fields.Float):
    ...     def validate(self, value):
    ...         super().validate(value)
    ...         validators.Between(0.0, 100.0)(value)

Python 2.7 and Python 3.5 compatibility
---------------------------------------

Class annotations were only added in Python 3.6, for this reason class
attributes can be used for ``Field`` definitions for projects that require
compatibility for these versions. For example

.. code-block:: python

    class Artist(Model):
        name: fields.Str()

    class Album(Model):
        title: fields.Str()
        release_date: fields.Optional(fields.Date)
        artist: fields.Nested(Artist)

is equivalent to

.. code-block:: python

    class Artist(Model):
        name = fields.Str()

    class Album(Model):
        title = fields.Str()
        release_date = fields.Optional(fields.Date)
        artist = fields.Nested(Artist)

Model states and processes
--------------------------

In Serde, there are two states that the data can be in:

* Serialized data
* Model instance

There are five different processes that the data structure can go through when
moving between these two states.

* Deserialization happens when you create a model instance from a serialized
  version using ``from_dict()`` or similar.
* Instantiation happens when you construct a model instance in Python using the
  ``__init__()`` constructor.
* Normalization happens after instantiation and after deserialization. This is
  usually a way to transform things before they are validated. For example: this
  is where an ``Optional`` field sets default values.
* Validation is where the model and fields values are validated. This happens
  after normalization.
* Serialization is when you serialize a model instance to a supported
  serialization format using ``to_dict()`` or similar.

The diagram below shows how the stages (uppercase) and processes (lowercase) fit
in with each other.

.. code-block:: text


                           +---------------+
                           | Instantiation |
                           +---------------+
                                   |
                                   v
       +---------------+   +---------------+
       |Deserialization|-->| Normalization |
       +---------------+   +---------------+
               ^                   |
               |                   v
               |           +---------------+
               |           |   Validation  |
               |           +---------------+
               |                   |
               |                   v
       +-------+-------+   +---------------+
       |SERIALIZED DATA|   | MODEL INSTANCE|
       +---------------+   +---------------+
               ^                   |
               |                   |
       +-------+-------+           |
       | Serialization |<----------+
       +---------------+

License
-------

Serde is licensed under either of

- Apache License, Version 2.0 (`LICENSE-APACHE <LICENSE-APACHE>`_ or https://www.apache.org/licenses/LICENSE-2.0)
- MIT License (`LICENSE-MIT <LICENSE-MIT>`_ or https://opensource.org/licenses/MIT)

at your option.
