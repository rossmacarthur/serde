"""
Exception types used in Serde.
"""


class SerdeError(Exception):
    """
    A generic error that can occur in this package.
    """


class SerializationError(SerdeError):
    """
    Raised when field serialization fails.
    """


class DeserializationError(SerdeError):
    """
    Raised when field deserialization fails.
    """


class ValidationError(SerdeError):
    """
    Raised when field validation fails.
    """
