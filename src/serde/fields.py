"""
This module contains Field classes for `Models <serde.model.Model>`.

`Fields <serde.fields.Field>` do the work of serializing, deserializing,
normalizing, and validating the input values. Fields are always assigned to a
`~serde.model.Model` as *instances*. And although it is easy enough to subclass
`Field`, they support extra serialization, deserialization, normalization, and
validation of values without having to subclass `Field`.

In the following example we define an ``Album`` class. The ``title`` field is
of type `str`, and we apply the `str.strip` normalizer to automatically strip
the input value when instantiating or deserializing the ``Album``. The
``released`` field is of type `datetime.date` and we apply an extra validator to
only accept dates after 15th April 1912. Note: the ``rename`` argument only
applies to the serializing and deserializing of the data, the ``Album`` class
would still be instantiated using ``Album(released=...)``.

::

    >>> from serde import Model, fields, validate

    >>> class Album(Model):
    ...     title = fields.Str(normalizers=[str.strip])
    ...     released = fields.Date(
    ...         rename='release_date',
    ...         validators=[validate.min(datetime.date(1912, 4, 15))]
    ...     )

Additionally, the `create()` method can be used to generate a new `Field` class
from arbitrary functions without having to manually subclass a `Field`. For
example if we wanted a ``Percent`` field we would do the following.

::

    >>> Percent = fields.create(
    ...     'Percent',
    ...     Float,
    ...     validators=[validate.between(0.0, 100.0)]
    ... )

    >>> issubclass(Percent, Float)
    True

If these methods of creating custom `Field` classes are not satisfactory, you
can always subclass a `Field` and override the relevant methods.

::

    >>> class Percent(Float):
    ...     def validate(self, value):
    ...         super(Percent, self).validate(value)
    ...         validate.between(0.0, 100.0)

"""

import datetime
import uuid
from functools import wraps
from itertools import chain

import isodate
from six import integer_types

from serde import validate
from serde.exceptions import (
    ContextError,
    DeserializationError,
    NormalizationError,
    SerializationError,
    ValidationError,
    map_errors
)
from serde.utils import applied, chained, try_import_all, zip_equal


__all__ = [
    'BaseField',
    'Bool',
    'Bytes',
    'Choice',
    'Complex',
    'Constant',
    'Date',
    'DateTime',
    'Dict',
    'Field',
    'Float',
    'Instance',
    'Int',
    'List',
    'Nested',
    'Optional',
    'Str',
    'Time',
    'Tuple',
    'Uuid',
    'create'
]


def _resolve_to_field_instance(thing, none_allowed=True):
    """
    Resolve an arbitrary object to a `Field` instance.

    Args:
        thing: anything to resolve to a Field instance.
        none_allowed (bool): if set then a thing of None will be resolved to a
            generic Field.

    Returns:
        Field: a field instance.
    """
    # We import Model here to avoid circular dependency problems.
    from serde.model import Model

    # If the thing is None then return a generic Field instance.
    if none_allowed and thing is None:
        return Field()

    # If the thing is a Field instance then thats great.
    elif isinstance(thing, Field):
        return thing

    # If the thing is a subclass of Field then attempt to create an instance.
    # This could fail the Field expects positional arguments.
    try:
        if issubclass(thing, Field):
            return thing()
    except TypeError:
        pass

    # If the thing is a subclass of Model then create a Nested instance.
    try:
        if issubclass(thing, Model):
            return Nested(thing)
    except TypeError:
        pass

    # If the thing is a built-in type that we support then create an Instance
    # with that type.
    field_class = FIELD_CLASS_MAP.get(thing, None)

    if field_class is not None:
        return field_class()

    raise TypeError(
        '{!r} is not a Field, a Model class, an instance of a Field, or a supported built-in type'
        .format(thing)
    )


