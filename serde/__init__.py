"""
Serde - A framework for serializing and deserializing Python objects.
"""


from serde.error import DeserializationError, SerdeError, SerializationError, ValidationError
from serde.field import (
    Bool, Boolean, Choice, Dict, Dictionary, Domain, Email, Field, Float,
    InstanceField, Int, Integer, List, ModelField, Slug, Str, String, Tuple, Url, Uuid
)
from serde.model import Model


__all__ = [
    'Bool', 'Boolean', 'Choice', 'DeserializationError', 'Dict', 'Dictionary', 'Domain', 'Email',
    'Field', 'Float', 'InstanceField', 'Int', 'Integer', 'List', 'Model', 'ModelField',
    'SerdeError', 'SerializationError', 'Slug', 'Str', 'String', 'Tuple', 'Url', 'Uuid',
    'ValidationError'
]
__author__ = 'Ross MacArthur'
__email__ = 'macarthur.ross@gmail.com'
__version__ = '0.1.2'
