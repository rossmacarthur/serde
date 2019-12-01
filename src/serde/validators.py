"""
This module contains validators for use with `Fields <serde.fields.Field>`.
"""

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
        return isinstance(other, self.__class__) and self._attrs() == other._attrs()

    def _attrs(self):
        """
        Returns a dictionary of all public attributes on this validator.
        """
        return {
            name: value
            for name, value in vars(self).items()
            if not name.startswith('_')
        }

    def __call__(self, value):
        """
        Call this validator on a value.
        """
        raise NotImplementedError('this method should be overridden')


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
                    'expected at least {!r} but got {!r}'.format(self.endpoint, value)
                )
        else:
            if value <= self.endpoint:
                raise ValidationError(
                    'expected more than {!r} but got {!r}'.format(self.endpoint, value)
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
                    'expected at most {!r} but got {!r}'.format(self.endpoint, value)
                )
        else:
            if value >= self.endpoint:
                raise ValidationError(
                    'expected less than {!r} but got {!r}'.format(self.endpoint, value)
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


class Length(Validator):
    """
    A validator that asserts the value's length is a specific value.
    """

    def __init__(self, value):
        self.value = value

    def __call__(self, value):
        if len(value) != self.value:
            raise ValidationError(
                'expected length {!r} but got length {!r} for value {!r}'.format(
                    self.value, len(value), value
                )
            )


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


__all__ = [name for name, obj in globals().items() if is_subclass(obj, Validator)]
