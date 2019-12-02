"""
Serde is a lightweight, general-purpose framework for defining, serializing,
deserializing, and validating data structures in Python.
"""

from serde.model import Model


__all__ = ['Model', 'exceptions', 'fields', 'tags', 'validators']
__title__ = 'serde'
__version__ = '0.7.2'
__url__ = 'https://github.com/rossmacarthur/serde'
__author__ = 'Ross MacArthur'
__author_email__ = 'ross@macarthur.io'
__license__ = 'MIT'
__description__ = 'Define, serialize, deserialize, and validate Python data structures.'
