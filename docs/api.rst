API Reference
=============

This part of the documentation lists the full API reference of all public
classes and functions.


Model
-----

.. autoclass:: serde.model.Model
    :members:


Fields
------

.. autoclass:: serde.field.Field
    :members:


.. autoclass:: serde.field.ModelField
    :members:
    :show-inheritance:


.. autoclass:: serde.field.Array
    :members:
    :show-inheritance:


.. autoclass:: serde.field.Map
    :members:
    :show-inheritance:


.. autoclass:: serde.field.Parts
    :members:
    :show-inheritance:


Fields for built-in types
-------------------------

.. autoclass:: serde.field.InstanceField
    :members:
    :show-inheritance:


.. autoclass:: serde.field.Boolean
    :show-inheritance:


.. autoclass:: serde.field.Bytes
    :show-inheritance:


.. autoclass:: serde.field.Dictionary
    :show-inheritance:


.. autoclass:: serde.field.Float
    :show-inheritance:


.. autoclass:: serde.field.Integer
    :show-inheritance:


.. autoclass:: serde.field.List
    :show-inheritance:


.. autoclass:: serde.field.String
    :show-inheritance:


.. autoclass:: serde.field.Tuple
    :show-inheritance:


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
