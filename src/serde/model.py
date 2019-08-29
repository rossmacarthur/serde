"""
This module defines the core `~serde.model.Model` class.
"""

import inspect
import json
from collections import OrderedDict

from six import add_metaclass

from serde.exceptions import (
    DeserializationError,
    InstantiationError,
    NormalizationError,
    ValidationError,
    map_errors
)
from serde.fields import Field
from serde.utils import dict_partition, zip_until_right


__all__ = ['Model']


class Fields(OrderedDict):
    """
    An OrderedDict that allows value access with dot notation.
    """

    def __getattr__(self, name):
        """
        Return values in the dictionary using attribute access with keys.
        """
        try:
            return self[name]
        except KeyError:
            return super(Fields, self).__getattribute__(name)


class ModelType(type):
    """
    A metaclass for Models.

    This metaclass pulls `~serde.fields.Field` attributes off the defined class.
    The can be accessed using the `__fields__` attribute on the class or
    instance. Model methods use the `__fields__` attribute to construct,
    validate, and convert Models between data formats.
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
        abstract = False
        tag = None
        parent = None

        # Handle the Meta class.
        if 'Meta' in attrs:
            meta = attrs.pop('Meta').__dict__
            if 'abstract' in meta:
                abstract = meta['abstract']
            if 'tag' in meta:
                tag = meta['tag']

        # Split the attrs into Fields and non-Fields.
        fields, final_attrs = dict_partition(attrs, lambda k, v: isinstance(v, Field))

        # Create our Model class.
        model_cls = super(ModelType, cls).__new__(cls, cname, bases, final_attrs)

        # Bind the Model to the Fields.
        for name, field in fields.items():
            field._bind(model_cls, name=name)
        # Bind the Model to the Tags.
        if tag:
            tag._bind(model_cls)
            tags = [tag]
        else:
            tags = []

        # Loop though the base classes, and pull Fields and Tags off.
        for base in inspect.getmro(model_cls)[1:]:
            if getattr(base, '__class__', None) is cls:
                fields.update([
                    (name, field) for name, field in base.__fields__.items()
                    if name not in attrs
                ])
                tags = base.__tags__ + tags

                if not parent:
                    parent = base

        # Assign all the things to the Model!
        model_cls._abstract = abstract
        model_cls._parent = parent
        model_cls._fields = Fields(sorted(fields.items(), key=lambda x: x[1].id))
        model_cls._tag = tag
        model_cls._tags = tags

        return model_cls

    @property
    def __abstract__(cls):
        return cls._abstract

    @property
    def __parent__(cls):
        return cls._parent

    @property
    def __fields__(cls):
        return cls._fields.copy()

    @property
    def __tag__(cls):
        return cls._tag

    @property
    def __tags__(cls):
        return cls._tags[:]


@add_metaclass(ModelType)
class Model(object):
    """
    The base Model.
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
        if self.__class__.__abstract__:
            raise InstantiationError(
                'unable to instantiate abstract Model {!r}'
                .format(self.__class__.__name__)
            )

        try:
            for name, value in zip_until_right(self.__class__.__fields__.keys(), args):
                if name in kwargs:
                    raise InstantiationError(
                        '__init__() got multiple values for keyword argument {!r}'
                        .format(name),
                    )
                kwargs[name] = value
        except ValueError:
            raise InstantiationError(
                '__init__() takes a maximum of {!r} positional arguments but {!r} were given'
                .format(len(self.__class__.__fields__) + 1, len(args) + 1),
            )

        for name in self.__class__.__fields__.keys():
            if name in kwargs:
                setattr(self, name, kwargs.pop(name))

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
                for name in self.__class__.__fields__.keys()
            )
        )

    def __hash__(self):
        """
        Return a hash value for this Model.
        """
        return hash(tuple((name, getattr(self, name)) for name in self.__class__.__fields__.keys()))

    def __repr__(self):
        """
        Return the canonical string representation of this Model.
        """
        return '<{module}.{name} model at 0x{id:x}>'.format(
            module=self.__class__.__module__,
            name=getattr(self.__class__, '__qualname__', self.__class__.__name__),
            id=id(self)
        )

    def to_dict(self):
        """
        Convert this Model to a dictionary.

        Returns:
            dict: the Model serialized as a dictionary.
        """
        d = OrderedDict()

        for field in self.__class__.__fields__.values():
            d = field._serialize_with(self, d)

        for tag in reversed(self.__class__.__tags__):
            d = tag._serialize_with(self, d)

        return d

    def to_json(self, **kwargs):
        """
        Dump the Model as a JSON string.

        Args:
            **kwargs: extra keyword arguments to pass directly to `json.dumps`.

        Returns:
            str: a JSON representation of this Model.
        """
        return json.dumps(self.to_dict(), **kwargs)

    @classmethod
    def from_dict(cls, d):
        """
        Convert a dictionary to an instance of this Model.

        Args:
            d (dict): a serialized version of this Model.

        Returns:
            Model: an instance of this Model.
        """
        model = cls.__new__(cls)

        model_cls = None
        while model.__class__.__tag__ and model_cls is not model.__class__:
            model_cls = model.__class__
            model, d = model.__class__.__tag__._deserialize_with(model, d)

        for field in reversed(model.__class__.__fields__.values()):
            model, d = field._deserialize_with(model, d)

        with map_errors(DeserializationError):
            model.normalize_all()
            model.validate_all()

        return model

    @classmethod
    def from_json(cls, s, **kwargs):
        """
        Load the Model from a JSON string.

        Args:
            s (str): the JSON string.
            **kwargs: extra keyword arguments to pass directly to `json.loads`.

        Returns:
            Model: an instance of this Model.
        """
        return cls.from_dict(json.loads(s, **kwargs))

    def normalize_all(self):
        """
        Normalize all Fields on this Model, and the Model itself.

        This is called by the Model constructor and on deserialization, so this
        is only needed if you modify attributes directly and want to renormalize
        the Model.
        """
        for field in self.__class__.__fields__.values():
            field._normalize_with(self)

        with map_errors(NormalizationError):
            self.normalize()

    def normalize(self):
        """
        Normalize this Model.

        Override this method to add any additional normalization to the Model.
        This will be called after all Fields have been normalized.
        """
        pass

    def validate_all(self):
        """
        Validate all Fields on this Model, and the Model itself.

        This is called by the Model constructor, so this is only needed if you
        modify attributes directly and want to revalidate the Model.
        """
        for field in self.__class__.__fields__.values():
            field._validate_with(self)

        with map_errors(ValidationError):
            self.validate()

    def validate(self):
        """
        Validate this Model.

        Override this method to add any additional validation to the Model. This
        will be called after all Fields have been validated.
        """
        pass
