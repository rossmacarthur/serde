"""
Field types for Serde Models.
"""

from .core import Bool, Dict, Field, Float, InstanceField, Int, List, ModelField, Str, Tuple
from .ext import Choice, Domain, Email, Slug, Url, Uuid


# Aliases
Boolean = Bool
Dictionary = Dict
Integer = Int
String = Str

__all__ = [
    'Bool', 'Boolean', 'Choice', 'Dict', 'Dictionary', 'Domain', 'Email',
    'Field', 'Float', 'InstanceField', 'Int', 'Integer', 'List', 'ModelField',
    'Slug', 'Str', 'String', 'Tuple', 'Url', 'Uuid'
]
