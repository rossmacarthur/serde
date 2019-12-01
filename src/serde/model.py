"""
This module defines the core `~serde.Model` class.
"""

import inspect
import json
from collections import OrderedDict

from six import add_metaclass

from serde.exceptions import (
    ContextError,
    DeserializationError,
    InstantiationError,
    NormalizationError,
    ValidationError,
    map_errors,
)
from serde.fields import Field, _resolve_to_field_instance
from serde.utils import dict_partition, zip_until_right


__all__ = ['Model']


class Fields(OrderedDict):
    """
    An `~collections.OrderedDict` that allows value access with dot notation.
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
    A metaclass for a `Model`.

    This metaclass pulls `~serde.fields.Field` attributes off the defined class.
    These can be accessed using the ``__fields__`` attribute on the class. Model
    methods use the ``__fields__`` attribute to instantiate, serialize,
    deserialize, normalize, and validate models.
    """

    @staticmethod
    def _pop_meta(attrs):
        """
        Handle the Meta class attributes.
        """
        abstract = False
        tag = None

        if 'Meta' in attrs:
            meta = attrs.pop('Meta').__dict__
            if 'abstract' in meta:
                abstract = meta['abstract']
            if 'tag' in meta:
                tag = meta['tag']

        return abstract, tag

    def __new__(cls, cname, bases, attrs):
        """
        Create a new `Model` class.

        Args:
            cname (str): the class name.
            bases (tuple): the base classes.
            attrs (dict): the attributes for this class.

        Returns:
            Model: a new model class.
        """
        parent = None
        abstract, tag = cls._pop_meta(attrs)

        # Split the attrs into Fields and non-Fields.
        fields, final_attrs = dict_partition(attrs, lambda k, v: isinstance(v, Field))

        if '__annotations__' in attrs:
            if fields:
                raise ContextError(
                    'simultaneous use of annotations and class attributes '
                    'for Field definitions'
                )
            fields = OrderedDict(
                (k, _resolve_to_field_instance(v))
                for k, v in attrs.pop('__annotations__').items()
            )

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
                fields.update(
                    [
                        (name, field)
                        for name, field in base.__fields__.items()
                        if name not in attrs
                    ]
                )
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
        """
        Whether this model class is abstract or not.
        """
        return cls._abstract

    @property
    def __parent__(cls):
        """
        This model class's parent model class.
        """
        return cls._parent

    @property
    def __fields__(cls):
        """
        A map of attribute name to field instance.
        """
        return cls._fields.copy()

    @property
    def __tag__(cls):
        """
        The model class's tag (or None).
        """
        return cls._tag

    @property
    def __tags__(cls):
        """
        The model class's tag and all parent class's tags.
        """
        return cls._tags[:]


@add_metaclass(ModelType)
class Model(object):
    """
    The base model.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a new model.

        Args:
            *args: positional arguments values for each field on the model. If
                these are given they will be interpreted as corresponding to the
                fields in the order they are defined on the model class.
            **kwargs: keyword argument values for each field on the model.
        """
        if self.__class__.__abstract__:
            raise InstantiationError(
                'unable to instantiate abstract Model {!r}'.format(
                    self.__class__.__name__
                )
            )

        try:
            for name, value in zip_until_right(self.__class__.__fields__.keys(), args):
                if name in kwargs:
                    raise InstantiationError(
                        '__init__() got multiple values '
                        'for keyword argument {!r}'.format(name)
                    )
                kwargs[name] = value
        except ValueError:
            raise InstantiationError(
                '__init__() takes a maximum of {!r} positional arguments'
                ' but {!r} were given'.format(
                    len(self.__class__.__fields__) + 1, len(args) + 1
                )
            )

        for field in self.__class__.__fields__.values():
            field._instantiate_with(self, kwargs)

        if kwargs:
            raise InstantiationError(
                'invalid keyword argument{} {}'.format(
                    '' if len(kwargs.keys()) == 1 else 's',
                    ', '.join('{!r}'.format(k) for k in kwargs.keys()),
                )
            )

        with map_errors(InstantiationError):
            self._normalize()
            self._validate()

    def __eq__(self, other):
        """
        Whether two models are the same.
        """
        return isinstance(other, self.__class__) and all(
            getattr(self, name) == getattr(other, name)
            for name in self.__class__.__fields__.keys()
        )

    def __hash__(self):
        """
        Return a hash value for this model.
        """
        return hash(
            tuple(
                (name, getattr(self, name)) for name in self.__class__.__fields__.keys()
            )
        )

    def __repr__(self):
        """
        Return the canonical string representation of this model.
        """
        return '<{module}.{name} model at 0x{id:x}>'.format(
            module=self.__class__.__module__,
            name=getattr(self.__class__, '__qualname__', self.__class__.__name__),
            id=id(self),
        )

    def to_dict(self):
        """
        Convert this model to a dictionary.

        Returns:
            ~collections.OrderedDict: the model serialized as a dictionary.
        """
        d = OrderedDict()

        for field in self.__class__.__fields__.values():
            d = field._serialize_with(self, d)

        for tag in reversed(self.__class__.__tags__):
            d = tag._serialize_with(self, d)

        return d

    def to_json(self, **kwargs):
        """
        Dump the model as a JSON string.

        Args:
            **kwargs: extra keyword arguments to pass directly to `json.dumps`.

        Returns:
            str: a JSON representation of this model.
        """
        return json.dumps(self.to_dict(), **kwargs)

    @classmethod
    def from_dict(cls, d):
        """
        Convert a dictionary to an instance of this model.

        Args:
            d (dict): a serialized version of this model.

        Returns:
            Model: an instance of this model.
        """
        model = cls.__new__(cls)

        model_cls = None
        while model.__class__.__tag__ and model_cls is not model.__class__:
            model_cls = model.__class__
            model, d = model.__class__.__tag__._deserialize_with(model, d)

        for field in reversed(model.__class__.__fields__.values()):
            model, d = field._deserialize_with(model, d)

        with map_errors(DeserializationError):
            model._normalize()
            model._validate()

        return model

    @classmethod
    def from_json(cls, s, **kwargs):
        """
        Load the model from a JSON string.

        Args:
            s (str): the JSON string.
            **kwargs: extra keyword arguments to pass directly to `json.loads`.

        Returns:
            Model: an instance of this model.
        """
        return cls.from_dict(json.loads(s, **kwargs))

    def _normalize(self):
        """
        Normalize all fields on this model, and the model itself.

        This is called by the model constructor and on deserialization, so this
        is only needed if you modify attributes directly and want to renormalize
        the model instance.
        """
        for field in self.__class__.__fields__.values():
            field._normalize_with(self)

        with map_errors(NormalizationError):
            self.normalize()

    def normalize(self):
        """
        Normalize this model.

        Override this method to add any additional normalization to the model.
        This will be called after all fields have been normalized.
        """
        pass

    def _validate(self):
        """
        Validate all fields on this model, and the model itself.

        This is called by the model constructor and on deserialization, so this
        is only needed if you modify attributes directly and want to revalidate
        the model instance.
        """
        for field in self.__class__.__fields__.values():
            field._validate_with(self)

        with map_errors(ValidationError):
            self.validate()

    def validate(self):
        """
        Validate this model.

        Override this method to add any additional validation to the model. This
        will be called after all fields have been validated.
        """
        pass
