"""
This module defines the core Model class.
"""

from collections import OrderedDict
from contextlib import contextmanager

from six import with_metaclass

from serde.exceptions import (
    DeserializationError,
    InstantiationError,
    NormalizationError,
    SerializationError,
    SkipSerialization,
    ValidationError
)
from serde.fields import Field
from serde.utils import dict_partition, subclasses, zip_until_right


try:
    import simplejson as json
except ImportError:
    import json


__all__ = ['Model']


@contextmanager
def map_errors(error, model=None, field=None, value=None):
    """
    Returns a decorator that maps generic exceptions to the given SerdeError.

    Args:
        error (SerdeError): a SerdeError to wrap any generic exceptions that are
            generated by the Field function.
        model (Model): the Model in this context.
        value: the Field value in this context.
        field (Field): the Field in this context.

    Returns:
        function: the real decorator.
    """
    try:
        yield
    except SkipSerialization:
        raise
    except error as e:
        e.add_context(value=value, field=field, model=model)
        raise
    except Exception as e:
        raise error.from_exception(e, value=value, field=field, model=model)


class Fields(OrderedDict):
    """
    An OrderedDict that allows value access with dot notation.
    """

    def names(self):
        """
        Provides a view on Field names.
        """
        return [field.name for field in self.values()]

    def __getattr__(self, name):
        """
        Return values in the dictionary using attribute access with keys.
        """
        try:
            return self[name]
        except KeyError:
            return super(Fields, self).__getattribute__(name)


class Meta(object):
    """
    Extra configuration for a `Model`.

    Warning:
        You should not instantiate or subclass this class directly. Instead you
        should use the Meta paradigm by adding a inner ``Meta`` class to your
        Model classes.
    """

    #: Whether the Model is allowed to be instantiated.
    abstract = False
    #: The key to use when tagging this Model.
    tag = None
    #: The content key to use when tagging this Model.
    content = None

    def is_owner(self, cls_or_instance):
        """
        Check whether the given Model or Model instance is the Meta owner.
        """
        cls = cls_or_instance.__class__ if isinstance(cls_or_instance, Model) else cls_or_instance
        return cls == self.model

    def variants(self):
        """
        Return a list of variants.
        """
        variants = self.model.__subclasses__()

        if not self.abstract:
            variants = [self.model] + variants

        return variants

    def tag_for(self, variant):
        """
        Return the tag for the given variant.
        """
        return variant.__name__

    def variant_for(self, tag):
        """
        Return the variant for the given tag.
        """
        for variant in self.variants():
            if self.tag_for(variant) == tag:
                return variant


class ModelType(type):
    """
    A metaclass for Models.

    This metaclass pulls `~serde.fields.Field` attributes off the defined class
    and adds them as a `_fields` attribute to the resulting object. Model
    methods then use the `_fields` attribute to construct, validate, and convert
    Models between data formats.
    """

    def __new__(cls, cname, bases, attrs):
        """
        Create a new `Model` class.

        Args:
            cname (str): the class name.
            bases (tuple): the base classes.
            attrs (dict): the attributes for this class.

        Returns:
            Model: a new Model class.
        """
        # Handle the Meta class.
        if 'Meta' in attrs:
            meta_attrs = {
                k: v for k, v in attrs.pop('Meta').__dict__.items()
                if not k.startswith('_')
            }
            meta = type('Meta', (Meta,), meta_attrs)()
        else:
            for base in bases:
                if hasattr(base, '_meta'):
                    meta = base._meta
                    break
            else:
                meta = Meta()

        def is_field(key, value):
            if isinstance(value, Field):
                value._name = key
                return True
            return False

        # Split the attrs into Fields and non-Fields.
        fields, final_attrs = dict_partition(attrs, is_field)

        # Add base class Fields.
        for base in bases:
            if hasattr(base, '_fields'):
                fields.update({
                    name: field for name, field in base._fields.items()
                    if name not in attrs
                })

        # Order the fields by the Field identifier. This gets the order that
        # they were defined on the Models. We add these to the Model.
        final_attrs['_fields'] = Fields(sorted(fields.items(), key=lambda x: x[1].id))
        final_attrs['_meta'] = meta

        # Figure out the parent.
        if not (bases == (object,) and cname == 'Model'):
            final_attrs['_parent'] = next(iter(b for b in bases if issubclass(b, Model)))
        else:
            final_attrs['_parent'] = None

        cls = super(ModelType, cls).__new__(cls, cname, bases, final_attrs)

        # So that the Meta object knows its Model.
        if not hasattr(cls._meta, 'model'):
            cls._meta.model = cls

        return cls


