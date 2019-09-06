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

Containers
^^^^^^^^^^

.. autoclass:: serde.fields.Nested
.. autoclass:: serde.fields.Dict
.. autoclass:: serde.fields.List
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

.. autoclass:: serde.fields.Constant
.. autoclass:: serde.fields.Choice

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
