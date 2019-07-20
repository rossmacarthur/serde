"""
Serde is a lightweight, general-purpose, powerful ORM framework for defining,
serializing, deserializing, and validating data structures in Python.

Basic usage
-----------

In Serde, `Models <serde.model.Model>` are containers for `Fields
<serde.fields.Field>`. Data structures are defined by subclassing
`~serde.model.Model` and assigning `~serde.fields.Field` instances as class
attributes. The `~serde.fields.Field` instances handle serialization,
deserialization and validation for these attributes. Documentation for supported
fields can be found in the `~serde.fields` module.

In the following example ``Person`` subclasses `Model <serde.model.Model>` and
adds two fields ``name`` and ``birthday``.

::

    >>> from serde import Model, fields

    >>> class Person(Model):
    ...     name = fields.Str()
    ...     birthday = fields.Optional(fields.Date)

Models are validated when they are instantiated and after they are deserialized.

::

    >>> person = Person(
    ...     name='Benedict Cumberbatch',
    ...     birthday=datetime.date(1976, 7, 19)
    ... )

    >>> person.name
    'Benedict Cumberbatch'
    >>> person.birthday
    datetime.date(1976, 7, 19)

Models can be serialized and deserialized from different data formats. The most
basic format is primitive Python types. To do this we call the
`~serde.model.Model.to_dict()` method on the ``Person`` instance.

::

    >>> assert person.to_dict() == {
    ...     'name': 'Benedict Cumberbatch',
    ...     'birthday': '1976-07-19'
    ... }

To deserialize a Model we simply call the reciprocal method. For example, to
deserialize a ``Person`` from a dictionary we use the
`~serde.model.Model.from_dict()` class method.

::

    >>> person = Person.from_dict({
    ...     'name': 'Idris Elba',
    ...     'birthday': '1972-09-06'
    ... })

    >>> person.name
    'Idris Elba'
    >>> person.birthday
    datetime.date(1972, 9, 6)

Other supported data formats include `JSON <serde.model.Model.to_json()>`,
`Pickle <serde.model.Model.to_pickle()>`, `CBOR <serde.model.Model.to_cbor()>`,
`TOML <serde.model.Model.to_toml()>`, and `YAML <serde.model.Model.to_yaml()>`.

Nested Models
-------------

`Models <serde.model.Model>` can be nested and used in container fields. For
example, let's say we wanted to represent a group of ``Persons``.

::

    >>> class Group(Model):
    ...     name = fields.Str()
    ...     lead = fields.Nested(Person)
    ...     members = fields.List(Person)

When instantiating you have to supply instances of the nested Models.

::

    >>> group = Group(
    ...     name='The Lonely Island',
    ...     lead=Person(name='Andy Samberg'),
    ...     members=[
    ...         Person(name='Akiva Schaffer'),
    ...         Person(name='Jorma Taccone')
    ...     ]
    ... )

    >>> group.name
    'The Lonely Island'
    >>> group.lead
    Person(name='Andy Samberg')
    >>> group.members
    [Person(name='Akiva Schaffer'), Person(name='Jorma Taccone')]

Serializing a ``Group`` would serialize the entire nested structure.

::

    >>> assert group.to_dict() ==  {
    ...     'name': 'The Lonely Island',
    ...     'lead': {'name': 'Andy Samberg'},
    ...     'members': [
    ...         {'name': 'Akiva Schaffer'},
    ...         {'name': 'Jorma Taccone'}
    ...     ]
    ... }

Similiarly deserializing a ``Group`` would deserialize the entire nested
structure, and create instances of all the submodels.

::

    >>> group = Group.from_dict({
    ...     'name': 'One-man Wolf Pack',
    ...     'lead': {'name': 'Alan Garner'},
    ...     'members': []
    ... })

    >>> group.name
    'One-man Wolf Pack'
    >>> group.lead
    Person(name='Alan Garner')
    >>> group.members
    []

Subclassed Models
------------------

Defined data structures can be subclassed. The subclass will have all the fields
of the parent and any additional ones. Consider the case where we define a
``User`` model which is a subclass of a ``Person``; simply a ``Person`` that has
extra ``id`` and ``email`` attributes.

::

    >>> class User(Person):
    ...     id = fields.Int(validators=[validate.min(1)])
    ...     email = fields.Email()

We instantiate it as normal by passing in each field value.

::

    >>> user = User(
    ...     id=1,
    ...     name='Linus Benedict Torvalds',
    ...     birthday=datetime.date(1969, 12, 28),
    ...     email='torvalds@linuxfoundation.org'
    ... )

    >>> user.id
    1
    >>> user.name
    'Linus Benedict Torvalds'

This is great for many cases, however, a commonly desired paradigm is to be able
to have the ``Person.from_dict()`` method be able to deserialize a ``User``.
This is made possible through tagging. Let's redesign our ``Person`` model to
include Model tagging.

::

    >>> class Person(Model):
    ...     class Meta:
    ...         tag = 'kind'
    ...
    ...     name = fields.Str()
    ...     birthday = fields.Optional(fields.Date)

This will *internally tag* our serialized data, and expect tagged data when
deserializing.

::

    >>> Person.from_dict({  # doctest: +SKIP
    ...     'kind': 'User',
    ...     'id': 2,
    ...     'name': 'Guido van Rossum',
    ...     'email': 'guido@python.org'
    ... })
    User(name='Guido van Rossum', id=2, email='guido@python.org')

We refer to the ``Person`` subclass as a *variant* of a ``User``.

Customizing Subclassed Models
-----------------------------

There are four types of `Model <serde.model.Model>` tagging and they are each
described below. These examples only show deserialization, but the tagging does
work for serialization as well.

Externally tagged
~~~~~~~~~~~~~~~~~

Externally tagged data uses the tag value as a key and nests the content
underneath that key. You can enable *external tagging* by setting the ``tag``
field to ``True``.

::

    >>> class Pet(Model):
    ...     class Meta:
    ...         tag = True
    ...
    ...     name = fields.Str()

    >>> class Dog(Pet):
    ...     hates_cats = fields.Bool()

    >>> Pet.from_dict({'Dog': {'name': 'Max', 'hates_cats': True}})
    Dog(name='Max', hates_cats=True)

Internally tagged
~~~~~~~~~~~~~~~~~

Internally tagged data stores the tag value at a key of value ``tag``, inside
the serialized data.  You can enable *internal tagging* by setting the ``tag``
field to a string value.

::

    >>> class Pet(Model):
    ...     class Meta:
    ...         tag = 'species'
    ...
    ...     name = fields.Str()

    >>> class Dog(Pet):
    ...     hates_cats = fields.Bool()

    >>> Pet.from_dict({'species': 'Dog', 'name': 'Max', 'hates_cats': True})
    Dog(name='Max', hates_cats=True)

Adjacently tagged
~~~~~~~~~~~~~~~~~

Adjacently tagged data data stores the tag value and the content underneath two
separate keys.  You can enable *adjacent tagging* by setting the ``tag`` *and*
content field to string values.

::

    >>> class Pet(Model):
    ...     class Meta:
    ...         tag = 'species'
    ...         content = 'data'
    ...
    ...     name = fields.Str()

    >>> class Dog(Pet):
    ...     hates_cats = fields.Bool()

    >>> Pet.from_dict({'species': 'Dog', 'data': {'name': 'Max', 'hates_cats': True}})
    Dog(name='Max', hates_cats=True)

Untagged
~~~~~~~~

Untagged data will try to deserialize each variant in turn. The first variant
that succeeds deserialization will be returned. You can enable this by setting
the ``tag`` field to ``False``.

::

    >>> class Pet(Model):
    ...     class Meta:
    ...         tag = False
    ...
    ...     name = fields.Str()

    >>> class Dog(Pet):
    ...     hates_cats = fields.Bool()

    >>> Pet.from_dict({'name': 'Max', 'hates_cats': True})
    Dog(name='Max', hates_cats=True)

Abstract Models
~~~~~~~~~~~~~~~

All of the above methods allow deserialization of the base Model. It is common
to have this Model be abstract. You can do this by setting the ``abstract``
Meta field to ``True``. This will make it uninstantiatable and it won't be
included in the variant list during deserialization.

::

    >>> class Fruit(Model):
    ...     class Meta:
    ...         abstract = True

    >>> Fruit()
    Traceback (most recent call last):
        ...
    serde.exceptions.InstantiationError: unable to instantiate abstract Model 'Fruit'

Model states and processes
--------------------------

In the **Serde** paradigm, there are two states that the data can be in:

- Serialized data
- Model instance

There are five different processes that the data structure can go through when
moving between these two states.

- Deserialization happens when you create a Model instance from a serialized
  version using `Model.from_dict() <serde.model.Model.from_dict()>` or similar.
- Instantiation happens when you construct a Model instance in Python using
  `Model.__init__() <serde.model.Model.__init__()>`.
- Normalization happens after instantiation and after deserialization. This is
  usually a way to transform things before they are validated. For example: this
  is where an `~serde.fields.Optional` field sets default values.
- Validation is where the Model and Fields are validated. This happens after
  normalization.
- Serialization is when you serialize a Model instance to a supported
  serialization format using `Model.to_dict() <serde.model.Model.to_dict()>` or
  similar.

The diagram below shows how the stages (uppercase) and processes (lowercase) fit
in with each other.

::

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
"""

from serde.model import Model


__all__ = ['Model', 'exceptions', 'fields', 'validate']
__title__ = 'serde'
__version__ = '0.6.2'
__url__ = 'https://github.com/rossmacarthur/serde'
__author__ = 'Ross MacArthur'
__author_email__ = 'ross@macarthur.io'
__license__ = 'MIT'
__description__ = 'Define, serialize, deserialize, and validate Python data structures.'
