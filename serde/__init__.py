"""
Serde - A framework for serializing and deserializing Python objects.
"""


from .error import DeserializationError, SerdeError, SerializationError, ValidationError
from .field import (
    Bool, Boolean, Choice, Dict, Dictionary, Domain, Email, Field, Float,
    Instance, Int, Integer, List, Nested, Slug, Str, String, Tuple, Url, Uuid
)
from .model import Model


__all__ = [
    'Bool', 'Boolean', 'Choice', 'DeserializationError', 'Dict', 'Dictionary', 'Domain', 'Email',
    'Field', 'Float', 'Instance', 'Int', 'Integer', 'List', 'Model', 'Nested', 'SerdeError',
    'SerializationError', 'Slug', 'Str', 'String', 'Tuple', 'Url', 'Uuid', 'ValidationError'
]
__author__ = 'Ross MacArthur'
__email__ = 'macarthur.ross@gmail.com'
__version__ = '0.1.2'
