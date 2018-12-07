"""
Validator functions for use with `Fields <serde.field.Field>`.
"""

import validators

from serde.error import ValidationError


__all__ = [
    'between',
    'contains',
    'domain',
    'email',
    'instance',
    'ip_address',
    'ipv4_address',
    'ipv6_address',
    'mac_address',
    'max',
    'min',
    'slug',
    'url'
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
            ValidationError: when the value is not an instance of the type.
        """
        if not isinstance(value, type):
            raise ValidationError(
                'expected {!r} but got {!r}'
                .format(type.__name__, value.__class__.__name__)
            )

    return instance_


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

        ValidationError: when the value is greater than and/or equal to the
                maximum.
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
            ValidationError: when the value is not less than and/or equal to the
                maximum.
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
            ValidationError: when the value is not between the minimum and
                maximum.
        """
        min(min_endpoint, inclusive=inclusive)(value)
        max(max_endpoint, inclusive=inclusive)(value)

    return between_


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
            ValidationError: when the value is not one of the allowed values.
        """
        if value not in allowed:
            raise ValidationError('{!r} is not a valid choice'.format(value))

    return contains_


def domain(value):
    """
    Validate whether or not the given string is a valid domain.

    Args:
        value (str): the value to validate.

    Raises:
        ValidationError: when the value is not a valid domain.
    """
    if not validators.domain(value):
        raise ValidationError('{!r} is not a valid domain'.format(value))


def email(value):
    """
    Validate whether or not the given string is a valid email.

    Args:
        value (str): the value to validate.

    Raises:
        ValidationError: when the value is not a valid email.
    """
    if not validators.email(value):
        raise ValidationError('{!r} is not a valid email'.format(value))


def ip_address(value):
    """
    Validate whether or not the given string is a valid IP address.

    Args:
        value (str): the value to validate.

    Raises:
        ValidationError: when the value is not a valid IP address.
    """
    if not validators.ipv4(value) and not validators.ipv6(value):
        raise ValidationError('{!r} is not a valid IP address'.format(value))


def ipv4_address(value):
    """
    Validate whether or not the given string is a valid IP version 4 address.

    Args:
        value (str): the value to validate.

    Raises:
        ValidationError: when the value is not a valid IP version 4 address.
    """
    if not validators.ipv4(value):
        raise ValidationError('{!r} is not a valid IPv4 address'.format(value))


def ipv6_address(value):
    """
    Validate whether or not the given string is a valid IP version 6 address.

    Args:
        value (str): the value to validate.

    Raises:
        ValidationError: when the value is not a valid IP version 6 address.
    """
    if not validators.ipv6(value):
        raise ValidationError('{!r} is not a valid IPv6 address'.format(value))


def mac_address(value):
    """
    Validate whether or not the given string is a valid MAC address.

    Args:
        value (str): the value to validate.

    Raises:
        ValidationError: when the value is not a valid MAC address.
    """
    if not validators.mac_address(value):
        raise ValidationError('{!r} is not a valid MAC address'.format(value))


def slug(value):
    """
    Validate whether or not the given string is a valid slug.

    Args:
        value (str): the value to validate.

    Raises:
        ValidationError: when the value is not a valid slug.
    """
    if not validators.slug(value):
        raise ValidationError('{!r} is not a valid slug'.format(value))


def url(value):
    """
    Validate whether or not the given string is a valid URL.

    Args:
        value (str): the value to validate.

    Raises:
        ValidationError: when the value is not a valid URL.
    """
    if not validators.url(value):
        raise ValidationError('{!r} is not a valid URL'.format(value))
