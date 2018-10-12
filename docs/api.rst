API Reference
=============

This part of the documentation lists the full API reference of all public
classes and functions.


Model
-----

.. autoclass:: serde.model.Model
    :members:


Core Fields
-----------

.. autoclass:: serde.field.Field
    :members: __init__, serialize, deserialize, validate

.. autoclass:: serde.field.ModelField
    :members: __init__

.. autoclass:: serde.field.InstanceField
    :members: __init__

.. autoclass:: serde.field.Bool
    :members: __init__

.. autoclass:: serde.field.Dict
    :members: __init__

.. autoclass:: serde.field.Float
    :members: __init__

.. autoclass:: serde.field.Int
    :members: __init__

.. autoclass:: serde.field.List
    :members: __init__

.. autoclass:: serde.field.Str
    :members: __init__

.. autoclass:: serde.field.Tuple
    :members: __init__


Extended Fields
---------------

.. autoclass:: serde.field.Choice
    :members: __init__

.. autoclass:: serde.field.Domain
    :members: __init__

.. autoclass:: serde.field.Email
    :members: __init__

.. autoclass:: serde.field.Slug
    :members: __init__

.. autoclass:: serde.field.Url
    :members: __init__

.. autoclass:: serde.field.Uuid
    :members: __init__


Exceptions
----------

.. autoclass:: serde.error.SerdeError
    :members: __init__

.. autoclass:: serde.error.SerializationError

.. autoclass:: serde.error.DeserializationError

.. autoclass:: serde.error.ValidationError
