"""
Extended Field types for Serde Models.
"""

import uuid

import validators

from serde.error import ValidationError

from .core import Field, InstanceField, Str


class Choice(Field):
    """
    One of a given selection of values.

    This field checks if the input data is one of the allowed values. These
    values do not need to be the same type. This field is easily subclassed if
    extra serialization and deserialization is required.

    ..  doctest::

        >>> class Car(Model):
        ...     color = Choice(['black', 'blue', 'red'])
        >>> car = Car.from_dict({'color': 'blue'})
        >>> car.color
        'blue'
        >>> car.to_dict()
        OrderedDict([('color', 'blue')])
        >>> Car('yellow')
        Traceback (most recent call last):
        ...
        serde.error.ValidationError: 'yellow' is not a valid choice
    """

    def __init__(self, choices, **kwargs):
        """
        Create a new Choice.

        Args:
            choices: a list/range/tuple/iterable of allowed values.
            **kwargs: keyword arguments for the `Field` constructor.
        """
        super().__init__(**kwargs)
        self.choices = choices

    def validate(self, value):
        """
        Validate the given value according to this Field's specification.

        Args:
            value: the value to validate.
        """
        if value not in self.choices:
            raise ValidationError('{!r} is not a valid choice'.format(value))


class Domain(Str):
    """
    A domain field.

    This is a `Str` field that validates that the input string is a domain

    .. doctest::

        >>> class Service(Model):
        ...     domain = Domain()
        >>> service = Service.from_dict({'domain': 'www.github.com'})
        >>> service.domain
        'www.github.com'
        >>> service.to_dict()
        OrderedDict([('domain', 'www.github.com')])
        >>> Service('not a domain')
        Traceback (most recent call last):
        ...
        serde.error.ValidationError: 'not a domain' is not a valid domain
    """

    def validate(self, value):
        """
        Validate the given value according to this Field's specification.

        Args:
            value: the value to validate.
        """
        super().validate(value)

        if not validators.domain(value):
            raise ValidationError('{!r} is not a valid domain'.format(value))


class Email(Str):
    """
    An email field.

    This is a `Str` field that validates that the input string is a email.

    .. doctest::

        >>> class User(Model):
        ...     email = Email()
        >>> user = User.from_dict({'email': 'john@smith.com'})
        >>> user.email
        'john@smith.com'
        >>> user.to_dict()
        OrderedDict([('email', 'john@smith.com')])
        >>> User('not an email')
        Traceback (most recent call last):
        ...
        serde.error.ValidationError: 'not an email' is not a valid email
    """

    def validate(self, value):
        """
        Validate the given value according to this Field's specification.

        Args:
            value: the value to validate.
        """
        super().validate(value)

        if not validators.email(value):
            raise ValidationError('{!r} is not a valid email'.format(value))


class Slug(Str):
    """
    A slug field.

    This is a `Str` field that validates that the input string is a slug.

    .. doctest::

        >>> class Article(Model):
        ...     slug = Slug()
        >>> article = Article.from_dict({'slug': 'hello-world'})
        >>> article.slug
        'hello-world'
        >>> article.to_dict()
        OrderedDict([('slug', 'hello-world')])
        >>> Article('not a slug!')
        Traceback (most recent call last):
        ...
        serde.error.ValidationError: 'not a slug!' is not a valid slug
    """

    def validate(self, value):
        """
        Validate the given value according to this Field's specification.

        Args:
            value: the value to validate.
        """
        super().validate(value)

        if not validators.slug(value):
            raise ValidationError('{!r} is not a valid slug'.format(value))


class Url(Str):
    """
    A URL field.

    This is a `Str` field that validates that the input string is a URL.

    .. doctest::

        >>> class Service(Model):
        ...     url = Url()
        >>> service = Service.from_dict({'url': 'https://github.com/github'})
        >>> service.url
        'https://github.com/github'
        >>> service.to_dict()
        OrderedDict([('url', 'https://github.com/github')])
        >>> Service('not a url')
        Traceback (most recent call last):
        ...
        serde.error.ValidationError: 'not a url' is not a valid url
    """

    def validate(self, value):
        """
        Validate the given value according to this Field's specification.

        Args:
            value: the value to validate.
        """
        super().validate(value)

        if not validators.url(value):
            raise ValidationError('{!r} is not a valid url'.format(value))


class Uuid(InstanceField):
    """
    A `~uuid.UUID` field.

    This field validates that the input data is an instance of `~uuid.UUID`. It
    serializes the UUID as a string, and deserializes strings as UUIDs.

    .. doctest::

        >>> class User(Model):
        ...     key = Uuid()
        >>> user = User.from_dict({'key': '6af21dcd-e479-4af6-a708-0cbc8e2438c1'})
        >>> user.key
        UUID('6af21dcd-e479-4af6-a708-0cbc8e2438c1')
        >>> user.to_dict()
        OrderedDict([('key', '6af21dcd-e479-4af6-a708-0cbc8e2438c1')])
        >>> User('not a uuid')
        Traceback (most recent call last):
        ...
        serde.error.ValidationError: expected 'UUID' but got 'str'
    """

    def __init__(self, **kwargs):
        """
        Create a new Uuid.

        Args:
            **kwargs: keyword arguments for the `InstanceField` constructor.
        """
        super().__init__(uuid.UUID, **kwargs)

    def serialize(self, value):
        """
        Serialize the given value.

        Args:
            value (~uuid.UUID): the UUID to serialize.

        Returns:
            str: a string representation of the Uuid.
        """
        return str(value)

    def deserialize(self, value):
        """
        Deserialize the given value.

        Args:
            value (str): the value to deserialize.

        Returns:
            ~uuid.UUID: the deserialized Uuid.
        """
        return uuid.UUID(value)
