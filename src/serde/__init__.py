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
`CBOR <serde.model.Model.to_cbor()>`, `TOML <serde.model.Model.to_toml()>`, and
`YAML <serde.model.Model.to_yaml()>`. See `~serde.model` for more examples.
Documentation for supported fields can be found in `~serde.fields`.
"""

from serde.model import Model


__all__ = ['Model', 'exceptions', 'fields', 'validate']
__title__ = 'serde'
__version__ = '0.4.1'
__url__ = 'https://github.com/rossmacarthur/serde'
__author__ = 'Ross MacArthur'
__author_email__ = 'ross@macarthur.io'
__license__ = 'MIT'
__description__ = 'Define, serialize, deserialize, and validate Python data structures.'
