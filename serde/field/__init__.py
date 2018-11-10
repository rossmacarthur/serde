"""
Field types for Serde Models.
"""

from .core import Bool, Dict, Field, Float, Instance, Int, List, Nested, Str, Tuple
from .ext import Choice, Domain, Email, Slug, Url, Uuid


__all__ = [
    'Bool', 'Boolean', 'Choice', 'Dict', 'Dictionary', 'Domain', 'Email', 'Field', 'Float',
    'Instance', 'Int', 'Integer', 'List', 'Nested', 'Slug', 'Str', 'String', 'Tuple', 'Url', 'Uuid'
]

# Aliases
Boolean = Bool
Dictionary = Dict
Integer = Int
String = Str