class BaseField(object):
    """
    A base field or tag on a `~serde.model.Model`.

    Fields and tags handle serializing and deserializing of input values for
    Models. This class serves as a base class for both Fields and Tags.
    """

    # This is so we can get the order the bases were instantiated in.
    _counter = 1

    def __init__(self, serializers=None, deserializers=None):
        """
        Create a new BaseField.

        Args:
            serializers (list): a list of serializer functions taking the value
                to serialize as an argument. The functions need to raise an
                `Exception` if they fail. These serializer functions will be
                applied before the primary serializer on this BaseField.
            deserializers (list): a list of deserializer functions taking the
                value to deserialize as an argument. The functions need to raise
                an `Exception` if they fail. These deserializer functions will
                be applied after the primary deserializer on this BaseField.
        """
        self.id = Field._counter
        Field._counter += 1
        self.serializers = serializers or []
        self.deserializers = deserializers or []

    def __eq__(self, other):
        """
        Whether two BaseFields are the same.
        """
        return isinstance(other, self.__class__) and self._attrs() == other._attrs()

    @property
    def __model__(self):
        """
        The Model class that the BaseField is bound to.
        """
        return self._model_cls

    def _attrs(self):
        """
        Return all attributes of BaseField except 'id' and some private attributes.
        """
        return {
            name: value for name, value in vars(self).items()
            if name not in ('id', '_model_cls')
        }

    def _bind(self, model_cls):
        """
        Bind the BaseField to a Model.
        """
        if hasattr(self, '_model_cls'):
            raise ContextError(
                '{name!r} instance used multiple times'
                .format(name=self.__class__.__name__),
            )

        self._model_cls = model_cls

    def _serialize_with(self, model, d):
        """
        Serialize value(s) from a Model instance to a dictionary.

        This method should use `self._serialize()` on individual values. This
        method needs to be overridden.

        Args:
            model (Model): the Model instance that we are serializing from.
            d (dict): the dictionary to serialize to.

        Returns:
            dict: the updated dictionary to continue serializing to.
        """
        raise NotImplementedError('this method should be overridden')

    def _deserialize_with(self, model, d):
        """
        Deserialize value(s) from a dictionary to a Model instance.

        This method should use `self._deserialize()` on individual values. This
        method needs to be overridden.

        Args:
            model (Model): the Model instance that we are deserializing to.
            d (dict): the dictionary to deserialize from.

        Returns:
            (model, dict): the updated Model instance to continue deserializing
                to and the updated dictionary to continue deserializing from.
        """
        raise NotImplementedError('this method should be overridden')

    def _serialize(self, value):
        return chained(chain(self.serializers, [self.serialize]), value)

    def _deserialize(self, value):
        return chained(chain([self.deserialize], self.deserializers), value)

    def serialize(self, value):
        """
        Serialize the given value according to this BaseField's specification.
        """
        return value

    def deserialize(self, value):
        """
        Deserialize the given value according to this BaseField's specification.
        """
        return value


