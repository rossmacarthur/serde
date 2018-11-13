"""
Validator functions for use with Fields.
"""

import validators

from .error import ValidationError


def instance(value, type):
    """
    Validate that the given value is an instance of a type.

    Args:
        value: the value to validate.
        type (type): the type to check for.

    Raises:
        ValidationError: when the value is not an instance of the type.
    """
    if not isinstance(value, type):
        raise ValidationError(
            'expected {!r} but got {!r}'
            .format(type.__name__, value.__class__.__name__)
        )


def between(value, min=None, max=None, units=''):
    """
    Validate that the given number is between a minimum and/or maximum.

    Args:
        value: the value to validate.
        min: the minimum value allowed.
        max: the maximum value allowed.

    Raises:
        ValidationError: when the value is not between the minimum and/or
            maximum.
    """
    if units:
        units = ' ' + units

    if min is not None and min == max:
        if value != min:
            raise ValidationError(
                'expected {0!r}{2} but got {1!r}{2}'
                .format(min, value, units)
            )
    else:
        if min is not None and value < min:
            raise ValidationError(
                'expected at least {0!r}{2} but got {1!r}{2}'
                .format(min, value, units)
            )

        if max is not None and value > max:
            raise ValidationError(
                'expected at most {0!r}{2} but got {1!r}{2}'
                .format(max, value, units)
            )


def contains(value, allowed):
    """
    Validate that the given list/range/tuple contains the given value.

    Args:
        value: the value to validate.
        allowed (list/range/tuple): the allowed values.

    Raises:
        ValidationError: when the value is not one of the allowed values.
    """
    if value not in allowed:
        raise ValidationError('{!r} is not a valid choice'.format(value))


def domain(value):
    """
    Validate whether or not the given string is a valid domain.
    """
    if not validators.domain(value):
        raise ValidationError('{!r} is not a valid domain'.format(value))


def email(value):
    """
    Validate whether or not the given string is a valid email.
    """
    if not validators.email(value):
        raise ValidationError('{!r} is not a valid email'.format(value))


def slug(value):
    """
    Validate whether or not the given string is a valid slug.
    """
    if not validators.slug(value):
        raise ValidationError('{!r} is not a valid slug'.format(value))


def url(value):
    """
    Validate whether or not the given string is a valid url.
    """
    if not validators.url(value):
        raise ValidationError('{!r} is not a valid url'.format(value))
