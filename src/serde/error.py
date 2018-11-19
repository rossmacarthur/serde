"""
Exception types used in Serde.
"""


class SerdeError(Exception):
    """
    A generic error that can occur in this package.
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
        super().__init__(message)
        self.cause = cause
        self.value = value
        self.field = field
        self.model = model

    @property
    def message(self):
        """
        A message describing the error that occurred.
        """
        return self.args[0]

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

    def __repr__(self):
        """
        Return the canonical string representation of this SerdeError.
        """
        return '<{}.{}: {}>'.format(
            self.__class__.__module__,
            self.__class__.__qualname__,
            self.message
        )

    def __str__(self):
        """
        Return a string representation of this SerdeError.
        """
        return self.message


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
