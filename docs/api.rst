API
===

This part of the documentation lists the full API reference of all public
classes and functions.

.. autoclass:: serde.Model
    :members: to_dict, to_json, from_dict, from_json, normalize, validate

Fields
------

.. automodule:: serde.fields
.. autoclass:: serde.fields.Field

Primitives
^^^^^^^^^^

.. autoclass:: serde.fields.Bool
.. autoclass:: serde.fields.Bytes
.. autoclass:: serde.fields.Complex
.. autoclass:: serde.fields.Float
.. autoclass:: serde.fields.Int
.. autoclass:: serde.fields.Str
.. autoclass:: serde.fields.Text

Containers
^^^^^^^^^^

In container fields each element is serialized, deserialized, normalized and
validated with the specified element type. The element type can be specified
using `Field` classes, `Field` instances, `~serde.Model` classes, or built-in
types that have a corresponding field type in this library.

.. autoclass:: serde.fields.Nested
.. autoclass:: serde.fields.Optional
.. autoclass:: serde.fields.Dict
.. autoclass:: serde.fields.OrderedDict
.. autoclass:: serde.fields.List
.. autoclass:: serde.fields.Deque
.. autoclass:: serde.fields.Set
.. autoclass:: serde.fields.FrozenSet
.. autoclass:: serde.fields.Tuple

Standard library
^^^^^^^^^^^^^^^^

.. autoclass:: serde.fields.DateTime
.. autoclass:: serde.fields.Date
.. autoclass:: serde.fields.Time
.. autoclass:: serde.fields.Uuid
.. autoclass:: serde.fields.Regex

Miscellanous
^^^^^^^^^^^^

.. autoclass:: serde.fields.Choice
.. autoclass:: serde.fields.Literal

Extended
^^^^^^^^

The following fields are available with the ``ext`` feature.

.. autoclass:: serde.fields.Domain
.. autoclass:: serde.fields.Email
.. autoclass:: serde.fields.Ipv4Address
.. autoclass:: serde.fields.Ipv6Address
.. autoclass:: serde.fields.MacAddress
.. autoclass:: serde.fields.Slug
.. autoclass:: serde.fields.Url

Tags
----

.. automodule:: serde.tags

.. autoclass:: serde.tags.Tag
    :members: variants, lookup_tag, lookup_variant

.. autoclass:: serde.tags.External
.. autoclass:: serde.tags.Internal
.. autoclass:: serde.tags.Adjacent

Validators
----------

.. automodule:: serde.validators
    :members:

Exceptions
----------

.. automodule:: serde.exceptions

.. autoexception:: serde.exceptions.SerdeError
    :members: iter_contexts, pretty

.. autoexception:: serde.exceptions.SerializationError
.. autoexception:: serde.exceptions.DeserializationError
.. autoexception:: serde.exceptions.InstantiationError
.. autoexception:: serde.exceptions.NormalizationError
.. autoexception:: serde.exceptions.ValidationError
.. autoexception:: serde.exceptions.MissingDependency
