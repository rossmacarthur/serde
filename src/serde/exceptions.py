"""
This module contains Exception classes that are used in Serde.
"""


__all__ = [
    'DeserializationError',
    'SerdeError',
    'SerializationError',
    'SkipSerialization',
    'ValidationError'
]


class BaseSerdeError(Exception):
    """
    A generic error that can occur in this package.
    """

    def __init__(self, message=None):
        """
        Create a new BaseSerdeError.

        Args:
            message (str): a message describing the error that occurred.
        """
        super(BaseSerdeError, self).__init__(message)

    @property
    def message(self):
        """
        A message describing the error that occurred.
        """
        return self.args[0]

    def __repr__(self):
        """
        Return the canonical string representation of this BaseSerdeError.
        """
        return '<{}.{}: {}>'.format(
            self.__class__.__module__,
            self.__class__.__name__,
            self.message or '...'
        )

    def __str__(self):
        """
        Return a string representation of this BaseSerdeError..
        """
        return self.message or self.__class__.__name__


class SkipSerialization(BaseSerdeError):
    """
    Raised when a field should not be serialized.
    """


class MissingDependency(BaseSerdeError):
    """
    Raised when there is a missing dependency.
    """


class SerdeError(BaseSerdeError):
    """
    Raised when serializing, deserializing, or validating Models fails.
    """

    def __init__(self, message, cause=None, value=None, field=None, model=None):
        """
        Create a new SerdeError.

        Args:
            message (str): a message describing the error that occurred.
            cause (Exception): the exception that caused this error.
            value: the Field value context.
            field (~serde.field.Field): the Field context.
            model (~serde.model.Model): the Model context.
        """
        super(SerdeError, self).__init__(message)
        self.cause = None
        self.value = None
        self.field = None
        self.model = None
        self.add_context(cause=cause, value=value, field=field, model=model)

    def add_context(self, cause=None, value=None, field=None, model=None):
        """
        Add cause/value/field/model context.

        Args:
            cause (Exception): the exception that caused this error.
            value: the Field value context.
            field (~serde.field.Field): the Field context.
            model (~serde.model.Model): the Model context.
        """
        if cause is not None:
            self.cause = cause

        if value is not None:
            self.value = value

        if field is not None:
            self.field = field

        if model is not None:
            self.model = model


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