class Field(BaseField):
    """
    A field on a `~serde.model.Model`.

    Fields handle serializing, deserializing, normalization, and validation of
    input values for Model objects.
    """

    def __init__(
        self,
        rename=None,
        serializers=None,
        deserializers=None,
        normalizers=None,
        validators=None
    ):
        """
        Create a new Field.

        Args:
            rename (str): override the name for the field when serializing and
                expect this name when deserializing.
            serializers (list): a list of serializer functions taking the value
                to serialize as an argument. The functions need to raise an
                `Exception` if they fail. These serializer functions will be
                applied before the primary serializer on this Field.
            deserializers (list): a list of deserializer functions taking the
                value to deserialize as an argument. The functions need to raise
                an `Exception` if they fail. These deserializer functions will
                be applied after the primary deserializer on this Field.
            normalizers (list): a list of normalizer functions taking the value
                to normalize as an argument. The functions need to raise an
                `Exception` if they fail. These normalizer functions will be
                applied after the primary normalizer on this Field.
            validators (list): a list of validator functions taking the value
                to validate as an argument. The functions need to raise an
                `Exception` if they fail.
        """
        super(Field, self).__init__(serializers=serializers, deserializers=deserializers)
        self.rename = rename
        self.normalizers = normalizers or []
        self.validators = validators or []

    def _attrs(self):
        """
        Return all attributes of Base except 'id' and some private attributes.
        """
        return {
            name: value for name, value in vars(self).items()
            if name not in ('id', '_model_cls', '_attr_name', '_serde_name')
        }

    def _bind(self, model_cls, name):
        """
        Bind the Field to a Model.
        """
        super(Field, self)._bind(model_cls)
        self._attr_name = name
        self._serde_name = self.rename if self.rename else name

    def _serialize_with(self, model, d):
        """
        Serialize the Model's attribute to a dictionary.
        """
        try:
            value = getattr(model, self._attr_name)
        except AttributeError:
            raise SerializationError(
                'expected attribute {!r}'.format(self._attr_name),
                field=self,
                model_cls=model.__class__
            )

        with map_errors(SerializationError, value=value, field=self, model_cls=model.__class__):
            d[self._serde_name] = self._serialize(value)

        return d

    def _deserialize_with(self, model, d):
        """
        Deserialize the Model's attribute from a dictionary.
        """
        try:
            value = d[self._serde_name]
        except KeyError:
            raise DeserializationError(
                'expected field {!r}'.format(self._serde_name),
                field=self,
                model_cls=model.__class__
            )

        with map_errors(DeserializationError, value=value, field=self, model_cls=model.__class__):
            setattr(model, self._attr_name, self._deserialize(value))

        return model, d

    def _normalize_with(self, model):
        """
        Normalize the Model's attribute according to this Field's specification.
        """
        try:
            value = getattr(model, self._attr_name)
        except AttributeError:
            raise NormalizationError(
                'expected attribute {!r}'.format(self._attr_name),
                field=self,
                model_cls=model.__class__
            )

        with map_errors(NormalizationError, value=value, field=self, model_cls=model.__class__):
            setattr(model, self._attr_name, self._normalize(value))

    def _validate_with(self, model):
        """
        Validate the Model's attribute according to this Field's specification.
        """
        try:
            value = getattr(model, self._attr_name)
        except AttributeError:
            raise ValidationError(
                'expected attribute {!r}'.format(self._attr_name),
                field=self,
                model_cls=model.__class__
            )

        with map_errors(ValidationError, value=value, field=self, model_cls=model.__class__):
            self._validate(value)

    def _normalize(self, value):
        return chained(chain([self.normalize], self.normalizers), value)

    def _validate(self, value):
        applied(chain([self.validate], self.validators), value)

    def normalize(self, value):
        """
        Normalize the given value according to this Field's specification.
        """
        return value

    def validate(self, value):
        """
        Validate the given value according to this Field's specification.
        """
        pass


def _create_serialize(cls, serializers):
    """
    Create a new serialize method with extra serializer functions.
    """
    @wraps(serializers[0])
    def serialize(self, value):
        return chained(chain(serializers, [super(cls, self).serialize]), value)
    return serialize


def _create_deserialize(cls, deserializers):
    """
    Create a new deserialize method with extra deserializer functions.
    """
    @wraps(deserializers[0])
    def deserialize(self, value):
        return chained(chain([super(cls, self).deserialize], deserializers), value)
    return deserialize


def _create_normalize(cls, normalizers):
    """
    Create a new normalize method with extra normalizer functions.
    """
    @wraps(normalizers[0])
    def normalize(self, value):
        return chained(chain([super(cls, self).normalize], normalizers), value)
    return normalize


def _create_validate(cls, validators):
    """
    Create a new validate method with extra validator functions.
    """
    @wraps(validators[0])
    def validate(self, value):
        applied(chain([super(cls, self).validate], validators), value)
    return validate


