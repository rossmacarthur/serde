"""
This module contains validators for use with `Fields <serde.fields.Field>`.
"""

import re
from functools import wraps

from serde.exceptions import ValidationError
from serde.utils import try_import_all


__all__ = [
    'between',
    'contains',
    'equal',
    'instance',
    'length',
    'length_between',
    'length_max',
    'length_min',
    'max',
    'min',
    'regex'
]


def instance(type):
    """
    Returns a validator that asserts the value is an instance of a type.
    """
    @wraps(instance)
    def validator(value):
        if not isinstance(value, type):
            raise ValidationError(
                'expected {!r} but got {!r}'
                .format(type.__name__, value.__class__.__name__)
            )

    return validator


def equal(to):
    """
    Returns a validator that asserts the value is equal to the specified one.
    """
    @wraps(equal)
    def validator(value):
        if value != to:
            raise ValidationError(
                'expected {!r} but got {!r}'
                .format(to, value)
            )

    return validator


def min(endpoint, inclusive=True):
    """
    Returns a validator that asserts the value is greater than a minimum.

    Args:
        inclusive (bool): if this is set to `False` then the endpoint value will
            not be considered valid.
    """
    @wraps(min)
    def validator(value):
        if inclusive:
            if value < endpoint:
                raise ValidationError(
                    'expected at least {!r} but got {!r}'
                    .format(endpoint, value)
                )
        else:
            if value <= endpoint:
                raise ValidationError(
                    'expected more than {!r} but got {!r}'
                    .format(endpoint, value)
                )

    return validator


def max(endpoint, inclusive=True):
    """
    Returns a validator that asserts the value is less than a maximum.

    Args:
        inclusive (bool): if this is set to `False` then the endpoint value will
            not be considered valid.
    """
    @wraps(max)
    def validator(value):
        if inclusive:
            if value > endpoint:
                raise ValidationError(
                    'expected at most {!r} but got {!r}'
                    .format(endpoint, value)
                )
        else:
            if value >= endpoint:
                raise ValidationError(
                    'expected less than {!r} but got {!r}'
                    .format(endpoint, value)
                )

    return validator


def between(min_endpoint, max_endpoint, inclusive=True):
    """
    Returns a validator that asserts the value is between two endpoints.

    Args:
        inclusive (bool): if this is set to `False` then the endpoint values
            will not be considered valid.
    """
    min_validator = min(min_endpoint, inclusive=inclusive)
    max_validator = max(max_endpoint, inclusive=inclusive)

    @wraps(between)
    def validator(value):
        min_validator(value)
        max_validator(value)

    return validator


def length(equal_to):
    """
    Returns a validator that asserts the value's length is a specific value.
    """
    equal_validator = equal(equal_to)

    @wraps(length)
    def validator(value):
        equal_validator(len(value))

    return validator


def length_min(endpoint, inclusive=True):
    """
    Returns a validator that asserts the value's length is greater than a min.

    Args:
        inclusive (bool): if this is set to `False` then the endpoint value will
            not be considered valid.
    """
    min_validator = min(endpoint, inclusive=inclusive)

    @wraps(length_min)
    def validator(value):
        min_validator(len(value))

    return validator


def length_max(endpoint, inclusive=True):
    """
    Returns a validator that asserts the value's length is less than a max.

    Args:
        inclusive (bool): if this is set to `False` then the endpoint value will
            not be considered valid.
    """
    max_validator = max(endpoint, inclusive=inclusive)

    @wraps(length_max)
    def validator(value):
        max_validator(len(value))

    return validator


def length_between(min_endpoint, max_endpoint, inclusive=True):
    """
    Returns a validator that asserts the value's length is between two values.

    Args:
        inclusive (bool): if this is set to `False` then the endpoint values
            will not be considered valid.
    """
    min_validator = min(min_endpoint, inclusive=inclusive)
    max_validator = max(max_endpoint, inclusive=inclusive)

    @wraps(length_between)
    def validator(value):
        length = len(value)
        min_validator(length)
        max_validator(length)

    return validator


def contains(allowed):
    """
    Returns validator that asserts the list/range/tuple contains a value.
    """
    @wraps(contains)
    def validator(value):
        if value not in allowed:
            raise ValidationError('{!r} is not a valid choice'.format(value))

    return validator


def regex(pattern, flags=0):
    """
    Returns validator that asserts a string matches a regex.

    Args:
        pattern (str): the regex pattern that the value must match.
        flags (int): the regex flags passed directly to `re.compile`.
    """
    compiled = re.compile(pattern, flags=flags)

    @wraps(regex)
    def validator(value):
        if not compiled.match(value):
            raise ValidationError(
                '{!r} does not match regex {!r}'
                .format(value, pattern)
            )

    return validator


try_import_all('serde_ext.validate', globals())
