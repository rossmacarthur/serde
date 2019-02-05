"""
This module contains Exception classes that are used in Serde.
"""

from collections import namedtuple


__all__ = [
    'DeserializationError',
    'InstantiationError',
    'NormalizationError',
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
        Return a string representation of this BaseSerdeError.
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

    Context = namedtuple('Context', 'cause value field model')

    def __init__(self, message, cause=None, value=None, field=None, model=None):
        """
        Create a new SerdeError.

        Args:
            message (str): a message describing the error that occurred.
            cause (Exception): an exception for this context.
            value: the value which caused this error.
            field (serde.fields.Field): the Field where this error happened.
            model (serde.model.Model): the Model where this error happened.
        """
        super(SerdeError, self).__init__(message)
        self.contexts = []

        if cause or value or field or model:
            self.add_context(cause, value, field, model)

    def add_context(self, cause=None, value=None, field=None, model=None):
        """
        Add another context to this SerdeError.

        Args:
            cause (Exception): an exception for this context.
            value: the value which caused this error.
            field (~serde.fields.Field): the Field where this error happened.
            model (~serde.model.Model): the Model where this error happened.
        """
        self.contexts.append(SerdeError.Context(cause, value, field, model))

    def iter_contexts(self):
        """
        Iterate through the contexts in reverse order.
        """
        return reversed(self.contexts)

    @classmethod
    def from_exception(cls, exception, value=None, field=None, model=None):
        """
        Create a new SerdeError from another Exception.

        Args:
            exception (Exception): the Exception to convert from.
            value: the value which caused this error.
            field (~serde.fields.Field): the Field where this error happened.
            model (~serde.model.Model): the Model where this error happened.

        Returns:
            SerdeError: an instance of SerdeError.
        """
        if isinstance(exception, SerdeError):
            self = cls(exception.message)
            exception.contexts, self.contexts = [], exception.contexts
            self.add_context(exception, value, field, model)
            return self
        else:
            return cls(str(exception) or repr(exception), exception, value, field, model)

    def __getattr__(self, name):
        """
        Get an attribute of a SerdeError.
        """
        if name in ('cause', 'value', 'field', 'model'):
            for context in self.contexts:
                value = getattr(context, name)

                if value is not None:
                    return value

            return None

        return self.__getattribute__(name)

    @staticmethod
    def _pretty_context(context, seperator='\n', prefix='Due to => ', indent=4):
        """
        Pretty format the given Context.

        Args:
            seperator (str): the seperator for each context.
            prefix (str): the prefix for each context. Example: 'Caused by: '.
            indent (int): the number of spaces to indent each context line.

        Returns:
            str: the pretty formatted Context.
        """
        lines = []

        if context.value or context.field or context.model:
            s = ''

            if context.value is not None:
                value = repr(context.value)

                if len(value) > 30:
                    value = value[:26] + '... '

                s += 'value {} '.format(value)

            if context.field is not None:
                s += 'for field {!r} of type {!r} '.format(
                    context.field._name,
                    context.field.__class__.__name__
                )

            if context.model is not None:
                s += 'on model {!r} '.format(context.model.__name__)

            lines.append(s.strip())

        if context.cause is not None:
            if isinstance(context.cause, SerdeError):
                lines.append(context.cause.pretty())
            else:
                lines.append(repr(context.cause) or str(context.cause))

        return seperator.join(' ' * indent + prefix + s for s in lines)

    def pretty(self, seperator='\n', prefix='Due to => ', indent=4):
        """
        Return a pretty string representation of this SerdeError.

        Args:
            seperator (str): the seperator for each context.
            prefix (str): the prefix for each context. Example: 'Caused by: '.
            indent (int): the number of spaces to indent each context line.

        Returns:
            str: the pretty formatted SerdeError.
        """
        lines = [self.__class__.__name__]

        if self.message:
            lines[0] += ': ' + self.message

        lines.extend([
            self._pretty_context(
                context,
                seperator=seperator,
                prefix=prefix,
                indent=indent
            )
            for context in self.iter_contexts()
        ])

        return seperator.join(lines)


class SerializationError(SerdeError):
    """
    Raised when field serialization fails.
    """


class DeserializationError(SerdeError):
    """
    Raised when field deserialization fails.
    """


class InstantiationError(SerdeError):
    """
    Raised when field instantiation fails.
    """


class NormalizationError(SerdeError):
    """
    Raised when field normalization fails.
    """


class ValidationError(SerdeError):
    """
    Raised when field validation fails.
    """
