"""
This module contains validators for use with `Fields <serde.fields.Field>`.
"""

import re

from serde.exceptions import ValidationError
from serde.utils import is_subclass


class Validator(object):
    """
    An abstract validator class that all validators should subclass.
    """

    def __eq__(self, other):
        """
        Whether this validator is equal to another validator.
        """
        return (
            isinstance(other, self.__class__)
            and self._attrs() == other._attrs()
        )

    def _attrs(self):
        """
        Returns a dictionary of all public attributes on this validator.
        """
        return {
            name: value for name, value in vars(self).items()
            if not name.startswith('_')
        }

    def __call__(self, value):
        """
        Call this validator on a value.
        """
        raise NotImplementedError('this method should be overridden')


class Instance(Validator):
    """
    A validator that asserts the value is an instance of a type.
    """

    def __init__(self, type):
        self.type = type

    def __call__(self, value):
        if not isinstance(value, self.type):
            raise ValidationError(
                'expected {!r} but got {!r}'
                .format(self.type.__name__, value.__class__.__name__)
            )


class Equal(Validator):
    """
    A validator that asserts the value is equal to the specified one.
    """

    def __init__(self, value):
        self.value = value

    def __call__(self, value):
        if value != self.value:
            raise ValidationError(
                'expected {!r} but got {!r}'
                .format(self.value, value)
            )


class Min(Validator):
    """
    A validator that asserts the value is greater than a minimum.

    Args:
        inclusive (bool): if this is set to `False` then the endpoint value will
            not be considered valid.
    """

    def __init__(self, endpoint, inclusive=True):
        self.endpoint = endpoint
        self.inclusive = inclusive

    def __call__(self, value):
        if self.inclusive:
            if value < self.endpoint:
                raise ValidationError(
                    'expected at least {!r} but got {!r}'
                    .format(self.endpoint, value)
                )
        else:
            if value <= self.endpoint:
                raise ValidationError(
                    'expected more than {!r} but got {!r}'
                    .format(self.endpoint, value)
                )


class Max(Validator):
    """
    A validator that asserts the value is less than a maximum.

    Args:
        inclusive (bool): if this is set to `False` then the endpoint value will
            not be considered valid.
    """

    def __init__(self, endpoint, inclusive=True):
        self.endpoint = endpoint
        self.inclusive = inclusive

    def __call__(self, value):
        if self.inclusive:
            if value > self.endpoint:
                raise ValidationError(
                    'expected at most {!r} but got {!r}'
                    .format(self.endpoint, value)
                )
        else:
            if value >= self.endpoint:
                raise ValidationError(
                    'expected less than {!r} but got {!r}'
                    .format(self.endpoint, value)
                )


class Between(Validator):
    """
    A validator that asserts the value is between two endpoints.

    Args:
        inclusive (bool): if this is set to `False` then the endpoint values
            will not be considered valid.
    """

    def __init__(self, min_endpoint, max_endpoint, inclusive=True):
        self.min_validator = Min(min_endpoint, inclusive=inclusive)
        self.max_validator = Max(max_endpoint, inclusive=inclusive)

    def __call__(self, value):
        self.min_validator(value)
        self.max_validator(value)


class Length(Equal):
    """
    A validator that asserts the value's length is a specific value.
    """

    def __call__(self, value):
        super(Length, self).__call__(len(value))


class LengthMin(Min):
    """
    A validator that asserts the value's length is greater than a minimum.

    Args:
        inclusive (bool): if this is set to `False` then the endpoint value will
            not be considered valid.
    """

    def __call__(self, value):
        super(LengthMin, self).__call__(len(value))


class LengthMax(Max):
    """
    A validator that asserts the value's length is less than a maximum.

    Args:
        inclusive (bool): if this is set to `False` then the endpoint value will
            not be considered valid.
    """

    def __call__(self, value):
        super(LengthMax, self).__call__(len(value))


class LengthBetween(Between):
    """
    A validator that asserts the value's length is between two endpoints.

    Args:
        inclusive (bool): if this is set to `False` then the endpoint values
            will not be considered valid.
    """

    def __call__(self, value):
        return super(LengthBetween, self).__call__(len(value))


class Contains(Validator):
    """
    A validator that asserts that a sequence contains a value.

    Args:
        allowed: the list/range/tuple/set of allowed values.
    """

    def __init__(self, allowed):
        self.allowed = allowed

    def __call__(self, value):
        if value not in self.allowed:
            raise ValidationError('{!r} is not a valid choice'.format(value))


class Regex(Validator):
    """
    A validator that asserts a string matches a regex.

    Args:
        pattern (str): the regex pattern that the value must match.
        flags (int): the regex flags passed directly to `re.compile`.
    """

    def __init__(self, pattern, flags=0):
        self.pattern = pattern
        self.flags = flags
        self._compiled = re.compile(pattern, flags=flags)

    def __call__(self, value):
        if not self._compiled.match(value):
            raise ValidationError(
                '{!r} does not match regex {!r}'
                .format(value, self.pattern)
            )


__all__ = [
    name for name, obj in globals().items()
    if is_subclass(obj, Validator)
]
