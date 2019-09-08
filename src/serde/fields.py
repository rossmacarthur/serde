"""
This module contains field classes for use with `Models <serde.Model>`.
"""

import datetime
import re
import uuid
from functools import wraps
from itertools import chain

import isodate
from six import integer_types

from serde.exceptions import (
    ContextError,
    DeserializationError,
    NormalizationError,
    SerializationError,
    ValidationError,
    map_errors
)
from serde.utils import applied, chained, is_subclass, try_lookup, zip_equal


def _resolve_to_field_instance(thing, none_allowed=True):
    """
    Resolve an arbitrary object to a `Field` instance.

    Args:
        thing: anything to resolve to a `Field` instance.
        none_allowed (bool): if set then a thing of `None` will be resolved to a
            generic `Field`.

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
        '{!r} is not a Field, a Model class, an instance of a Field, '
        'or a supported built-in type'
        .format(thing)
    )


class BaseField(object):
    """
    A base field or tag on a `~serde.Model`.

    Fields and tags handle serializing and deserializing of input values for
    models. This class serves as a base class for both fields and tags.

    Args:
        serializers (list): a list of serializer functions taking the value to
            serialize as an argument. The functions need to raise an `Exception`
            if they fail. These serializer functions will be applied before the
            primary serializer on this base field.
        deserializers (list): a list of deserializer functions taking the value
            to deserialize as an argument. The functions need to raise an
            `Exception` if they fail. These deserializer functions will be
            applied after the primary deserializer on this base field.
    """

    # This is so we can get the order the bases were instantiated in.
    _counter = 1

    def __init__(self, serializers=None, deserializers=None):
        """
        Create a new base field.
        """
        self.id = Field._counter
        Field._counter += 1
        self.serializers = serializers or []
        self.deserializers = deserializers or []

    def __eq__(self, other):
        """
        Whether two base fields are the same.
        """
        return (
            isinstance(other, self.__class__)
            and self._attrs() == other._attrs()
        )

    @property
    def __model__(self):
        """
        The model class that the base field is bound to.
        """
        return self._model_cls

    def _attrs(self):
        """
        Returns a dictionary of all public attributes on this base field.
        """
        return {
            name: value for name, value in vars(self).items()
            if name not in ('id', '_model_cls')
        }

    def _bind(self, model_cls):
        """
        Bind the base field to a model class.
        """
        if hasattr(self, '_model_cls'):
            raise ContextError(
                '{name!r} instance used multiple times'
                .format(name=self.__class__.__name__),
            )

        self._model_cls = model_cls

    def _serialize_with(self, model, d):
        """
        Serialize value(s) from a model instance to a dictionary.

        This method needs to be overridden and should use ``self._serialize()``
        on individual values.

        Args:
            model (Model): the model instance that we are serializing from.
            d (dict): the dictionary to serialize to.

        Returns:
            dict: the updated dictionary to continue serializing to.
        """
        raise NotImplementedError('this method should be overridden')

    def _deserialize_with(self, model, d):
        """
        Deserialize value(s) from a dictionary to a model instance.

        This method needs to be overridden and should use
        ``self._deserialize()`` on individual values.

        Args:
            model (Model): the model instance that we are deserializing to.
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
        Serialize a value according to this base field's specification.
        """
        return value

    def deserialize(self, value):
        """
        Deserialize a value according to this base field's specification.
        """
        return value


class Field(BaseField):
    """
    A field on a `~serde.Model`.

    Fields handle serializing, deserializing, normalization, and validation of
    input values for `~serde.Model` objects.

    Args:
        rename (str): override the name for the field when serializing and
            expect this name when deserializing.
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
        Create a new `Field`.
        """
        super(Field, self).__init__(
            serializers=serializers,
            deserializers=deserializers
        )
        self.rename = rename
        self.normalizers = normalizers or []
        self.validators = validators or []

    def _attrs(self):
        """
        Returns a dictionary of all public attributes on this field.
        """
        return {
            name: value for name, value in vars(self).items()
            if name not in ('id', '_model_cls', '_attr_name', '_serde_name')
        }

    def _bind(self, model_cls, name):
        """
        Bind the field to a model class with an attribute name.
        """
        super(Field, self)._bind(model_cls)
        self._attr_name = name
        self._serde_name = self.rename if self.rename else name

    def _serialize_with(self, model, d):
        """
        Serialize the corresponding model attribute to a dictionary.
        """
        try:
            value = getattr(model, self._attr_name)
        except AttributeError:
            raise SerializationError(
                'expected attribute {!r}'.format(self._attr_name),
                field=self,
                model_cls=model.__class__
            )

        with map_errors(
            SerializationError,
            value=value,
            field=self,
            model_cls=model.__class__
        ):
            d[self._serde_name] = self._serialize(value)

        return d

    def _deserialize_with(self, model, d):
        """
        Deserialize the corresponding model attribute from a dictionary.
        """
        try:
            value = d[self._serde_name]
        except KeyError:
            raise DeserializationError(
                'expected field {!r}'.format(self._serde_name),
                field=self,
                model_cls=model.__class__
            )

        with map_errors(
            DeserializationError,
            value=value,
            field=self,
            model_cls=model.__class__
        ):
            setattr(model, self._attr_name, self._deserialize(value))

        return model, d

    def _normalize_with(self, model):
        """
        Normalize the model attribute according to this field's specification.
        """
        try:
            value = getattr(model, self._attr_name)
        except AttributeError:
            raise NormalizationError(
                'expected attribute {!r}'.format(self._attr_name),
                field=self,
                model_cls=model.__class__
            )

        with map_errors(
            NormalizationError,
            value=value,
            field=self,
            model_cls=model.__class__
        ):
            setattr(model, self._attr_name, self._normalize(value))

    def _validate_with(self, model):
        """
        Validate the model attribute according to this field's specification.
        """
        try:
            value = getattr(model, self._attr_name)
        except AttributeError:
            raise ValidationError(
                'expected attribute {!r}'.format(self._attr_name),
                field=self,
                model_cls=model.__class__
            )

        with map_errors(
            ValidationError,
            value=value,
            field=self,
            model_cls=model.__class__
        ):
            self._validate(value)

    def _normalize(self, value):
        return chained(chain([self.normalize], self.normalizers), value)

    def _validate(self, value):
        applied(chain([self.validate], self.validators), value)

    def normalize(self, value):
        """
        Normalize a value according to this field's specification.

        By default this method does not do anything.
        """
        return value

    def validate(self, value):
        """
        Validate a value according to this field's specification.

        By default this method does not do anything.
        """
        pass


def _create_serialize(cls, serializers):
    """
    Create a new serialize method with extra serializer functions.
    """
    @wraps(serializers[0])
    def serialize(self, value):
        funcs = chain(serializers, [super(cls, self).serialize])
        return chained(funcs, value)
    return serialize


def _create_deserialize(cls, deserializers):
    """
    Create a new deserialize method with extra deserializer functions.
    """
    @wraps(deserializers[0])
    def deserialize(self, value):
        funcs = chain([super(cls, self).deserialize], deserializers)
        return chained(funcs, value)
    return deserialize


def _create_normalize(cls, normalizers):
    """
    Create a new normalize method with extra normalizer functions.
    """
    @wraps(normalizers[0])
    def normalize(self, value):
        funcs = chain([super(cls, self).normalize], normalizers)
        return chained(funcs, value)
    return normalize


def _create_validate(cls, validators):
    """
    Create a new validate method with extra validator functions.
    """
    @wraps(validators[0])
    def validate(self, value):
        funcs = chain([super(cls, self).validate], validators)
        applied(funcs, value)
    return validate


def create(
    name,
    base=None,
    args=None,
    description=None,
    serializers=None,
    deserializers=None,
    normalizers=None,
    validators=None
):
    """
    Create a new `Field` class.

    This is a convenience method for creating new Field classes from arbitrary
    serializer, deserializer, normalizer, and/or validator functions.

    Args:
        name (str): the name of the class.
        base (Field): the base field class to subclass.
        args (tuple): positional arguments for the base class's ``__init__``
            method.
        serializers (list): a list of serializer functions taking the value to
            serialize as an argument. The functions need to raise an `Exception`
            if they fail. These serializer functions will be applied before the
            primary serializer on this field.
        deserializers (list): a list of deserializer functions taking the value
            to deserialize as an argument. The functions need to raise an
            `Exception` if they fail. These deserializer functions will be
            applied after the primary deserializer on this field.
        normalizers (list): a list of normalizer functions taking the value to
            normalize as an argument. The functions need to raise an `Exception`
            if they fail. These normalizer functions will be applied after the
            primary normalizer on this field.
        validators (list): a list of validator functions taking the value to
            validate as an argument. The functions need to raise an `Exception`
            if they fail.

    Returns:
        class: a new `Field` class.
    """
    if not base:
        base = Field

    if not description:
        description = name.lower()

    doc = """\
{description}

Args:
    **kwargs: keyword arguments for the `Field` constructor.
""".format(description=description)

    field_cls = type(name, (base,), {'__doc__': doc})

    if args:
        def __init__(self, **kwargs):  # noqa: N807
            super(field_cls, self).__init__(*args, **kwargs)

        __init__.__doc__ = 'Create a new `{name}`.'.format(name=name)
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
    An optional field.

    An `Optional` is a field that is allowed to be `None`. Serialization,
    normalization, deserialization, and validation using the wrapped field will
    only be called if the value is not `None`. The wrapped Field can be
    specified using `Field` classes, `Field` instances, `~serde.Model` classes,
    or built-in types that have a corresponding field type in this library.

    Args:
        inner: the the `Field` class/instance that this `Optional` wraps.
        default: a value to use if there is no input field value or the input
            value is `None`. This can also be a callable that generates the
            default. The callable must take no positional arguments.
        **kwargs: keyword arguments for the `Field` constructor.
    """

    def __init__(self, inner=None, default=None, **kwargs):
        """
        Create a new `Optional`.
        """
        super(Optional, self).__init__(**kwargs)
        self.inner = _resolve_to_field_instance(inner)
        self.default = default

    def _serialize_with(self, model, d):
        """
        Serialize the corresponding model attribute to a dictionary.

        The value will only be added to the dictionary if it is not `None`.
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
            with map_errors(
                SerializationError,
                value=value,
                field=self,
                model_cls=model.__class__
            ):
                d[self._serde_name] = self._serialize(value)

        return d

    def _deserialize_with(self, model, d):
        """
        Deserialize the corresponding model attribute from a dictionary.

        If the field is not present in the dictionary then the model instance is
        left unchanged.
        """
        try:
            value = d[self._serde_name]
        except KeyError:
            return model, d

        with map_errors(
            DeserializationError,
            value=value,
            field=self,
            model_cls=model.__class__
        ):
            setattr(model, self._attr_name, self._deserialize(value))

        return model, d

    def _normalize_with(self, model):
        """
        Normalize the model attribute.

        If the value is `None` or not present then the value will be normalized
        using the inner field's normalize method. Otherwise, if a default is
        specified then it is set here.
        """
        value = getattr(model, self._attr_name, None)

        if value is not None:
            with map_errors(
                NormalizationError,
                value=value,
                field=self,
                model_cls=model.__class__
            ):
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
        Validate the model attribute if it is not `None`.
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
            with map_errors(
                ValidationError,
                value=value,
                field=self,
                model_cls=model.__class__
            ):
                self._validate(value)

    def serialize(self, value):
        """
        Serialize the given value using the inner `Field`.
        """
        return self.inner._serialize(value)

    def deserialize(self, value):
        """
        Deserialize the given value using the inner `Field`.
        """
        return self.inner._deserialize(value)

    def normalize(self, value):
        """
        Normalize the given value using the inner `Field`.
        """
        return self.inner._normalize(value)

    def validate(self, value):
        """
        Validate the given value using the inner `Field`.
        """
        self.inner._validate(value)


class Instance(Field):
    """
    A field that is an instance of a type.

    An `Instance` field simply validates that the data is the specified type.

    Args:
        type: the type that this `Instance` wraps.
        **kwargs: keyword arguments for the `Field` constructor.
    """

    def __init__(self, type, **kwargs):
        """
        Create a new `Instance`.
        """
        super(Instance, self).__init__(**kwargs)
        self.type = type

    def validate(self, value):
        """
        Validate the given value is an instance of the specified type.
        """
        super(Instance, self).validate(value)
        if not isinstance(value, self.type):
            raise ValidationError(
                'expected {!r} but got {!r}'
                .format(self.type.__name__, value.__class__.__name__)
            )


class Nested(Instance):
    """
    A field  for `~serde.Model` fields.

    A `Nested` is a wrapper field for models to support sub-models. The
    serialize and deserialize methods call the `~serde.Model.to_dict()` and
    `~serde.Model.from_dict()` methods on the model class. This allows complex
    nested models.
    """

    def serialize(self, model):
        """
        Serialize the given `~serde.Model` instance as a dictionary.
        """
        return model.to_dict()

    def deserialize(self, d):
        """
        Deserialize the given dictionary to a `~serde.Model` instance.
        """
        return self.type.from_dict(d)


class Dict(Instance):
    """
    This field represents the built-in `dict` type.

    Each key and value will be serialized, deserialized, normalized, and
    validated with the specified key and value types. The key and value types
    can be specified using `Field` classes, `Field` instances, `~serde.Model`
    classes, or built-in types that have a corresponding field type in this
    library.

    Args:
        key: the `Field` class or instance for keys in this `Dict`.
        value: the `Field` class or instance for values in this `Dict`.
        **kwargs: keyword arguments for the `Field` constructor.
    """

    def __init__(self, key=None, value=None, **kwargs):
        """
        Create a new `Dict`.
        """
        super(Dict, self).__init__(dict, **kwargs)
        self.key = _resolve_to_field_instance(key)
        self.value = _resolve_to_field_instance(value)

    def serialize(self, value):
        """
        Serialize the given dictionary.

        Each key and value in the dictionary will be serialized with the
        specified key and value field instances.
        """
        return {
            self.key._serialize(k): self.value._serialize(v)
            for k, v in value.items()
        }

    def deserialize(self, value):
        """
        Deserialize the given dictionary.

        Each key and value in the dictionary will be deserialized with the
        specified key and value field instances.
        """
        return {
            self.key._deserialize(k): self.value._deserialize(v)
            for k, v in value.items()
        }

    def normalize(self, value):
        """
        Normalize the given dictionary.

        Each key and value in the dictionary will be normalized with the
        specified key and value field instances.
        """
        return {
            self.key._normalize(k): self.value._normalize(v)
            for k, v in value.items()
        }

    def validate(self, value):
        """
        Validate the given dictionary.

        Each key and value in the dictionary will be validated with the
        specified key and value field instances.
        """
        super(Dict, self).validate(value)

        for k, v in value.items():
            self.key._validate(k)
            self.value._validate(v)


class List(Instance):
    """
    This field represents the built-in `list` type.

    Each element is serialized, deserialized, normalized and validated with the
    specified element type. The element type can be specified using `Field`
    classes, `Field` instances, `~serde.Model` classes, or built-in types that
    have a corresponding field type in this library.

    Args:
        element: the `Field` class or instance for elements in the `List`.
        **kwargs: keyword arguments for the `Field` constructor.
    """

    def __init__(self, element=None, **kwargs):
        """
        Create a new `List`.
        """
        super(List, self).__init__(list, **kwargs)
        self.element = _resolve_to_field_instance(element)

    def serialize(self, value):
        """
        Serialize the given list.

        Each element in the list will be serialized with the specified element
        field instance.
        """
        value = [self.element._serialize(v) for v in value]
        return super(List, self).serialize(value)

    def deserialize(self, value):
        """
        Deserialize the given list.

        Each element in the list will be deserialized with the specified element
        field instance.
        """
        value = super(List, self).deserialize(value)
        return [self.element._deserialize(v) for v in value]

    def normalize(self, value):
        """
        Normalize the given list.

        Each element in the list will be normalized with the specified element
        field instance.
        """
        value = super(List, self).normalize(value)
        return [self.element._normalize(v) for v in value]

    def validate(self, value):
        """
        Validate the given list.

        Each element in the list will be validated with the specified element
        field instance.
        """
        super(List, self).validate(value)

        for v in value:
            self.element._validate(v)


class Tuple(Instance):
    """
    This field represents the built-in `tuple` type.

    Each element will be serialized, deserialized, normalized, and validated
    with the specified element type. The given element types can be specified
    using `Field` classes, `Field` instances, `~serde.Model` classes, or
    built-in types that have a corresponding field type in this library.

    Args:
        *elements: the `Field` classes or instances for elements in this tuple.
        **kwargs: keyword arguments for the `Field` constructor.
    """

    def __init__(self, *elements, **kwargs):
        """
        Create a new `Tuple`.
        """
        super(Tuple, self).__init__(tuple, **kwargs)
        self.elements = tuple(
            _resolve_to_field_instance(e, none_allowed=False)
            for e in elements
        )

    def serialize(self, value):
        """
        Serialize the given tuple.

        Each element in the tuple will be serialized with the specified element
        Field instance.
        """
        return tuple(
            e._serialize(v)
            for e, v in zip_equal(self.elements, value)
        )

    def deserialize(self, value):
        """
        Deserialize the given tuple.

        Each element in the tuple will be deserialized with the specified
        element field instance.
        """
        value = super(Tuple, self).deserialize(value)
        return tuple(
            e._deserialize(v)
            for e, v in zip_equal(self.elements, value)
        )

    def normalize(self, value):
        """
        Normalize the given tuple.

        Each element in the tuple will be normalized with the specified element
        field instance.
        """
        value = super(Tuple, self).normalize(value)
        return tuple(
            e._normalize(v)
            for e, v in zip_equal(self.elements, value)
        )

    def validate(self, value):
        """
        Validate the given tuple.

        Each element in the tuple will be validated with the specified element
        field instance.
        """
        super(Tuple, self).validate(value)

        for e, v in zip_equal(self.elements, value):
            e._validate(v)


def create_primitive(name, type):
    """
    Create a primitive `Field` class.
    """
    description = (
        'This field represents the built-in `{type}` type.'
        .format(type=type.__name__)
    )
    return create(name, base=Instance, args=(type,), description=description)


Bool = create_primitive('Bool', bool)
Complex = create_primitive('Complex', complex)
Float = create_primitive('Float', float)
Int = create_primitive('Int', int)
Str = create_primitive('Str', str)
Bytes = create_primitive('Bytes', bytes) if bytes != str else Str

try:
    BaseString = create_primitive('BaseString', basestring)
except NameError:
    pass

try:
    Long = create_primitive('Long', long)
except NameError:
    pass

try:
    Unicode = create_primitive('Unicode', unicode)
except NameError:
    pass

del create_primitive


class Constant(Field):
    """
    A constant field.

    A `Constant` is a field that always has to be the specified value.

    Args:
        value: the constant value that this `Constant` wraps.
        **kwargs: keyword arguments for the `Field` constructor.
    """

    def __init__(self, value, **kwargs):
        """
        Create a new `Constant`.
        """
        super(Constant, self).__init__(**kwargs)
        self.value = value

    def validate(self, value):
        """
        Validate that the given value is equal to the constant value.
        """
        if value != self.value:
            raise ValidationError(
                'expected {!r} but got {!r}'
                .format(self.value, value)
            )


class Choice(Field):
    """
    One of a given selection of values.

    A `Choice` field checks if the input data is one of the allowed values.
    These values do not need to be the same type.

    Args:
        choices: a list or range or tuple of allowed values.
        **kwargs: keyword arguments for the `Field` constructor.
    """

    def __init__(self, choices, **kwargs):
        """
        Create a new `Choice`.
        """
        super(Choice, self).__init__(**kwargs)
        self.choices = choices

    def validate(self, value):
        """
        Validate that the given value is one of the choices.
        """
        super(Choice, self).validate(value)
        if value not in self.choices:
            raise ValidationError('{!r} is not a valid choice'.format(value))


class DateTime(Instance):
    """
    A `~datetime.datetime` field.

    This field serializes `~datetime.datetime` objects as strings and
    deserializes string representations of datetimes as `~datetime.datetime`
    objects.

    The date format can be specified. It will default to ISO 8601.

    Args:
        format (str): the datetime format to use. "iso8601" may be used for
            ISO 8601 datetimes.
        **kwargs: keyword arguments for the `Field` constructor.
    """

    type = datetime.datetime

    def __init__(self, format='iso8601', **kwargs):
        """
        Create a new `DateTime`.
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


class Regex(Str):
    """
    A regex field.

    A `Regex` is a string field that validates that data matches a specified
    regex expression.

    Args:
        pattern (str): the regex pattern that the value must match.
        flags (int): the regex flags passed directly to `re.compile`.
        **kwargs: keyword arguments for the `Field` constructor.
    """

    def __init__(self, pattern, flags=0, **kwargs):
        """
        Create a new `Regex`.
        """
        super(Regex, self).__init__(**kwargs)
        self.pattern = pattern
        self.flags = flags
        self._compiled = re.compile(pattern, flags=flags)

    def validate(self, value):
        """
        Validate the given string matches the specified regex.
        """
        super(Regex, self).validate(value)
        if not self._compiled.match(value):
            raise ValidationError(
                '{!r} does not match regex {!r}'
                .format(value, self.pattern)
            )


class Uuid(Instance):
    """
    A `~uuid.UUID` field.

    A `Uuid` field validates that the input data is a UUID. It serializes the
    UUID as a hex string, and deserializes hex strings or integers as UUIDs.

    Args:
        **kwargs: keyword arguments for the `Field` constructor.
    """

    def __init__(self, **kwargs):
        """
        Create a new `Uuid`.
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


def create_from(foreign, name=None, human=None):
    """
    Create a new `Field` class from a `validators` function.
    """
    suffix = foreign.split('.', 1)[1]

    if name is None:
        name = suffix.title()
    if human is None:
        human = suffix

    doc = """\
A string field that asserts the string is a valid {}.

The validation is delegated to `{}`.

Args:
    **kwargs: keyword arguments for the `Field` constructor.
""".format(human, foreign)

    field_cls = type(name, (Str,), {'__doc__': doc})

    def __init__(self, **kwargs):  # noqa: N807
        super(field_cls, self).__init__(**kwargs)
        self._validator = try_lookup(foreign)

    def validate(self, value):
        super(field_cls, self).validate(value)
        if not self._validator(value):
            raise ValidationError('{!r} is not a valid {}'.format(value, human))

    field_cls.__init__ = __init__
    field_cls.validate = validate

    return field_cls


# Generate string fields using functions in the 'validators' package.
Domain = create_from('validators.domain')
Email = create_from('validators.email')
Ipv4Address = create_from('validators.ip_address.ipv4', name='Ipv4Address', human='IPv4 address')
Ipv6Address = create_from('validators.ip_address.ipv6', name='Ipv6Address', human='IPv6 address')
MacAddress = create_from('validators.mac_address', name='MacAddress', human='MAC address')
Slug = create_from('validators.slug')
Url = create_from('validators.url', human='URL')

del create_from

__all__ = [name for name, obj in globals().items() if is_subclass(obj, Field)]
__all__.append('create')
