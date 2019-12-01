"""
This module contains `Exception` classes that are used in Serde.
"""

from contextlib import contextmanager


__all__ = [
    'Context',
    'ContextError',
    'DeserializationError',
    'InstantiationError',
    'NormalizationError',
    'SerdeError',
    'SerializationError',
    'ValidationError',
]


class BaseError(Exception):
    """
    A generic error that can occur in this package.

    Args:
        message (str): a message describing the error that occurred.
    """

    def __init__(self, message):
        """
        Create a new `BaseError`.
        """
        super(BaseError, self).__init__(message)

    @property
    def message(self):
        """
        A message describing the error that occurred.
        """
        return self.args[0]

    def __repr__(self):
        """
        Return the canonical string representation.
        """
        return '<{}.{}: {}>'.format(
            self.__class__.__module__, self.__class__.__name__, self.message
        )

    def __str__(self):
        """
        Return a string representation.
        """
        return self.message


class MissingDependency(BaseError):
    """
    Raised when a dependency is missing.
    """


class SerdeError(BaseError):
    """
    Raised when any `~serde.Model` stage fails.

    Attributes:
        message: a message describing the error that occurred.
        cause: an exception for this context.
        value: the value which caused this error.
        field: the field context.
        model_cls: the model class context.
    """

    def __init__(self, message, cause=None, value=None, field=None, model_cls=None):
        """
        Create a new `SerdeError`.
        """
        super(SerdeError, self).__init__(message)
        self.contexts = []

        if cause or value or field or model_cls:
            self.add_context(cause=cause, value=value, field=field, model_cls=model_cls)

    def add_context(self, cause=None, value=None, field=None, model_cls=None):
        """
        Add another context to this SerdeError.

        Args:
            cause (Exception): an exception for this context.
            value: the value which caused this error.
            field (~serde.fields.Field): the Field context.
            model_cls (~serde.Model): the Model class context.
        """
        self.contexts.append(
            Context(cause=cause, value=value, field=field, model_cls=model_cls)
        )

    def iter_contexts(self):
        """
        Iterate through the contexts in reverse order.
        """
        return reversed(self.contexts)

    @classmethod
    def from_exception(cls, exception, value=None, field=None, model_cls=None):
        """
        Create a new SerdeError from another Exception.

        Args:
            exception (Exception): the Exception to convert from.
            value: the value which caused this error.
            field (~serde.fields.Field): the Field context.
            model_cls (~serde.Model): the Model class context.

        Returns:
            SerdeError: an instance of SerdeError.
        """
        if isinstance(exception, SerdeError):
            new = cls(exception.message)
            exception.contexts, new.contexts = [], exception.contexts
            new.add_context(exception, value, field, model_cls)
            return new
        else:
            return cls(
                str(exception) or repr(exception), exception, value, field, model_cls
            )

    def __getattr__(self, name):
        """
        Get an attribute of a SerdeError.
        """
        if name in ('cause', 'value', 'field', 'model_cls'):
            for context in self.contexts:
                value = getattr(context, name)

                if value is not None:
                    return value

            return None

        return self.__getattribute__(name)

    def pretty(self, separator='\n', prefix='Due to => ', indent=4):
        """
        Return a pretty string representation of this `SerdeError`.

        Args:
            separator (str): the separator for each context.
            prefix (str): the prefix for each context. Example: 'Caused by: '.
            indent (int): the number of spaces to indent each context line.

        Returns:
            str: the pretty formatted `SerdeError`.
        """
        lines = [self.__class__.__name__]
        if self.message:
            lines[0] += ': ' + self.message

        lines.extend(
            [
                context.pretty(separator=separator, prefix=prefix, indent=indent)
                for context in self.iter_contexts()
            ]
        )

        return separator.join(lines)


class SerializationError(SerdeError):
    """
    Raised when `~serde.Model` or `~serde.fields.Field` serialization fails.

    This would be experienced when calling a serialization method like
    `Model.to_dict() <serde.Model.to_dict()>`.
    """


class DeserializationError(SerdeError):
    """
    Raised when `~serde.Model` or `~serde.fields.Field` deserialization fails.

    This would be experienced when calling a deserialization method like
    `Model.from_dict() <serde.Model.from_dict()>`.
    """


