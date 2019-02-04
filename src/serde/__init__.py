"""
Serde is a lightweight, general-purpose, ORM framework for defining,
serializing, deserializing, and validating data structures in Python.

Objects are defined by subclassing `~serde.model.Model` and assigning
`~serde.fields.Field` attributes on the Model. In the following example `User`
is the subclassed `~serde.model.Model` with two fields `name` and `age`. The
`~serde.fields.Str` and `~serde.fields.Int` classes handle serialization,
deserialization, and validation for these attributes.

::

    >>> from serde import Model, fields

    >>> class User(Model):
    ...     name = fields.Str(rename='username')
    ...     age = fields.Optional(fields.Int)

Models are validated when they are instantiated and after they are deserialized.

::

    >>> user = User(name='Benedict Cumberbatch', age=42)
    >>> user.name
    'Benedict Cumberbatch'
    >>> user.age
    42

Models can be serialized and deserialized from different data formats. The most
basic format is primitive Python types. To do this we call the
`~serde.model.Model.to_dict()` method.

::

    >>> user.to_dict() # doctest: +SKIP
    {'username': 'Benedict Cumberbatch', 'age', 42}

To deserialize a Model we simply call the reciprocal method. For example to
deserialize a `User` from a dictionary we use the
`~serde.model.Model.from_dict()` method.

::

    >>> user = User.from_dict({'username': 'Idris Elba', 'age': 46})
    >>> user.name
    'Idris Elba'
    >>> user.age
    46

Other supported data formats including `JSON <serde.model.Model.to_json()>`,
`Pickle <serde.model.Model.to_pickle()>`, `CBOR <serde.model.Model.to_cbor()>`,
`TOML <serde.model.Model.to_toml()>`, and `YAML <serde.model.Model.to_yaml()>`.
See `~serde.model` for more examples. Documentation for supported fields can be
found in `~serde.fields`.

The Stages
----------

There are five main stages that Model or Model instance can go through.

- **Deserialization** happens when you create a Model instance from a serialized
  version using `Model.from_dict() <serde.model.Model.from_dict()>` or similar.
- **Instantiation** happens when you construct a Model instance in Python using
  `Model.__init__() <serde.model.Model.__init__()>`.
- **Normalization** happens after instantiation and after deserialization. This
  is usually a way to transform things before they are validated. For example:
  this is where an `~serde.fields.Optional` field sets defaults.
- **Validation** is where the Model and Fields are validated.
- **Serialization** is when you serialize a Model instance to a supported
  serialization format using `Model.to_dict() <serde.model.Model.to_dict()>` or
  similar.

The diagram below shows how the stages fit in with each other.

::

                              +---------------+
                              | Instantiation |---+
                              +---------------+   |
                                                  v
                   +-----------------+    +---------------+    +------------+
            +----->| Deserialization |--->| Normalization |--->| Validation |--+
            |      +-----------------+    +---------------+    +------------+  |
    +-------------+                                                            |
    |             |                             +----------+                   |
    |  SERIALIZED |      +---------------+      |          |                   |
    |    DATA     |<-----| Serialization |<-----|  MODEL   |<------------------+
    |             |      +---------------+      | INSTANCE |
    +-------------+                             |          |
                                                +----------+

"""

from serde.model import Model


__all__ = ['Model', 'exceptions', 'fields', 'validate']
__title__ = 'serde'
__version__ = '0.5.2'
__url__ = 'https://github.com/rossmacarthur/serde'
__author__ = 'Ross MacArthur'
__author_email__ = 'ross@macarthur.io'
__license__ = 'MIT'
__description__ = 'Define, serialize, deserialize, and validate Python data structures.'
