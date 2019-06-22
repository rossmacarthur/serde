"""
This module contains validators for use with `Fields <serde.fields.Field>`.
"""

import re

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
    'min'
]


def instance(type):
    """
    Validate that the given value is an instance of a type.

    Args:
        type (type): the type to check for.

    Returns:
        function: the validator function.
    """
    def instance_(value):
        """
        Validate that the given value is an instance of a type.

        Args:
            value: the value to validate.

        Raises:
            `~serde.exceptions.ValidationError`: when the value is not an
                instance of the type.
        """
        if not isinstance(value, type):
            raise ValidationError(
                'expected {!r} but got {!r}'
                .format(type.__name__, value.__class__.__name__)
            )

    return instance_


def equal(to):
    """
    Validate that a value is equal to something.

    Args:
        to: the value to check against.

    Returns:
        function: the validator function.
    """
    def equal_(value):
        """
        Validate that the given value is equal to the specified value.

        Args:
            value: the value to validate.

        Raises:
            `~serde.exceptions.ValidationError`: when the value is not equal to
                the expected value.
        """
        if value != to:
            raise ValidationError(
                'expected {!r} but got {!r}'
                .format(to, value)
            )

    return equal_


def min(endpoint, inclusive=True):
    """
    Validate that a value is greater than and/or equal to the given endpoint.

    Args:
        endpoint: the minimum value allowed.
        inclusive (bool): whether the minimum value is allowed.

    Returns:
        function: the validator function.
    """
    def min_(value):
        """
        Validate that the given value is greater than and/or equal to a minimum.

        Args:
            value: the value to validate.

        Raises:
            `~serde.exceptions.ValidationError`: when the value is greater than
                and/or equal to the maximum.
        """
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

    return min_


def max(endpoint, inclusive=True):
    """
    Validate that a value is less than and/or equal to the given endpoint.

    Args:
        endpoint: the maximum value allowed.
        inclusive (bool): whether the maximum value is allowed.

    Returns:
        function: the validator function.
    """
    def max_(value):
        """
        Validate that the given value is less than and/or equal to the maximum.

        Args:
            value: the value to validate.

        Raises:
            `~serde.exceptions.ValidationError`: when the value is not less than
                and/or equal to the maximum.
        """
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

    return max_


def between(min_endpoint, max_endpoint, inclusive=True):
    """
    Validate that the given number is between a minimum and maximum.

    Args:
        min_endpoint: the minimum value allowed.
        max_endpoint: the maximum value allowed.
        inclusive (bool): whether the endpoint values are allowed.

    Returns:
        function: the validator function.
    """
    def between_(value):
        """
        Validate that the given number is between a minimum and maximum.

        Args:
            value: the value to validate.

        Raises:
            `~serde.exceptions.ValidationError`: when the value is not between
                the minimum and maximum.
        """
        min(min_endpoint, inclusive=inclusive)(value)
        max(max_endpoint, inclusive=inclusive)(value)

    return between_


def length(length):
    """
    Validate that the given value has a particular length.

    Args:
        length (int): the length allowed.

    Returns:
        function: the validator function.
    """
    def length_(value):
        """
        Validate that the given value has the expected length.

        Args:
            value: the value to validate.

        Raises:
            `~serde.exceptions.ValidationError`: when the value does not have
                the expected length.
        """
        equal(length)(len(value))

    return length_


def length_min(endpoint, inclusive=True):
    """
    Validate that a value's length is greater than/or equal to a minimum.

    Args:
        endpoint: the minimum length allowed.
        inclusive (bool): whether the minimum length value itself allowed.

    Returns:
        function: the validator function.
    """
    def length_min_(value):
        """
        Validate that a value's length is greater than/or equal to a minimum.

        Args:
            value: the value to validate.

        Raises:
            `~serde.exceptions.ValidationError`: when the value's length is
                greater than and/or equal to the maximum.
        """
        min(endpoint, inclusive=inclusive)(len(value))

    return length_min_


def length_max(endpoint, inclusive=True):
    """
    Validate that a value's length is less than/or equal to a maximum.

    Args:
        endpoint: the maximum length allowed.
        inclusive (bool): whether the maximum length value itself allowed.

    Returns:
        function: the validator function.
    """
    def length_max_(value):
        """
        Validate that a value's length is less than/or equal to a maximum.

        Args:
            value: the value to validate.

        Raises:
            `~serde.exceptions.ValidationError`: when the value's length is
                less than and/or equal to the maximum.
        """
        max(endpoint, inclusive=inclusive)(len(value))

    return length_max_


def length_between(min_endpoint, max_endpoint, inclusive=True):
    """
    Validate that the given value's length is between a minimum and maximum.

    Args:
        min_endpoint: the minimum length allowed.
        max_endpoint: the maximum length allowed.
        inclusive (bool): whether the endpoint length values are allowed.

    Returns:
        function: the validator function.
    """
    def length_between_(value):
        """
        Validate that the given value's length is between a minimum and maximum.

        Args:
            value: the value to validate.

        Raises:
            `~serde.exceptions.ValidationError`: when the value's length is not
                between the minimum and maximum.
        """
        min(min_endpoint, inclusive=inclusive)(len(value))
        max(max_endpoint, inclusive=inclusive)(len(value))

    return length_between_


def contains(allowed):
    """
    Validate that the given list/range/tuple contains the given value.

    Args:
        allowed (list/range/tuple): the allowed values.

    Returns:
        function: the validator function.
    """
    def contains_(value):
        """
        Validate that the given list/range/tuple contains the given value.

        Raises:
            `~serde.exceptions.ValidationError`: when the value is not one of
                the allowed values.
        """
        if value not in allowed:
            raise ValidationError('{!r} is not a valid choice'.format(value))

    return contains_


def regex(pattern, flags=0):
    """
    Validate that the given string matches the given regex.

    Args:
        pattern (str): the regex string to match with.
        flags (int): regex flags passed directly to `re.compile`.

    Returns:
        function: the validator function.
    """
    compiled = re.compile(pattern, flags=flags)

    def regex_(value):
        """
        Validate that the given string matches the regex.

        Raises:
            `serde.exceptions.ValidationError`: when the value does not match
                the regex.
        """
        if not compiled.match(value):
            raise ValidationError('{!r} does not match regex {!r}'.format(value, pattern))

    return regex_


try_import_all('serde_ext.validate', globals())
