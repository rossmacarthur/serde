"""
Serde - A framework for serializing and deserializing Python objects.
"""


from serde.error import DeserializationError, SerdeError, SerializationError, ValidationError
from serde.field import (Bool, Choice, Dict, Domain, Email, Field, Float, InstanceField,
                         Int, List, ModelField, Slug, Str, Tuple, Url, Uuid)
from serde.model import Model


__all__ = ['Bool', 'Choice', 'DeserializationError', 'Dict', 'Domain', 'Email', 'Field',
           'Float', 'InstanceField', 'Int', 'List', 'Model', 'ModelField', 'SerdeError',
           'SerializationError', 'Slug', 'Str', 'Tuple', 'Url', 'Uuid', 'ValidationError']
__author__ = 'Ross MacArthur'
__email__ = 'macarthur.ross@gmail.com'
__version__ = '0.1.1'
