"""
Exception types used in Serde.
"""


class SerdeError(Exception):
    """
    A generic error that can occur in this package.
    """

    def __init__(self, message, cause=None, field=None, model=None):
        """
        Create a new SerdeError.

        Args:
            message (str): a message describing the error that occurred.
            field (~serde.field.Field): the field context.
            model (~serde.model.Model): the model context.
        """
        super().__init__()
        self.message = message
        self.cause = cause
        self.model = model

    def add_context(self, cause=None, field=None, model=None):
        """
        Add cause/field/model context to this SerdeError.
        """
        self.cause = cause
        self.field = field
        self.model = model

    def __repr__(self):
        """
        Return the canonical string representation of this SerdeError.
        """
        return '<{}.{}: {}>'.format(self.__class__.__module__,
                                    self.__class__.__qualname__,
                                    self.message)

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