class InstantiationError(SerdeError):
    """
    Raised when `~serde.Model` or `~serde.fields.Field` instantiation fails.

    This would be experienced when instantiating a Model using
    `Model.__init__() <serde.Model.__init__()>`.
    """


class NormalizationError(SerdeError):
    """
    Raised when `~serde.Model` or `~serde.fields.Field` normalization fails.

    This would be experienced when normalizing a Model using `Model._normalize()
    <serde.Model._normalize()>`. However, since this method is automatically
    called when deserializing or instantiating a Model you would not typically
    catch this exception because it would be converted to an
    `InstantiationError` or `DeserializationError`.
    """


class ValidationError(SerdeError):
    """
    Raised when `~serde.Model` or `~serde.fields.Field` validation fails.

    This would be experienced when validating a Model using `Model._validate()
    <serde.Model._validate()>`. However, since this method is automatically
    called when deserializing or instantiating a Model you would not typically
    catch this exception because it would be converted to an
    `InstantiationError` or `DeserializationError`.
    """


class ContextError(BaseError):
    """
    Raised when `Fields <serde.fields.Field>` are used in the wrong context.
    """


class Context(object):
    """
    Contextual information about a `SerdeError`.

    Args:
        cause (Exception): an exception for this context.
        value: the value which caused this error.
        field (~serde.fields.Field): the field context.
        model_cls (~serde.Model): the model class context.
    """

    def __init__(self, cause=None, value=None, field=None, model_cls=None):
        """
        Create a new `Context`.
        """
        self.cause = cause
        self.value = value
        self.field = field
        self.model_cls = model_cls

    def _pretty_cause(self, separator, prefix, indent):
        if isinstance(self.cause, SerdeError):
            return self.cause.pretty(separator=separator, prefix=prefix, indent=indent)
        else:
            return repr(self.cause)

    def _pretty_value(self):
        if self.value is None:
            return ''

        msg = 'value {value}{suffix}'

        value = repr(self.value)
        if len(value) > 30:
            value = value[:26] + '... '

        return msg.format(value=value, suffix='' if self.field is None else ' for ')

    def _pretty_field(self):
        if not self.field:
            return ''

        from serde.fields import Field
        from serde.tags import Tag

        type_ = self.field.__class__.__name__
        suffix = ' on ' if self.model_cls else ''

        if isinstance(self.field, Field):
            return 'field {field!r} of type {type!r}{suffix}'.format(
                field=self.field._attr_name, type=type_, suffix=suffix
            )
        elif isinstance(self.field, Tag):
            return 'tag {type!r}{suffix}'.format(type=type_, suffix=suffix)

    def _pretty_model_cls(self):
        if not self.model_cls:
            return ''

        return 'model {type!r}'.format(type=self.model_cls.__name__)

    def pretty(self, separator='\n', prefix='Due to => ', indent=4):
        """
        Pretty format the given `Context`.

        Args:
            separator (str): the separator for each context.
            prefix (str): the prefix for each context. Example: 'Caused by: '.
            indent (int): the number of spaces to indent each context line.

        Returns:
            str: the pretty formatted contextual information.
        """
        lines = []

        if self.value or self.field or self.model_cls:
            lines.append(
                self._pretty_value() + self._pretty_field() + self._pretty_model_cls()
            )

        if self.cause:
            lines.append(self._pretty_cause(separator, prefix, indent))

        return separator.join(' ' * indent + prefix + s for s in lines)


@contextmanager
def map_errors(error, value=None, field=None, model_cls=None):
    """
    A context manager that maps generic exceptions to the given SerdeError.

    Args:
        error (SerdeError): a SerdeError to wrap any generic exceptions that are
            generated by the Field function.
        value: the value which caused this error.
        field (~serde.fields.Field): the Field context.
        model_cls (~serde.Model): the Model class context.
    """
    try:
        yield
    except error as e:
        e.add_context(value=value, field=field, model_cls=model_cls)
        raise
    except Exception as e:
        raise error.from_exception(e, value=value, field=field, model_cls=model_cls)