def create(
    name,
    base=None,
    args=None,
    serializers=None,
    deserializers=None,
    normalizers=None,
    validators=None
):
    """
    Create a new Field class.

    This is a convenience method for creating new Field classes from arbitrary
    serializer, deserializer, normalizer, and/or validator functions.

    Args:
        name (str): the name of the class.
        base (Field): the base Field class to subclass.
        args (tuple): positional arguments for the base class __init__ method.
        serializers (list): a list of serializer functions taking the value to
            serialize as an argument. The functions need to raise an `Exception`
            if they fail. These serializer functions will be applied before the
            primary serializer on this Field.
        deserializers (list): a list of deserializer functions taking the value
            to deserialize as an argument. The functions need to raise an
            `Exception` if they fail. These deserializer functions will be
            applied after the primary deserializer on this Field.
        normalizers (list): a list of normalizer functions taking the value to
            normalize as an argument. The functions need to raise an `Exception`
            if they fail. These normalizer functions will be applied after the
            primary normalizer on this Field.
        validators (list): a list of validator functions taking the value to
            validate as an argument. The functions need to raise an `Exception`
            if they fail.

    Returns:
        class: a new Field class.
    """
    if not base:
        base = Field

    field_cls = type(name, (base,), {})

    if args:
        def __init__(self, **kwargs):  # noqa: N807
            super(field_cls, self).__init__(*args, **kwargs)

        __init__.__doc__ = """\
Create a new {name}.

Args:
    **kwargs: keyword arguments for the `{base}` constructor.
""".format(name=name, base=base.__name__)
        field_cls.__init__ = __init__

    if serializers:
        field_cls.serialize = _create_serialize(field_cls, serializers)

    if deserializers:
        field_cls.deserialize = _create_deserialize(field_cls, deserializers)

    if normalizers:
        field_cls.normalize = _create_normalize(field_cls, normalizers)

    if validators:
        field_cls.validate = _create_validate(field_cls, validators)

    return field_cls


class Optional(Field):
    """
    An optional `Field`.

    An Optional is a field that is allowed to be None. Serialization,
    deserialization, and validation using the wrapped Field will only be called
    if the value is not None. The wrapped Field can be specified using a Field
    class, a Field instance, a Model class, or a built-in type that has a
    corresponding Field type in this library.

    ::

        >>> class Quote(Model):
        ...     author = Optional(str)
        ...     year = Optional(int, default=2004)
        ...     content = Str()

        >>> quote = Quote(year=2000, content='Beautiful is better than ugly.')
        >>> assert quote.author is None
        >>> quote.year
        2000
        >>> quote.content
        'Beautiful is better than ugly.'

        >>> assert quote.to_dict() == {
        ...     'content': 'Beautiful is better than ugly.',
        ...     'year': 2000
        ... }

        >>> quote = Quote.from_dict({
        ...     'author': 'Tim Peters',
        ...     'content': 'Now is better than never',
        ... })
        >>> quote.author
        'Tim Peters'
        >>> quote.year
        2004
        >>> quote.content
        'Now is better than never'
    """

    def __init__(self, inner=None, default=None, **kwargs):
        """
        Create a new Optional.

        Args:
            inner: the the Field class/instance that this Optional wraps.
            default: a value to use if there is no input field value or the
                input value is None. This can also be a callable that generates
                the default. The callable must take no positional arguments.
            **kwargs: keyword arguments for the `Field` constructor.
        """
        super(Optional, self).__init__(**kwargs)
        self.inner = _resolve_to_field_instance(inner)
        self.default = default

    def _serialize_with(self, model, d):
        """
        Serialize value(s) from a Model instance to a dictionary.
        """
        try:
            value = getattr(model, self._attr_name)
        except AttributeError:
            raise SerializationError(
                'expected attribute {!r}'.format(self._attr_name),
                field=self,
                model_cls=model.__class__
            )

        if value is not None:
            with map_errors(SerializationError, value=value, field=self, model_cls=model.__class__):
                d[self._serde_name] = self._serialize(value)

        return d

    def _deserialize_with(self, model, d):
        """
        Deserialize value(s) from a dictionary to a Model instance.
        """
        try:
            value = d[self._serde_name]
        except KeyError:
            return model, d

        with map_errors(DeserializationError, value=value, field=self, model_cls=model.__class__):
            setattr(model, self._attr_name, self._deserialize(value))

        return model, d

    def _normalize_with(self, model):
        """
        Normalize value(s) according to this Field's specification.
        """
        value = getattr(model, self._attr_name, None)

        if value is not None:
            with map_errors(NormalizationError, value=value, field=self, model_cls=model.__class__):
                value = self._normalize(value)
        elif self.default is not None:
            if callable(self.default):
                value = self.default()
            else:
                value = self.default

        setattr(model, self._attr_name, value)

        return model

    def _validate_with(self, model):
        """
        Validate value(s) according to this Field's specification.
        """
        try:
            value = getattr(model, self._attr_name)
        except AttributeError:
            raise ValidationError(
                'expected attribute {!r}'.format(self._attr_name),
                field=self,
                model_cls=model.__class__
            )

        if value is not None:
            with map_errors(ValidationError, value=value, field=self, model_cls=model.__class__):
                self._validate(value)

    def serialize(self, value):
        """
        Serialize the given value using the inner Field.
        """
        return self.inner._serialize(value)

    def deserialize(self, value):
        """
        Deserialize the given value using the inner Field.
        """
        return self.inner._deserialize(value)

    def normalize(self, value):
        """
        Normalize the given value using the inner Field.
        """
        return self.inner._normalize(value)

    def validate(self, value):
        """
        Validate the given value using the inner Field.
        """
        self.inner._validate(value)


class Instance(Field):
    """
    A `Field` that is an instance of the given type.
    """

    def __init__(self, type, **kwargs):
        """
        Create a new Instance.

        Args:
            type: the type that this Field wraps.
            **kwargs: keyword arguments for the `Field` constructor.
        """
        super(Instance, self).__init__(**kwargs)
        self.type = type

    def validate(self, value):
        """
        Validate the given value is an instance of the specified type.
        """
        super(Instance, self).validate(value)
        validate.instance(self.type)(value)


class Nested(Instance):
    """
    A `Field` for `~serde.model.Model` fields.

    This is wrapper Field for Models to support sub-Models. The serialize and
    deserialize methods call the `~serde.model.Model.to_dict()` and
    `~serde.model.Model.from_dict()`  methods on the Model class. This allows
    complex nested Models.

    ::

        >>> class Birthday(Model):
        ...     day = Int(validators=[validate.between(1, 31)])
        ...     month = Str()

        >>> class Person(Model):
        ...     name = Str()
        ...     birthday = Nested(Birthday)

        >>> person = Person('Beyonce', birthday=Birthday(4, 'September'))
        >>> person.name
        'Beyonce'
        >>> person.birthday.day
        4
        >>> person.birthday.month
        'September'

        >>> assert person.to_dict() == {
        ...     'name': 'Beyonce',
        ...     'birthday': {
        ...         'day': 4,
        ...         'month': 'September'
        ...     }
        ... }

        >>> person = Person.from_dict({
        ...     'name': 'Beyonce',
        ...     'birthday': {
        ...         'day': 4,
        ...         'month': 'September'
        ...     }
        ... })
        >>> person.name
        'Beyonce'
        >>> person.birthday.day
        4
        >>> person.birthday.month
        'September'
    """

    def serialize(self, model):
        """
        Serialize the given `~serde.model.Model` instance as a dictionary.
        """
        return model.to_dict()

    def deserialize(self, d):
        """
        Deserialize the given dictionary to a `~serde.model.Model` instance.
        """
        return self.type.from_dict(d)


class Constant(Field):
    """
    A constant Field.

    A Constant is a Field that always has to be the given value. It does not
    have to be given, but if it is present it must be equal to the given value.
    """

    def __init__(self, value, **kwargs):
        """
        Create a new Constant.

        Args:
            value: the constant value that this Constant wraps.
            **kwargs: keyword arguments for the `Field` constructor.
        """
        super(Constant, self).__init__(**kwargs)
        self.value = value

    def normalize(self, value):
        """
        Normalize the given value.

        If the value is None then it will normalized to the constant value.
        Otherwise, the given value is returned.
        """
        if value is None:
            value = self.value

        return value

    def validate(self, value):
        """
        Validate that the given value is equal to the constant value.
        """
        validate.equal(self.value)(value)


class Dict(Instance):
    """
    A dictionary Field with a required key and value type.

    This field represents the built-in `dict` type. Each key and value will be
    serialized, deserialized, normalized, and validated with the specified key
    and value types. The key and value types can be specified using Field
    classes, Field instances, Model classes, or built-in types that have a
    corresponding Field type in this library.

    Consider an example model with a constants attribute which is map of strings
    to floats.

    ::

        >>> class Example(Model):
        ...     constants = Dict(str, float)

        >>> example = Example({'pi': 3.1415927, 'e': 2.7182818})
        >>> example.constants['pi']
        3.1415927
        >>> example.constants['e']
        2.7182818

        >>> d = example.to_dict()
        >>> d['constants']['pi']
        3.1415927
        >>> d['constants']['e']
        2.7182818

        >>> Example({'pi': '3.1415927'})
        Traceback (most recent call last):
            ...
        serde.exceptions.InstantiationError: expected 'float' but got 'str'

        >>> Example.from_dict({'constants': {100: 3.1415927}})
        Traceback (most recent call last):
            ...
        serde.exceptions.DeserializationError: expected 'str' but got 'int'
    """

    def __init__(self, key=None, value=None, **kwargs):
        """
        Create a new Dict.

        Args:
            key (Field): the Field class/instance for keys in this Dict.
            value (Field): the Field class/instance for values in this Dict.
            **kwargs: keyword arguments for the `Field` constructor.
        """
        super(Dict, self).__init__(dict, **kwargs)
        self.key = _resolve_to_field_instance(key)
        self.value = _resolve_to_field_instance(value)

    def serialize(self, value):
        """
        Serialize the given dictionary.

        Each key and value in the dictionary will be serialized with the
        specified key and value Field instances.
        """
        return {self.key._serialize(k): self.value._serialize(v) for k, v in value.items()}

    def deserialize(self, value):
        """
        Deserialize the given dictionary.

        Each key and value in the dictionary will be deserialized with the
        specified key and value Field instances.
        """
        return {self.key._deserialize(k): self.value._deserialize(v) for k, v in value.items()}

    def normalize(self, value):
        """
        Normalize the given dictionary.

        Each key and value in the dictionary will be normalized with the
        specified key and value Field instances.
        """
        return {self.key._normalize(k): self.value._normalize(v) for k, v in value.items()}

    def validate(self, value):
        """
        Validate the given dictionary.

        Each key and value in the dictionary will be validated with the
        specified key and value Field instances.
        """
        super(Dict, self).validate(value)

        for k, v in value.items():
            self.key._validate(k)
            self.value._validate(v)


class List(Instance):
    """
    A list Field with a required element type.

    This field represents the built-in `list` type. Each element will be
    serialized, deserialized, normalized and validated with the specified
    element type. The element type can be specified using Field classes, Field
    instances, Model classes, or built-in types that have a corresponding Field
    type in this library.

    Consider a user model that can have multiple emails

    ::

        >>> class User(Model):
        ...     emails = List(str)

        >>> user = User(['john@smith.com', 'john.smith@email.com'])
        >>> user.emails[0]
        'john@smith.com'
        >>> user.emails[1]
        'john.smith@email.com'

        >>> User(emails=1234)
        Traceback (most recent call last):
            ...
        serde.exceptions.InstantiationError: 'int' object is not iterable

        >>> User.from_dict({'emails': [1234]})
        Traceback (most recent call last):
            ...
        serde.exceptions.DeserializationError: expected 'str' but got 'int'
    """

    def __init__(self, element=None, **kwargs):
        """
        Create a new List.

        Args:
            element (Field): the Field class/instance for elements in the List.
            **kwargs: keyword arguments for the `Field` constructor.
        """
        super(List, self).__init__(list, **kwargs)
        self.element = _resolve_to_field_instance(element)

    def serialize(self, value):
        """
        Serialize the given list.

        Each element in the list will be serialized with the specified element
        Field instance.
        """
        value = [self.element._serialize(v) for v in value]
        return super(List, self).serialize(value)

    def deserialize(self, value):
        """
        Deserialize the given list.

        Each element in the list will be deserialized with the specified element
        Field instance.
        """
        value = super(List, self).deserialize(value)
        return [self.element._deserialize(v) for v in value]

    def normalize(self, value):
        """
        Normalize the given list.

        Each element in the list will be normalized with the specified element
        Field instance.
        """
        value = super(List, self).normalize(value)
        return [self.element._normalize(v) for v in value]

    def validate(self, value):
        """
        Validate the given list.

        Each element in the list will be validated with the specified element
        Field instance.
        """
        super(List, self).validate(value)

        for v in value:
            self.element._validate(v)


class Tuple(Instance):
    """
    A tuple Field with required element types.

    Each element will be serialized, deserialized, normalized, and validated
    with the specified element type. The given element types can be specified
    using Field classes, Field instances, Model classes, or built-in types that
    have a corresponding Field type in this library.

    Consider an example person that has a name and a birthday

    ::

        >>> class Person(Model):
        ...     name = Str()
        ...     birthday = Tuple(int, str, int)

        >>> person = Person('Ross MacArthur', (19, 'June', 1994))
        >>> person.name
        'Ross MacArthur'
        >>> person.birthday[0]
        19
        >>> person.birthday[1]
        'June'
        >>> person.birthday[2]
        1994

        >>> Person('Beyonce', birthday=(4, 'September'))
        Traceback (most recent call last):
            ...
        serde.exceptions.InstantiationError: iterables have different lengths

        >>> Person.from_dict({'name': 'Beyonce', 'birthday': (4, 9, 1994)})
        Traceback (most recent call last):
            ...
        serde.exceptions.DeserializationError: expected 'str' but got 'int'
    """

    def __init__(self, *elements, **kwargs):
        """
        Create a new Tuple.

        Args:
            *elements (Field): the Field classes/instances for elements in this
                Tuple.
            **kwargs: keyword arguments for the `Field` constructor.
        """
        super(Tuple, self).__init__(tuple, **kwargs)
        self.elements = tuple(_resolve_to_field_instance(e, none_allowed=False) for e in elements)

    def serialize(self, value):
        """
        Serialize the given tuple.

        Each element in the tuple will be serialized with the specified element
        Field instance.
        """
        return tuple(e._serialize(v) for e, v in zip_equal(self.elements, value))

    def deserialize(self, value):
        """
        Deserialize the given tuple.

        Each element in the tuple will be deserialized with the specified
        element Field instance.
        """
        value = super(Tuple, self).deserialize(value)
        return tuple(e._deserialize(v) for e, v in zip_equal(self.elements, value))

    def normalize(self, value):
        """
        Normalize the given tuple.

        Each element in the tuple will be normalized with the specified element
        Field instance.
        """
        value = super(Tuple, self).normalize(value)
        return tuple(e._normalize(v) for e, v in zip_equal(self.elements, value))

    def validate(self, value):
        """
        Validate the given tuple.

        Each element in the tuple will be validated with the specified element
        Field instance.
        """
        super(Tuple, self).validate(value)

        for e, v in zip_equal(self.elements, value):
            e._validate(v)


#: This field represents the built-in `bool` type.
Bool = create('Bool', base=Instance, args=(bool,))

#: This field represents the built-in `complex` type.
Complex = create('Complex', base=Instance, args=(complex,))

#: This field represents the built-in `float` type.
Float = create('Float', base=Instance, args=(float,))

#: This field represents the built-in `int` type.
Int = create('Int', base=Instance, args=(int,))

#: This field represents the built-in `str` type.
Str = create('Str', base=Instance, args=(str,))

#: This field represents the built-in `bytes` type.
Bytes = create('Bytes', base=Instance, args=(bytes,)) if bytes != str else Str

try:
    #: This field represents the built-in `basestring` type.
    BaseString = create('BaseString', base=Instance, args=(basestring,))
except NameError:
    pass

try:
    #: This field represents the built-in `long` type.
    Long = create('Long', base=Instance, args=(long,))
except NameError:
    pass

try:
    #: This field represents the built-in `unicode` type.
    Unicode = create('Unicode', base=Instance, args=(unicode,))
except NameError:
    pass


class Regex(Str):

    def __init__(self, pattern, flags=0, **kwargs):
        """
        Create a new Regex.

        Args:
            pattern (str): the regex pattern that the value must match.
            flags (int): the regex flags passed directly to `re.compile`.
            **kwargs: keyword arguments for the `Field` constructor.
        """
        super(Regex, self).__init__(**kwargs)
        self.pattern = pattern
        self.flags = flags
        self._validate_regex = validate.regex(self.pattern, flags=self.flags)

    def validate(self, value):
        """
        Validate the given string matches the specified regex.
        """
        super(Regex, self).validate(value)
        self._validate_regex(value)


class Choice(Field):
    """
    One of a given selection of values.

    This field checks if the input data is one of the allowed values. These
    values do not need to be the same type.

    ::

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
        serde.exceptions.InstantiationError: 'yellow' is not a valid choice
    """

    def __init__(self, choices, **kwargs):
        """
        Create a new Choice.

        Args:
            choices: a list/range/tuple of allowed values.
            **kwargs: keyword arguments for the `Field` constructor.
        """
        super(Choice, self).__init__(**kwargs)
        self.choices = choices

    def validate(self, value):
        """
        Validate that the given value is one of the choices.
        """
        super(Choice, self).validate(value)
        validate.contains(self.choices)(value)


class DateTime(Instance):
    """
    A `~datetime.datetime` field.

    This field serializes `~datetime.datetime` objects as strings and
    deserializes string representations of datetimes as `~datetime.datetime`
    objects.

    The date format can be specified. It will default to ISO 8601.

    ::

        >>> class Entry(Model):
        ...     timestamp = DateTime(format='%Y-%m-%d %H:%M:%S')

        >>> entry = Entry(datetime.datetime(2001, 9, 11, 12, 5, 48))
        >>> entry.to_dict()
        OrderedDict([('timestamp', '2001-09-11 12:05:48')])
    """

    type = datetime.datetime

    def __init__(self, format='iso8601', **kwargs):
        """
        Create a new DateTime.

        Args:
            format (str): the datetime format to use. "iso8601" may be used for
                ISO 8601 datetimes.
            **kwargs: keyword arguments for the `Field` constructor.
        """
        super(DateTime, self).__init__(self.__class__.type, **kwargs)
        self.format = format

    def serialize(self, value):
        """
        Serialize the given `~datetime.datetime` as a string.
        """
        if self.format == 'iso8601':
            return value.isoformat()
        else:
            return value.strftime(self.format)

    def deserialize(self, value):
        """
        Deserialize the given string as a `~datetime.datetime`.
        """
        if self.format == 'iso8601':
            return isodate.parse_datetime(value)
        else:
            return datetime.datetime.strptime(value, self.format)


class Date(DateTime):
    """
    A `~datetime.date` field.

    This field behaves in a similar fashion to the `DateTime` field.
    """

    type = datetime.date

    def deserialize(self, value):
        """
        Deserialize the given string as a `~datetime.date`.
        """
        if self.format == 'iso8601':
            return isodate.parse_date(value)
        else:
            return datetime.datetime.strptime(value, self.format).date()


class Time(DateTime):
    """
    A `~datetime.time` field.

    This field behaves in a similar fashion to the `DateTime` field.
    """

    type = datetime.time

    def deserialize(self, value):
        """
        Deserialize the given string as a `~datetime.time`.
        """
        if self.format == 'iso8601':
            return isodate.parse_time(value)
        else:
            return datetime.datetime.strptime(value, self.format).time()


class Uuid(Instance):
    """
    A `~uuid.UUID` field.

    This field validates that the input data is a UUID. It serializes the UUID
    as a hex string, and deserializes hex strings or integers as UUIDs.

    ::

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
        serde.exceptions.InstantiationError: badly formed hexadecimal UUID string
    """

    def __init__(self, **kwargs):
        """
        Create a new Uuid.

        Args:
            **kwargs: keyword arguments for the `Field` constructor.
        """
        super(Uuid, self).__init__(uuid.UUID, **kwargs)

    def serialize(self, value):
        """
        Serialize the given `~uuid.UUID` as a string.
        """
        return str(value)

    def normalize(self, value):
        """
        Normalize the value into a `~uuid.UUID`.
        """
        if not isinstance(value, uuid.UUID):
            input_form = 'int' if isinstance(value, integer_types) else 'hex'
            return uuid.UUID(**{input_form: value})


FIELD_CLASS_MAP = {
    # Built-in types
    bool: Bool,
    bytes: Bytes,
    complex: Complex,
    dict: Dict,
    float: Float,
    int: Int,
    list: List,
    str: Str,
    tuple: Tuple,

    # Datetimes
    datetime.datetime: DateTime,
    datetime.date: Date,
    datetime.time: Time,

    # Others
    uuid.UUID: Uuid,
}

try:
    FIELD_CLASS_MAP[basestring] = BaseString
except NameError:
    pass

try:
    FIELD_CLASS_MAP[long] = Long
except NameError:
    pass

try:
    FIELD_CLASS_MAP[unicode] = Unicode
except NameError:
    pass


try_import_all('serde_ext.fields', globals())