class Model(with_metaclass(ModelType, object)):
    """
    The base Model to be subclassed.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a new Model.

        Args:
            *args: positional arguments values for each Field on the Model. If
                these are given they will be interpreted as corresponding to the
                Fields in the order the Fields are defined on the Model.
            **kwargs: keyword argument values for each Field on the Model.
        """
        if self._meta.is_owner(self) and self._meta.abstract:
            raise InstantiationError(
                'unable to instantiate abstract Model {!r}'.format(self.__class__.__name__)
            )

        try:
            for name, value in zip_until_right(self._fields.keys(), args):
                if name in kwargs:
                    raise InstantiationError(
                        '__init__() got multiple values for keyword argument {!r}'
                        .format(name)
                    )
                kwargs[name] = value
        except ValueError:
            raise InstantiationError(
                '__init__() takes a maximum of {!r} positional arguments but {!r} were given'
                .format(len(self._fields) + 1, len(args) + 1)
            )

        for name in self._fields.keys():
            setattr(self, name, kwargs.pop(name, None))

        if kwargs:
            raise InstantiationError(
                'invalid keyword argument{} {}'.format(
                    '' if len(kwargs.keys()) == 1 else 's',
                    ', '.join('{!r}'.format(k) for k in kwargs.keys())
                )
            )

        with map_errors(InstantiationError):
            self.normalize_all()
            self.validate_all()

    def __eq__(self, other):
        """
        Whether two Models are the same.
        """
        return (
            isinstance(other, self.__class__)
            and all(
                getattr(self, name) == getattr(other, name)
                for name in self._fields.keys()
            )
        )

    def __hash__(self):
        """
        Return a hash value for this Model.
        """
        return hash(tuple((name, getattr(self, name)) for name in self._fields.keys()))

    def __repr__(self):
        """
        Return the canonical string representation of this Model.
        """
        values = ', '.join(
            '{}={!r}'.format(name, getattr(self, name))
            for name in self._fields.keys()
            if getattr(self, name) is not None
        )
        return '{name}({values})'.format(name=self.__class__.__name__, values=values)

    @classmethod
    def __subclasses_recursed__(cls):
        """
        Returns the recursed subclasses.
        """
        return subclasses(cls)

    def _serialize_field(self, field, value):
        """
        Serialize a single Field and map all errors to `SerializationError`.
        """
        with map_errors(SerializationError, model=self.__class__, field=field, value=value):
            return field._serialize(value)

    @classmethod
    def _deserialize_field(cls, field, value):
        """
        Deserialize a single Field and map all errors to `DeserializationError`.
        """
        with map_errors(DeserializationError, model=cls, field=field, value=value):
            return field._deserialize(value)

    def _normalize_field(self, field, value):
        """
        Normalize a single Field and map all errors to `NormalizationError`.
        """
        with map_errors(NormalizationError, model=self.__class__, field=field, value=value):
            return field._normalize(value)

    def _validate_field(self, field, value):
        """
        Validate a single Field and map all errors to `ValidationError`.
        """
        with map_errors(ValidationError, model=self.__class__, field=field, value=value):
            field._validate(value)

    def normalize_all(self):
        """
        Normalize all Fields on this Model, and the Model itself.

        This is called by the Model constructor and on deserialization, so this
        is only needed if you modify attributes directly and want to renormalize
        the Model.
        """
        for name, field in self._fields.items():
            setattr(self, name, self._normalize_field(field, getattr(self, name)))

        with map_errors(NormalizationError, model=self.__class__):
            self.normalize()

    def validate_all(self):
        """
        Validate all Fields on this Model, and the Model itself.

        This is called by the Model constructor, so this is only needed if you
        modify attributes directly and want to revalidate the Model.
        """
        for name, field in self._fields.items():
            self._validate_field(field, getattr(self, name))

        with map_errors(ValidationError, model=self.__class__):
            self.validate()

    def normalize(self):
        """
        Normalize this Model.

        Override this method to add any additional normalization to the Model.
        This will be called after all Fields have been normalized.
        """
        pass

    def validate(self):
        """
        Validate this Model.

        Override this method to add any additional validation to the Model. This
        will be called after all Fields have been validated.
        """
        pass

    @classmethod
    def _from_dict_transform_get_tag(cls, d):
        # Externally tagged variant
        if cls._meta.tag is True:
            try:
                return next(iter(d))
            except StopIteration:
                raise DeserializationError('expected externally tagged data')
        # Internally/adjacently tagged variant
        try:
            return d[cls._meta.tag]
        except KeyError:
            raise DeserializationError('expected tag {!r}'.format(cls._meta.tag))

    @classmethod
    def _from_dict_transform_data(cls, d, tag):
        # Externally tagged variant
        if cls._meta.tag is True:
            return d[tag]
        # Adjacently tagged variant
        elif cls._meta.content:
            try:
                return d[cls._meta.content]
            except KeyError:
                raise DeserializationError(
                    'expected adjacently tagged data under key {!r}'.format(cls._meta.content)
                )
        # Internally tagged variant
        return {k: v for k, v in d.items() if k != cls._meta.tag}

    @classmethod
    def _from_dict_transform(cls, d):
        """
        Transform the tagged content so that it can be deserialized.
        """
        tag = cls._from_dict_transform_get_tag(d)
        variant = cls._meta.variant_for(tag)

        if not variant:
            raise DeserializationError('no variant found for tag {!r}'.format(tag))

        return variant, cls._from_dict_transform_data(d, tag)

    @classmethod
    def _to_dict_transform(cls, d, dict):
        """
        Transform the untagged content into tagged data.
        """
        if cls._meta.tag:
            variant_tag = cls._meta.tag_for(cls)

            # Externally tagged variant
            if cls._meta.tag is True:
                d = dict(((variant_tag, d),))
            # Adjacently tagged variant
            elif cls._meta.content:
                d = dict(((cls._meta.tag, variant_tag), (cls._meta.content, d)))
            # Internally tagged variant
            else:
                d_new = dict(((cls._meta.tag, variant_tag),))
                d_new.update(d)
                d = d_new

        return d

    @classmethod
    def _from_dict(cls, d, strict=True):
        """
        Convert a dictionary to an instance of this Model.
        """
        self = cls.__new__(cls)

        for name, field in cls._fields.items():
            value = self._deserialize_field(field, d[field.name]) if field.name in d else None
            setattr(self, name, value)

        if strict:
            allowed = cls._fields.names()
            unknown = [key for key in d.keys() if key not in allowed]

            if unknown:
                raise DeserializationError(
                    'unexpected dictionary key{} {}'.format(
                        '' if len(unknown) == 1 else 's',
                        ', '.join('{!r}'.format(k) for k in unknown)
                    )
                )

        with map_errors(DeserializationError):
            self.normalize_all()
            self.validate_all()

        return self

    @classmethod
    def from_dict(cls, d, strict=True):
        """
        Convert a dictionary to an instance of this Model.

        Args:
            d (dict): a serialized version of this Model.
            strict (bool): if set to False then no exception will be raised when
                unknown dictionary keys are present.

        Returns:
            Model: an instance of this Model.
        """
        if cls._meta.is_owner(cls):
            # Externally/internally/adjacently tagged variant
            if cls._meta.tag:
                variant, d = cls._from_dict_transform(d)

                if variant != cls:
                    return variant.from_dict(d, strict=strict)
                else:
                    return cls._from_dict(d, strict=strict)

            # Untagged variant
            elif cls._meta.tag is False:
                # Try each variant in turn until one succeeds
                for variant in cls._meta.variants():
                    try:
                        if variant != cls:
                            return variant.from_dict(d, strict=strict)
                        else:
                            return cls._from_dict(d, strict=strict)
                    except DeserializationError:
                        pass

                raise DeserializationError('no variant succeeded deserialization')

        return cls._from_dict(d, strict=strict)

    @classmethod
    def from_json(cls, s, strict=True, **kwargs):
        """
        Load the Model from a JSON string.

        Args:
            s (str): the JSON string.
            strict (bool): if set to False then no exception will be raised when
                unknown dictionary keys are present.
            **kwargs: extra keyword arguments to pass directly to `json.loads`.

        Returns:
            Model: an instance of this Model.
        """
        return cls.from_dict(json.loads(s, **kwargs), strict=strict)

    def to_dict(self, dict=None):
        """
        Convert this Model to a dictionary.

        Args:
            dict (type): the class of the deserialized dictionary. This defaults
                to an `OrderedDict` so that the fields will be returned in the
                order they were defined on the Model.

        Returns:
            dict: the Model serialized as a dictionary.
        """
        if dict is None:
            dict = OrderedDict

        d = dict()

        for name, field in self._fields.items():
            try:
                d[field.name] = self._serialize_field(field, getattr(self, name))
            except SkipSerialization:
                pass

        d = self._to_dict_transform(d, dict=dict)

        return d

    def to_json(self, dict=None, **kwargs):
        """
        Dump the Model as a JSON string.

        Args:
            dict (type): the class of the deserialized dictionary that is passed
                to `json.dumps`.
            **kwargs: extra keyword arguments to pass directly to `json.dumps`.

        Returns:
            str: a JSON representation of this Model.
        """
        return json.dumps(self.to_dict(dict=dict), **kwargs)
