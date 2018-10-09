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
    :members: __init__, serialize, deserialize, validate
    :show-inheritance:


.. autoclass:: serde.field.InstanceField
    :members: __init__, serialize, deserialize, validate
    :show-inheritance:


.. autoclass:: serde.field.Bool
    :members: __init__, serialize, deserialize, validate
    :show-inheritance:


.. autoclass:: serde.field.Dict
    :members: __init__, serialize, deserialize, validate
    :show-inheritance:


.. autoclass:: serde.field.Float
    :members: __init__, serialize, deserialize, validate
    :show-inheritance:


.. autoclass:: serde.field.Int
    :members: __init__, serialize, deserialize, validate
    :show-inheritance:


.. autoclass:: serde.field.List
    :members: __init__, serialize, deserialize, validate
    :show-inheritance:


.. autoclass:: serde.field.Str
    :members: __init__, serialize, deserialize, validate
    :show-inheritance:


.. autoclass:: serde.field.Tuple
    :members: __init__, serialize, deserialize, validate
    :show-inheritance:


Extended Fields
---------------



Exceptions
----------

.. autoclass:: serde.error.SerdeError
    :members:
    :show-inheritance:


.. autoclass:: serde.error.SerializationError
    :members:
    :show-inheritance:


.. autoclass:: serde.error.DeserializationError
    :members:
    :show-inheritance:


.. autoclass:: serde.error.ValidationError
    :members:
    :show-inheritance:
