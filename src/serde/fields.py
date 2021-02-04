"""
This module contains field classes for use with `Models <serde.Model>`.
"""

import collections
import datetime
import decimal
import re
import uuid
from collections.abc import Mapping as MappingType

from serde.exceptions import ContextError, ValidationError, add_context
from serde.utils import is_subclass, try_lookup, zip_equal


def _resolve(thing, none_allowed=True):
    """
    Resolve an arbitrary object to a `Field` instance.

    Args:
        thing: anything to resolve to a `Field` instance.
        none_allowed (bool): if set then a thing of `None` will be resolved to a
            generic `Field`.

    Returns:
        Field: a field instance.
    """
    from serde.model import Model

    # If the thing is None then return a generic Field instance.
    if none_allowed and thing is None:
        return Field()
    # If the thing is a Field instance then thats great.
    elif isinstance(thing, Field):
        return thing
    # If the thing is a subclass of Field then attempt to create an instance.
    # This could fail the Field expects positional arguments.
    if is_subclass(thing, Field):
        return thing()
    # If the thing is a subclass of Model then create a Nested instance.
    if is_subclass(thing, Model):
        return Nested(thing)

    # If the thing is a built-in type that we support then create an Instance
    # with that type.
    try:
        return _FIELD_CLASS_MAP[thing]()
    except (KeyError, TypeError):
        pass

    raise TypeError(f'failed to resolve {thing!r} into a field')


class _Base(object):
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
        self.id = _Base._counter
        _Base._counter += 1
        self.serializers = serializers or []
        self.deserializers = deserializers or []

    def __eq__(self, other):
        """
        Whether two base fields are the same.
        """
        return isinstance(other, self.__class__) and self._attrs() == other._attrs()

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
            name: value
            for name, value in vars(self).items()
            if name not in ('id', '_model_cls')
        }

    def _bind(self, model_cls):
        """
        Bind the base field to a model class.
        """
        if hasattr(self, '_model_cls'):
            raise ContextError(
                f'attempted to use {self.__class__.__name__!r} instance more than once'
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
        for serializer in self.serializers:
            value = serializer(value)
        return self.serialize(value)

    def _deserialize(self, value):
        value = self.deserialize(value)
        for deserializer in self.deserializers:
            value = deserializer(value)
        return value

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


class Field(_Base):
    """
    A field on a `~serde.Model`.

    Fields handle serializing, deserializing, normalization, and validation of
    input values for `~serde.Model` objects.

    Args:
        rename (str): override the name for the field when serializing and
            expect this name when deserializing.
        default: a value to use if there is no input field value or the input
            value is `None`. This can also be a callable that generates the
            default. The callable must take no positional arguments. This
            default only applies to instantiated values. Field values are still
            required on deserialization.
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
        default=None,
        serializers=None,
        deserializers=None,
        normalizers=None,
        validators=None,
    ):
        """
        Create a new `Field`.
        """
        super(Field, self).__init__(
            serializers=serializers, deserializers=deserializers
        )
        self.rename = rename
        self.default = default
        self.normalizers = normalizers or []
        self.validators = validators or []

    def _attrs(self):
        """
        Returns a dictionary of all public attributes on this field.
        """
        return {
            name: value
            for name, value in vars(self).items()
            if name not in ('id', '_model_cls', '_attr_name', '_serde_name')
        }

    def _default(self):
        """
        Call the default function or return the default value.
        """
        return self.default() if callable(self.default) else self.default

    def _bind(self, model_cls, name):
        """
        Bind the field to a model class with an attribute name.
        """
        super(Field, self)._bind(model_cls)
        self._attr_name = name
        self._serde_name = self.rename if self.rename else name

    def _instantiate_with(self, model, kwargs):
        """
        Instantiate the corresponding model attribute from the keyword args.

        This method should .pop() from kwargs.
        """
        value = self._instantiate(kwargs.pop(self._attr_name, None))
        if value is None:
            raise TypeError(f'__init__() missing required argument {self._attr_name!r}')
        setattr(model, self._attr_name, value)

    def _serialize_with(self, model, d):
        """
        Serialize the corresponding model attribute to a dictionary.
        """
        d[self._serde_name] = self._serialize(getattr(model, self._attr_name))
        return d

    def _deserialize_with(self, model, d):
        """
        Deserialize the corresponding model attribute from a dictionary.
        """
        try:
            value = d[self._serde_name]
        except KeyError:
            raise ValidationError(f'missing data, expected field {self._serde_name!r}')
        setattr(model, self._attr_name, self._deserialize(value))
        return model, d

    def _normalize_with(self, model):
        """
        Normalize the model attribute according to this field's specification.
        """
        value = getattr(model, self._attr_name)
        setattr(model, self._attr_name, self._normalize(value))

    def _validate_with(self, model):
        """
        Validate the model attribute according to this field's specification.
        """
        self._validate(getattr(model, self._attr_name))

    def _instantiate(self, value):
        return self._default() if value is None else value

    def _normalize(self, value):
        value = self.normalize(value)
        for normalizer in self.normalizers:
            value = normalizer(value)
        return value

    def _validate(self, value):
        self.validate(value)
        for validator in self.validators:
            validator(value)

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


class Optional(Field):
    """
    An optional field.

    An `Optional` is a field that is allowed to be `None`. Serialization,
    normalization, deserialization, and validation using the wrapped field will
    only be called if the value is not `None`.

    Args:
        inner: the `Field` class/instance that this `Optional` wraps.
        default: a value to use if there is no input field value or the input
            value is `None`. This can also be a callable that generates the
            default. The callable must take no positional arguments.
        **kwargs: keyword arguments for the `Field` constructor.
    """

    def __init__(self, inner=None, **kwargs):
        """
        Create a new `Optional`.
        """
        super(Optional, self).__init__(**kwargs)
        self.inner = _resolve(inner)

    def _instantiate_with(self, model, kwargs):
        """
        Instantiate the corresponding model attribute from the keyword args.

        This method should .pop() from kwargs.
        """
        name = self._attr_name
        setattr(model, name, self._instantiate(kwargs.pop(name, None)))

    def _serialize_with(self, model, d):
        """
        Serialize the corresponding model attribute to a dictionary.

        The value will only be added to the dictionary if it is not `None`.
        """
        value = self._serialize(getattr(model, self._attr_name))
        if value is not None:
            d[self._serde_name] = value
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
        setattr(model, self._attr_name, self._deserialize(value))
        return model, d

    def _normalize_with(self, model):
        """
        Normalize the model attribute.
        """
        value = self._normalize(getattr(model, self._attr_name, None))
        setattr(model, self._attr_name, value)

    def _instantiate(self, value):
        return value

    def _serialize(self, value):
        if value is not None:
            value = self.serialize(value)
            for serializer in self.serializers:
                value = serializer(value)
        return value

    def _deserialize(self, value):
        if value is not None:
            value = self.deserialize(value)
            for deserializer in self.deserializers:
                value = deserializer(value)
        return value

    def _normalize(self, value):
        if value is not None:
            value = self.normalize(value)
            for normalizer in self.normalizers:
                value = normalizer(value)
        else:
            value = self._default()
        return value

    def _validate(self, value):
        if value is not None:
            self.validate(value)
            for validator in self.validators:
                validator(value)

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

    def __init__(self, ty, **kwargs):
        """
        Create a new `Instance`.
        """
        super(Instance, self).__init__(**kwargs)
        self.ty = ty

    def validate(self, value):
        """
        Validate the given value is an instance of the specified type.
        """
        if not isinstance(value, self.ty):
            raise ValidationError(
                f'invalid type, expected {self.ty.__name__!r}', value=value
            )


class Nested(Instance):
    """
    A field  for `~serde.Model` fields.

    A `Nested` is a wrapper field for models to support sub-models. The
    serialize and deserialize methods call the `~serde.Model.to_dict()` and
    `~serde.Model.from_dict()` methods on the model class. This allows complex
    nested models.

    Args:
        model_cls (serde.Model): the nested model class.
        **kwargs: keyword arguments for the `Field` constructor.
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
        if not isinstance(d, MappingType):
            raise ValidationError("invalid type, expected 'mapping'", value=d)
        return self.ty.from_dict(d)


class Flatten(Nested):
    """
    A field that flattens the serialized version of the wrapped `~serde.Model`
    into the parent dictionary.

    This effectively removes one level of structure between the serialized
    representation and the Python model representation.

    Warning:
        this field cannot be contained by another like an `Optional`, or a
        `List` or `Dict`.

    Args:
        model_cls (serde.Model): the nested model class.
        **kwargs: keyword arguments for the `Field` constructor.
    """

    def _serialize_with(self, model, d):
        """
        Serialize the corresponding nested model attribute to a dictionary.
        """
        d.update(self._serialize(getattr(model, self._attr_name)))
        return d

    def _deserialize_with(self, model, d):
        """
        Deserialize the corresponding model attribute from a dictionary.
        """
        setattr(model, self._attr_name, self._deserialize(d))
        return model, d


class _Container(Instance):
    """
    A base class for `Dict`, `List`, `Tuple`, and other container fields.
    """

    def __init__(self, ty, **kwargs):
        """
        Create a new `_Container`.
        """
        super(_Container, self).__init__(ty, **kwargs)
        self.kwargs = {}

    def _iter(self, value):
        """
        Iterate over the container.
        """
        raise NotImplementedError()

    def _apply(self, stage, element):
        """
        Apply a stage to a particular element in the container.
        """
        raise NotImplementedError()

    def serialize(self, value):
        """
        Serialize the given container.

        Each element in the container will be serialized with the specified
        field instances.
        """
        value = self.ty(
            (self._apply('_serialize', element) for element in self._iter(value)),
            **self.kwargs,
        )
        return super(_Container, self).serialize(value)

    def deserialize(self, value):
        """
        Deserialize the given container.

        Each element in the container will be deserialized with the specified
        field instances.
        """
        value = super(_Container, self).deserialize(value)
        return self.ty(
            (self._apply('_deserialize', element) for element in self._iter(value)),
            **self.kwargs,
        )

    def normalize(self, value):
        """
        Deserialize the given container.

        Each element in the container will be normalized with the specified
        field instances.
        """
        value = super(_Container, self).normalize(value)
        return self.ty(
            (self._apply('_normalize', element) for element in self._iter(value)),
            **self.kwargs,
        )

    def validate(self, value):
        """
        Validate the given container.

        Each element in the container will be validated with the specified field
        instances.
        """
        super(_Container, self).validate(value)
        for element in self._iter(value):
            self._apply('_validate', element)


class _Mapping(_Container):
    """
    A mapping field to be used as the base class for `Dict` and `OrderedDict`.
    """

    def __init__(self, ty, key=None, value=None, **kwargs):
        super(_Mapping, self).__init__(ty, **kwargs)
        self.key = _resolve(key)
        self.value = _resolve(value)

    def _iter(self, value):
        """
        Iterate over the mapping's items.
        """
        try:
            for element in value.items():
                yield element
        except (AttributeError, TypeError):
            raise ValidationError(
                f'invalid type, expected {self.ty.__name__!r}', value=value
            )

    def _apply(self, stage, element):
        """
        Apply the key stage to each key, and the value stage to each value.
        """
        key, value = element
        with add_context(key):
            return (getattr(self.key, stage)(key), getattr(self.value, stage)(value))


class Dict(_Mapping):
    """
    This field represents the built-in `dict` type.

    Args:
        key: the `Field` class or instance for keys in this `Dict`.
        value: the `Field` class or instance for values in this `Dict`.
        **kwargs: keyword arguments for the `Field` constructor.
    """

    def __init__(self, key=None, value=None, **kwargs):
        """
        Create a new `Dict`.
        """
        super(Dict, self).__init__(dict, key=key, value=value, **kwargs)


class OrderedDict(_Mapping):
    """
    An `~collections.OrderedDict` field.

    Args:
        key: the `Field` class or instance for keys in this `OrderedDict`.
        value: the `Field` class or instance for values in this `OrderedDict`.
        **kwargs: keyword arguments for the `Field` constructor.
    """

    def __init__(self, key=None, value=None, **kwargs):
        """
        Create a new `OrderedDict`.
        """
        super(OrderedDict, self).__init__(
            collections.OrderedDict, key=key, value=value, **kwargs
        )


class _Sequence(_Container):
    """
    A sequence field to be used as the base class for fields such as `List` and `Set`
    """

    def __init__(self, ty, element=None, **kwargs):
        super(_Sequence, self).__init__(ty, **kwargs)
        self.element = _resolve(element)

    def _iter(self, value):
        """
        Iterate over the sequence.
        """
        try:
            for element in enumerate(value):
                yield element
        except TypeError:
            raise ValidationError(
                f'invalid type, expected {self.ty.__name__!r}', value=value
            )

    def _apply(self, stage, element):
        """
        Apply a stage to a particular element in the container.
        """
        index, value = element
        with add_context(index):
            return getattr(self.element, stage)(value)


class Deque(_Sequence):
    """
    A `~collections.deque` field.

    Args:
        element: the `Field` class or instance for elements in the `Deque`.
        maxlen (int): the maximum length of this `Deque`.
        **kwargs: keyword arguments for the `Field` constructor.
    """

    def __init__(self, element=None, maxlen=None, **kwargs):
        """
        Create a new `Deque`.
        """
        super(Deque, self).__init__(collections.deque, element=element, **kwargs)
        self.kwargs = {'maxlen': maxlen}

    @property
    def maxlen(self):
        """
        The maximum length of this `Deque`.
        """
        return self.kwargs['maxlen']

    def validate(self, value):
        """
        Validate the given deque.
        """
        super(Deque, self).validate(value)
        if value.maxlen != self.maxlen:
            raise ValidationError(
                f'invalid max length, expected {self.maxlen}', value=value
            )


class FrozenSet(_Sequence):
    """
    This field represents the built-in `frozenset` type.

    Args:
        element: the `Field` class or instance for elements in the `Set`.
        **kwargs: keyword arguments for the `Field` constructor.
    """

    def __init__(self, element=None, **kwargs):
        """
        Create a new `FrozenSet`.
        """
        super(FrozenSet, self).__init__(frozenset, element=element, **kwargs)


class List(_Sequence):
    """
    This field represents the built-in `list` type.

    Args:
        element: the `Field` class or instance for elements in the `List`.
        **kwargs: keyword arguments for the `Field` constructor.
    """

    def __init__(self, element=None, **kwargs):
        """
        Create a new `List`.
        """
        super(List, self).__init__(list, element=element, **kwargs)


class Set(_Sequence):
    """
    This field represents the built-in `set` type.

    Args:
        element: the `Field` class or instance for elements in the `Set`.
        **kwargs: keyword arguments for the `Field` constructor.
    """

    def __init__(self, element=None, **kwargs):
        """
        Create a new `Set`.
        """
        super(Set, self).__init__(set, element=element, **kwargs)


class Tuple(_Sequence):
    """
    This field represents the built-in `tuple` type.

    Args:
        *elements: the `Field` classes or instances for elements in this tuple.
        **kwargs: keyword arguments for the `Field` constructor.
    """

    def __init__(self, *elements, **kwargs):
        """
        Create a new `Tuple`.
        """
        super(_Sequence, self).__init__(tuple, **kwargs)
        self.elements = tuple(_resolve(e, none_allowed=False) for e in elements)

    def _iter(self, value):
        """
        Iterate over the fields and each element in the tuple.
        """
        try:
            for element in zip_equal(self.elements, super(Tuple, self)._iter(value)):
                yield element
        except ValueError:
            raise ValidationError(
                f'invalid length, expected {len(self.elements)} elements',
                value=value,
            )

    def _apply(self, stage, element):
        """
        Apply the element field stage to the corresponding element value.
        """
        field, (index, value) = element
        with add_context(index):
            return getattr(field, stage)(value)


def create_primitive(name, ty):
    """
    Create a primitive `Field` class.
    """
    doc = f"""This field represents the built-in `{ty}` type.

Args:
    **kwargs: keyword arguments for the `Field` constructor.
"""

    def __init__(self, **kwargs):  # noqa: N807
        Instance.__init__(self, ty, **kwargs)

    __init__.__doc__ = f'Create a new `{name}`.'

    return type(name, (Instance,), {'__doc__': doc, '__init__': __init__})


Bool = create_primitive('Bool', bool)
Complex = create_primitive('Complex', complex)
Float = create_primitive('Float', float)
Int = create_primitive('Int', int)
Str = create_primitive('Str', str)
Bytes = create_primitive('Bytes', bytes)

del create_primitive


# A helper function...
def round_decimal(
    decimal_obj: decimal.Decimal, num_of_places: int = 6
) -> decimal.Decimal:
    return decimal_obj.quantize(decimal.Decimal(10) ** -num_of_places).normalize()


class Decimal(Instance):
    """
    A `~decimal.Decimal` field.

    This field serializes `~decimal.Decimal` objects as strings and
    deserializes string representations of Decimals as `~decimal.Decimal`
    objects.

    The resolution of the decimal can be specified. When not specified, the number
    is not rounded. When it is specified, the decimal is rounded to this number of
    decimal places upon serialization and deserialization.

    Note: When float type numbers are not rounded before serialization,
    they will be serialized in exact form, which as they are floats,
    is almost never the exact intended value,
    e.g. 0.2 = 0.20000000000000000000023

    Args:
        resolution (Union[int, bool]): The number of decimal places to round to.
        When None, rounding is disabled.
        **kwargs: keyword arguments for the `Field` constructor.
    """

    ty = decimal.Decimal

    def __init__(self, resolution=None, **kwargs):
        super(Decimal, self).__init__(self.__class__.ty, **kwargs)
        self.resolution = resolution

    def serialize(self, value: decimal.Decimal) -> str:
        if self.resolution is not None:
            value = round_decimal(value, num_of_places=self.resolution)
        return '{0:f}'.format(value)

    def deserialize(self, value) -> decimal.Decimal:
        try:
            if self.resolution is not None:
                return round_decimal(
                    decimal.Decimal(value), num_of_places=self.resolution
                )

            return decimal.Decimal(value)
        except decimal.DecimalException:
            raise ValidationError('invalid decimal', value=value)


class Literal(Field):
    """
    A literal field.

    A `Literal` is a field that always has to be the specified value.

    Args:
        value: the value that this `Literal` wraps.
        **kwargs: keyword arguments for the `Field` constructor.
    """

    def __init__(self, value, **kwargs):
        """
        Create a new `Literal`.
        """
        super(Literal, self).__init__(**kwargs)
        self.value = value

    def validate(self, value):
        """
        Validate that the given value is equal to the value.
        """
        if value != self.value:
            raise ValidationError(
                f'invalid literal, expected {self.value!r}', value=value
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
            raise ValidationError('invalid choice', value=value)


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

    ty = datetime.datetime

    def __init__(self, format='iso8601', **kwargs):
        """
        Create a new `DateTime`.
        """
        super(DateTime, self).__init__(self.__class__.ty, **kwargs)
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
            try:
                return self.ty.fromisoformat(value)
            except ValueError:
                raise ValidationError('invalid ISO 8601 datetime', value=value)
        else:
            try:
                return datetime.datetime.strptime(value, self.format)
            except (TypeError, ValueError):
                raise ValidationError(
                    f'invalid datetime, expected format {self.format!r}',
                    value=value,
                )


class Date(DateTime):
    """
    A `~datetime.date` field.

    This field behaves in a similar fashion to the `DateTime` field.
    """

    ty = datetime.date

    def deserialize(self, value):
        """
        Deserialize the given string as a `~datetime.date`.
        """
        if self.format == 'iso8601':
            try:
                return self.ty.fromisoformat(value)
            except ValueError:
                raise ValidationError('invalid ISO 8601 date', value=value)
        else:
            try:
                return datetime.datetime.strptime(value, self.format).date()
            except (TypeError, ValueError):
                raise ValidationError(
                    f'invalid date, expected format {self.format!r}',
                    value=value,
                )


class Time(DateTime):
    """
    A `~datetime.time` field.

    This field behaves in a similar fashion to the `DateTime` field.
    """

    ty = datetime.time

    def deserialize(self, value):
        """
        Deserialize the given string as a `~datetime.time`.
        """
        if self.format == 'iso8601':
            try:
                return self.ty.fromisoformat(value)
            except ValueError:
                raise ValidationError('invalid ISO 8601 time', value=value)
        else:
            try:
                return datetime.datetime.strptime(value, self.format).time()
            except (TypeError, ValueError):
                raise ValidationError(
                    f'invalid time, expected format {self.format!r}',
                    value=value,
                )


class Text(Instance):
    """
    A text field.

    A `Text` is a string field in Python 3 and a unicode field in Python 2. It
    will normalize byte strings into unicode strings using the given encoding.

    Args:
        encoding (str): the encoding with which to decode bytes. Passed
            directly to `bytes.decode`. If not given then `chardet.detect` will
            be used to detect the encoding.
        errors (str): The error handling scheme to use for the handling of
            decoding errors. Passed directly to `bytes.decode`.
        **kwargs: keyword arguments for the `Field` constructor.
    """

    def __init__(self, encoding=None, errors='strict', **kwargs):
        """
        Create a new `Text`.
        """
        super(Text, self).__init__(str, **kwargs)
        self.encoding = encoding
        self.errors = errors
        if self.encoding is None:
            self._detect = try_lookup('chardet.detect')

    def normalize(self, value):
        """
        Normalize byte strings to unicode strings.
        """
        if isinstance(value, bytes):
            if self.encoding is None:
                value = value.decode(
                    encoding=self._detect(value)['encoding'], errors=self.errors
                )
            else:
                value = value.decode(encoding=self.encoding, errors=self.errors)

        return value


class Regex(Text):
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
                f'invalid string, expected to match regex pattern {self.pattern!r}',
                value=value,
            )


class Uuid(Instance):
    """
    A `~uuid.UUID` field.

    A `Uuid` field validates that the input data is a UUID. It serializes the
    UUID into the specified output form and deserializes hex strings, bytes,
    fields, or integers as UUIDs.

    Args:
        output_form (str): the type of output form to serialize to. Possible
            values include 'str', 'urn', 'hex', 'int', 'bytes', or 'fields'.
        **kwargs: keyword arguments for the `Field` constructor.
    """

    def __init__(self, output_form='str', **kwargs):
        """
        Create a new `Uuid`.
        """
        if output_form not in ('str', 'urn', 'hex', 'int', 'bytes', 'fields'):
            raise ValueError('invalid output form')
        super(Uuid, self).__init__(uuid.UUID, **kwargs)
        self.output_form = output_form

    def serialize(self, value):
        """
        Serialize the given `~uuid.UUID` as a string.
        """
        if self.output_form == 'str':
            return str(value)
        else:
            return getattr(value, self.output_form)

    def normalize(self, value):
        """
        Normalize the value into a `~uuid.UUID`.
        """
        if not isinstance(value, uuid.UUID):
            input_form = None
            if isinstance(value, str):
                input_form = 'hex'
            elif isinstance(value, bytes):
                input_form = 'bytes'
            elif isinstance(value, int):
                input_form = 'int'
            elif isinstance(value, (list, tuple)):
                input_form = 'fields'
            if input_form:
                try:
                    return uuid.UUID(**{input_form: value})
                except ValueError:
                    pass
        return value


class IpAddress(Text):
    """
    A text field that asserts the text is a valid IP address.

    The validation is delegated to `validators.ip_address.ipv4` and
    `validators.ip_address.ipv6`.

    Args:
        **kwargs: keyword arguments for the `Field` constructor.
    """

    def __init__(self, **kwargs):
        super(IpAddress, self).__init__(**kwargs)
        self._validator_ipv4 = try_lookup('validators.ip_address.ipv4')
        self._validator_ipv6 = try_lookup('validators.ip_address.ipv6')

    def validate(self, value):
        super(IpAddress, self).validate(value)
        if not self._validator_ipv4(value) and not self._validator_ipv6(value):
            raise ValidationError('invalid IP address', value=value)


def create_from(foreign, name=None, human=None):
    """
    Create a new `Text` class from a `validators` function.
    """
    suffix = foreign.split('.', 1)[1]

    if name is None:
        name = suffix.title()
    if human is None:
        human = suffix

    doc = f"""A text field that asserts the text is a valid {human}.

The validation is delegated to `{foreign}`.

Args:
    **kwargs: keyword arguments for the `Field` constructor.
"""

    field_cls = type(name, (Text,), {'__doc__': doc})

    def __init__(self, **kwargs):  # noqa: N807
        super(field_cls, self).__init__(**kwargs)
        self._validator = try_lookup(foreign)

    def validate(self, value):
        super(field_cls, self).validate(value)
        if not self._validator(value):
            raise ValidationError(f'invalid {human}', value=value)

    field_cls.__init__ = __init__
    field_cls.validate = validate

    return field_cls


# Generate string fields using functions in the 'validators' package.
Domain = create_from('validators.domain')
Email = create_from('validators.email')
Ipv4Address = create_from(
    'validators.ip_address.ipv4', name='Ipv4Address', human='IPv4 address'
)
Ipv6Address = create_from(
    'validators.ip_address.ipv6', name='Ipv6Address', human='IPv6 address'
)
MacAddress = create_from(
    'validators.mac_address', name='MacAddress', human='MAC address'
)
Slug = create_from('validators.slug')
Url = create_from('validators.url', human='URL')

del create_from

_FIELD_CLASS_MAP = {
    # Built-in types
    bool: Bool,
    bytes: Bytes,
    complex: Complex,
    dict: Dict,
    float: Float,
    frozenset: FrozenSet,
    int: Int,
    list: List,
    set: Set,
    str: Str,
    tuple: Tuple,
    # Collections
    collections.deque: Deque,
    collections.OrderedDict: OrderedDict,
    # Datetimes
    datetime.datetime: DateTime,
    datetime.date: Date,
    datetime.time: Time,
    # Others
    uuid.UUID: Uuid,
    decimal.Decimal: Decimal,
}

__all__ = [name for name, obj in globals().items() if is_subclass(obj, Field)]
