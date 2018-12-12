"""
This module defines the core Model class.

`Models <Model>` are containers for `Fields <serde.field>`. Models can be
serialized to and from dictionaries with `~Model.to_dict`, `~Model.from_dict`
and to and from data formats such as JSON with `~Model.to_json` and
`~Model.from_json`.

When Models are subclassed, all `Fields <serde.field.Field>` attributes are
pulled off and used to uniquely determine the operation of instantiation,
serialization, deserialization, and validation methods for the Model.

Consider a simple example of a `Pet`, with a `name` attribute.

::

    >>> from serde import Model, field

    >>> class Pet(Model):
    ...     name = field.Str()

This can be subclassed and the subclassed Model will have all the fields of the
parent.

::

    >>> class Dog(Pet):
    ...     hates_cats = field.Bool(default=True)

    >>> max = Dog('Max', hates_cats=False)
    >>> max.name
    'Max'
    >>> max.hates_cats
    False
    >>> max._fields.name
    <serde.field.Str object at ...>

Models can be nested using the `~serde.field.Nested` Field. By default the
`~Model.to_dict()` and `~Model.from_dict()` methods will used for serialization
and deserialization.

::

    >>> class Owner(Model):
    ...     name = field.Str()
    ...     pet = field.Nested(Pet, required=False)

    >>> jeffery = Owner('Jeffery', pet=Dog('Brutus'))
    >>> jeffery.name
    'Jeffery'
    >>> jeffery.pet
    Dog(name='Brutus', hates_cats=True)


Model serialization and deserialization is done using the relevant methods. For
example to serialize an `Owner` to JSON we would call the `Model.to_json()`
method.

::

    >>> jeffery.to_json()
    '{"name": "Jeffery", "pet": {"name": "Brutus", "hates_cats": true}}'

To deserialize from JSON we use the `Model.from_json()` method.

::

    >>> Owner.from_json('{"name": "George"}')
    Owner(name='George')

"""

import json
from collections import OrderedDict
from functools import wraps

from six import with_metaclass

from serde.error import DeserializationError, SerdeError, SerializationError, ValidationError
from serde.field import Field
from serde.util import dict_partition, try_import, zip_until_right


toml = try_import('toml')
yaml = try_import('ruamel.yaml')


__all__ = ['Model']


def requires_module(module, package=None):
    """
    Returns a decorator that handles missing optional modules.

    Args:
        module (str): the module to check is imported.
        package (str): the PyPI package name. This is only used for the
            exception message.

    Returns:
        function: the real decorator.
    """
    def real_decorator(f):

        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not globals()[module]:
                raise SerdeError(
                    'this feature requires the {!r} package to be installed'
                    .format(package or module)
                )

            return f(*args, **kwargs)

        return decorated_function

    return real_decorator


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
    def real_decorator(f):

        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except error as e:
                e.add_context(value=value, field=field, model=model)
                raise
            except Exception as e:
                raise error(str(e) or repr(e), cause=e, value=value, field=field, model=model)

        return decorated_function

    return real_decorator


def handle_field_errors(error):
    """
    Returns a decorator that handles exceptions from a Field function.

    The decorated function needs to take the Model class or instance as the
    first parameter, the Field instance as the second parameter, and the Field
    value as the third parameter.

    Args:
        error (SerdeError): a SerdeError to wrap any generic exceptions that are
            generated by the Field function.

    Returns:
        function: the real decorator.
    """
    def real_decorator(f):

        @wraps(f)
        def decorated_function(*args, **kwargs):
            return map_errors(error, *args[:3])(f)(*args, **kwargs)

        return decorated_function

    return real_decorator


class Fields(OrderedDict):
    """
    An OrderedDict with that allows value access with dot notation.
    """

    def __getattr__(self, name):
        """
        Return values in the dictionary using attribute access with keys.

        Args:
            name (str): the dictionary key.

        Returns:
            Field: the field value in the dictionary.
        """
        try:
            return self[name]
        except KeyError:
            return super(Fields, self).__getattribute__(name)


class ModelType(type):
    """
    A metaclass for Models.

    This metaclass pulls `~serde.field.Field` attributes off the defined class
    and adds them as a `_fields` attribute to the resulting object. Model
    methods use the `_fields` attribute to construct, validate, and convert
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

        return super(ModelType, cls).__new__(cls, cname, bases, final_attrs)


class Model(with_metaclass(ModelType, object)):
    """
    The base Model to be subclassed.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a new Model.

        Args:
            *args: positional arguments values for each Fields on the Model. If
                these are given they will be interpreted as corresponding to the
                Fields in the order the Fields are defined on the Model.
            **kwargs: keyword argument values for each Field on the Model.
        """
        try:
            named_args = list(zip_until_right(self._fields.keys(), args))
        except ValueError:
            raise SerdeError(
                '__init__() takes a maximum of {!r} positional arguments but {!r} were given'
                .format(len(self._fields) + 1, len(args) + 1)
            )

        for name, value in named_args:
            if name in kwargs:
                raise SerdeError(
                    '__init__() got multiple values for keyword argument {!r}'
                    .format(name)
                )

            kwargs[name] = value

        for name, field in self._fields.items():
            value = kwargs.pop(name, None)

            if value is None and field.default is not None:
                if callable(field.default):
                    value = field.default()
                else:
                    value = field.default

            setattr(self, name, value)

        if kwargs:
            raise SerdeError(
                'invalid keyword argument{} {}'.format(
                    '' if len(kwargs.keys()) == 1 else 's',
                    ', '.join('{!r}'.format(k) for k in kwargs.keys())
                )
            )

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

    @handle_field_errors(SerializationError)
    def _serialize_field(self, field, value):
        """
        Serialize a field on this Model.

        Args:
            field (Field): the field to serialize.
            value: the value to serialize.

        Raises:
            `~serde.error.SerializationError`: when the serialization fails.
        """
        return field._serialize(value)

    @classmethod
    @handle_field_errors(DeserializationError)
    def _deserialize_field(cls, field, value):
        """
        Deserialize a field on this Model.

        Args:
            field (Field): the field to deserialize.
            value: the value to deserialize.

        Raises:
            `~serde.error.DeserializationError`: when the deserialization fails.
        """
        return field._deserialize(value)

    @handle_field_errors(ValidationError)
    def _validate_field(self, field, value):
        """
        Validate a field on this Model.

        Args:
            field (Field): the field to validate.
            value: the value to validate.

        Raises:
            `~serde.error.ValidationError`: when the validation fails.
        """
        field._validate(value)

    def validate_all(self):
        """
        Validate all Fields on this Model, and the Model itself.

        This is called by the Model constructor, so this is only needed if you
        modify attributes directly and want to revalidate the Model.
        """
        for name, field in self._fields.items():
            value = getattr(self, name)

            if value is None:
                if field.required:
                    raise ValidationError('{!r} is required'.format(name), field=field, model=self)
            else:
                self._validate_field(field, value)

        map_errors(ValidationError, model=self)(self.validate)()

    def validate(self):
        """
        Validate this Model.

        Override this method to add any additional validation to the Model.

        ::

            >>> class Owner(Model):
            ...     cats_name = field.Str(required=False)
            ...     dogs_name = field.Str(required=False)
            ...
            ...     def validate(self):
            ...         msg = 'No one is a cat *and* a dog person!'
            ...         assert not (self.cats_name and self.dogs_name), msg
            ...

            >>> owner = Owner(cats_name='Luna', dogs_name='Max')
            Traceback (most recent call last):
                ...
            serde.error.ValidationError: No one is a cat *and* a dog person!
        """
        pass

    @classmethod
    def from_dict(cls, d, strict=True):
        """
        Convert a dictionary to an instance of this Model.

        The given dictionary will be consumed by this operation.

        Args:
            d (dict): a serialized version of this Model.
            strict (bool): if set to False then no exception will be raised when
                unknown dictionary keys are present.

        Returns:
            Model: an instance of this Model.

        Raises:
            `~serde.error.DeserializationError`: when a Field value can not be
                deserialized or there are unknown dictionary keys.
            `~serde.error.ValidationError`: when a Field value is invalid.
        """
        kwargs = OrderedDict()

        for name, field in cls._fields.items():
            if field.name in d:
                value = d.pop(field.name)
                kwargs[name] = cls._deserialize_field(field, value)
            elif field.required:
                raise DeserializationError(
                    'dictionary key {!r} is missing'.format(field.name),
                    field=field,
                    model=cls
                )

        if strict and d:
            raise DeserializationError(
                'unknown dictionary key{} {}'.format(
                    '' if len(d.keys()) == 1 else 's',
                    ', '.join('{!r}'.format(k) for k in d.keys())
                ),
                model=cls
            )

        return cls(**kwargs)

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

    @classmethod
    @requires_module('toml')
    def from_toml(cls, s, strict=True, **kwargs):
        """
        Load the Model from a TOML string.

        Args:
            s (str): the TOML string.
            strict (bool): if set to False then no exception will be raised when
                unknown dictionary keys are present.
            **kwargs: extra keyword arguments to pass directly to `toml.loads`.

        Returns:
            Model: an instance of this Model.
        """
        return cls.from_dict(toml.loads(s, **kwargs), strict=strict)

    @classmethod
    @requires_module('yaml', package='ruamel.yaml')
    def from_yaml(cls, s, strict=True, **kwargs):
        """
        Load the Model from a YAML string.

        Args:
            s (str): the YAML string.
            strict (bool): if set to False then no exception will be raised when
                unknown dictionary keys are present.
            **kwargs: extra keyword arguments to pass directly to
                `yaml.safe_load`.

        Returns:
            Model: an instance of this Model.
        """
        return cls.from_dict(yaml.safe_load(s, **kwargs), strict=strict)

    def to_dict(self, dict=None):
        """
        Convert this Model to a dictionary.

        Args:
            dict (type): the class of the deserialized dictionary. This defaults
                to an `OrderedDict` so that the fields will be returned in the
                order they were defined on the Model.

        Returns:
            dict: the Model serialized as a dictionary.

        Raises:
            `~serde.error.SerializationError`: when a Field value cannot be
                serialized.
        """
        if dict is None:
            dict = OrderedDict

        result = dict()

        for name, field in self._fields.items():
            value = getattr(self, name)

            if field.required or value is not None:
                result[field.name] = self._serialize_field(field, value)

        return result

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

    @requires_module('toml')
    def to_toml(self, dict=None, **kwargs):
        """
        Dump the Model as a TOML string.

        Args:
            dict (type): the class of the deserialized dictionary that is passed
                to `toml.dumps`.
            **kwargs: extra keyword arguments to pass directly to `toml.dumps`.

        Returns:
            str: a TOML representation of this Model.
        """
        return toml.dumps(self.to_dict(dict=dict), **kwargs)

    @requires_module('yaml', package='ruamel.yaml')
    def to_yaml(self, dict=None, **kwargs):
        """
        Dump the Model as a YAML string.

        Args:
            dict (type): the class of the deserialized dictionary that is passed
                to `yaml.dump`.
            **kwargs: extra keyword arguments to pass directly to `yaml.dump`.

        Returns:
            str: a YAML representation of this Model.
        """
        return yaml.dump(self.to_dict(dict=dict), **kwargs)
