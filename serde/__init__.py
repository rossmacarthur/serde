"""
Serde - A framework for serializing and deserializing Python objects.
"""


from .error import DeserializationError, SerdeError, SerializationError, ValidationError
from .field import (Array, Boolean, Bytes, Dictionary, Field, Float, InstanceField,
                    Integer, List, Map, ModelField, Parts, String, Tuple, TypeField)
from .model import Model


__all__ = ['Array', 'Boolean', 'Bytes', 'DeserializationError', 'Dictionary',
           'Field', 'Float', 'InstanceField', 'Integer', 'List', 'Map',
           'Model', 'ModelField', 'Parts', 'SerdeError', 'SerializationError',
           'String', 'Tuple', 'TypeField', 'ValidationError', 'error', 'field']
__author__ = 'Ross MacArthur'
__email__ = 'macarthur.ross@gmail.com'
__version__ = '0.1.0'
