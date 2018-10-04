"""
Exception types used in Serde.
"""


class SerdeError(Exception):
    """
    A generic error that can occur in this package.
    """


class ModelError(SerdeError):
    """
    Raised when a Model cannot be constructed correctly.
    """


class ValidationError(SerdeError):
    """
    Raised when field validation fails.
    """


class SerializationError(SerdeError):
    """
    Raised when field serialization fails.
    """


class DeserializationError(SerdeError):
    """
    Raised when field deserialization fails.
    """
