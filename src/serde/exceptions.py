"""
This module contains Exception classes that are used in Serde.
"""

from collections import namedtuple


__all__ = [
    'ContextError',
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


class ContextError(BaseSerdeError):
    """
    Raised when Models or Fields are used in the wrong context.
    """


class SerdeError(BaseSerdeError):
    """
    Raised when any Model stage fails.

    ::

        >>> try:
        ...     class User(Model):
        ...         age = fields.Int(validators=[validate.between(0, 100)])
        ...
        ...     User.from_dict({'age': -1})
        ... except SerdeError as e:
        ...     error = e
        ...
        >>> error.cause
        <serde.exceptions.ValidationError: expected at least 0 but got -1>
        >>> error.value
        -1
        >>> error.field.name
        'age'
        >>> error.model.__name__
        'User'
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
    def _pretty_context(context, separator='\n', prefix='Due to => ', indent=4):
        """
        Pretty format the given Context.

        Args:
            separator (str): the separator for each context.
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

        return separator.join(' ' * indent + prefix + s for s in lines)

    def pretty(self, separator='\n', prefix='Due to => ', indent=4):
        """
        Return a pretty string representation of this SerdeError.

        Args:
            separator (str): the separator for each context.
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
                separator=separator,
                prefix=prefix,
                indent=indent
            )
            for context in self.iter_contexts()
        ])

        return separator.join(lines)


class SerializationError(SerdeError):
    """
    Raised when field serialization fails.

    This would be experienced when calling a serialization method like
    `Model.to_dict() <serde.model.Model.to_dict()>`.
    """


class DeserializationError(SerdeError):
    """
    Raised when field deserialization fails.

    This would be experienced when calling a deserialization method like
    `Model.from_dict() <serde.model.Model.from_dict()>`.
    """


class InstantiationError(SerdeError):
    """
    Raised when field instantiation fails.

    This would be experienced when instantiating a Model using
    `Model.__init__() <serde.model.Model.__init__()>`.
    """


class NormalizationError(SerdeError):
    """
    Raised when field normalization fails.

    This would be experienced when normalizing a Model using
    `Model.normalize_all() <serde.model.Model.normalize_all()>`. However, since
    this method is automatically called when deserializing or instantiating a
    Model you would not typically catch this exception because it would be
    converted to an `InstantiationError` or `DeserializationError`.
    """


class ValidationError(SerdeError):
    """
    Raised when field validation fails.

    This would be experienced when validating a Model using
    `Model.validate_all() <serde.model.Model.normalize_all()>`. However, since
    this method is automatically called when deserializing or instantiating a
    Model you would not typically catch this exception because it would be
    converted to an `InstantiationError` or `DeserializationError`.
    """
