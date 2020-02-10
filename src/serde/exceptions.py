"""
This module contains `Exception` classes that are used in Serde.
"""

from contextlib import contextmanager


__all__ = [
    'ContextError',
    'MissingDependency',
    'SerdeError',
    'ValidationError',
]


class SerdeError(Exception):
    """
    A generic error that can occur in this package.

    Args:
        message (str): a message describing the error that occurred.
    """

    @property
    def message(self):
        """
        A message describing the error that occurred.
        """
        return self.args[0]

    def __repr__(self):
        """
        Return the canonical string representation of this error.
        """
        return '<{}.{}: {}>'.format(
            self.__class__.__module__, self.__class__.__name__, str(self.message)
        )


class ContextError(SerdeError):
    """
    Raised when `Fields <serde.fields.Field>` are used in the wrong context.
    """


class MissingDependency(SerdeError):
    """
    Raised when a dependency is missing.
    """


class ValidationError(SerdeError):
    """
    Raised when any `~serde.Model` stage fails.

    Args:
        message: a message describing the error that occurred.
        value: the value which caused this error.
    """

    def __init__(self, message, value=None):
        """
        Create a new `SerdeError`.
        """
        super(SerdeError, self).__init__(message)
        self.value = value
        self._fields = []

    def messages(self):
        """
        A dictionary or list of messages that corresponds to the model structure.
        """
        from serde.fields import Field

        d = self.message
        for field in self._fields:
            # Avoids tags which might not have `_serde_name`
            if isinstance(field, Field):
                d = {field._serde_name: d}
        return d

    def __str__(self):
        """
        Return a string representation of this error.
        """
        return str(self.messages())


@contextmanager
def add_context(field):
    """
    A context manager to add the field context to a ValidationError.

    Args:
        field (~serde.fields.Field): the field context to add.
    """
    try:
        yield
    except ValidationError as e:
        e._fields.append(field)
        raise
