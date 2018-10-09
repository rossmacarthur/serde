"""
Defines the core Serde Model and the ModelType metaclass.
"""

import json
from collections import OrderedDict

from .error import DeserializationError, SerializationError, ValidationError
from .field import Field
from .util import create_function


class Fields(OrderedDict):
    """
    An OrderedDict with additional useful methods for use on fields.
    """

    def __getattr__(self, name):
        """
        Return keys in the dictionary like attributes.

        Args:
            name (str): the attribute lookup.

        Returns:
            Field: the field value in the dictionary.
        """
        try:
            return self[name]
        except KeyError:
            return super().__getattribute__(name)


class ModelType(type):
    """
    A metaclass for Models.

    This metaclass pulls `~serde.field.Field` attributes off the defined class
    and uses them to construct unique __init__, __eq__, and __hash__ methods on
    the `Model`.
    """

    def __new__(cls, cname, bases, attrs):
        """
        Create a new `Model` type, overriding the relevant methods.

        Args:
            cname (str): the class name.
            bases (tuple): the classes's base classes.
            attrs (dict): the attributes for this class.

        Returns:
            Model: a new Model.
        """
        # Split the attrs into Fields and non-Fields.
        fields = []
        final_attrs = OrderedDict()

        for name, value in attrs.items():
            if isinstance(value, Field):
                fields.append((name, value))
            else:
                final_attrs[name] = value

        # Get the most recent base class __fields__ attribute if it exists.
        if len(bases) > 0 and hasattr(bases[-1], '__fields__'):
            fields += list(bases[-1].__fields__.items())

        # Order the fields by the Field ID this gets the order that they are
        # defined on the Model.
        fields = Fields(sorted(fields, key=lambda x: x[1].id))

        # Generate the __init__ method for the Model.
        final_attrs['__init__'] = cls.create___init__(fields)

        # Add the fields to the Model.
        final_attrs['__fields__'] = fields

        return super().__new__(cls, cname, bases, final_attrs)

    @staticmethod
    def create___init__(fields):
        """
        Create the __init__ method for the `Model`.

        The generated function will simply take the actual field values as
        parameters and set them as attributes on the instance. It will also
        validate the field values.

        Args:
            fields (OrderedDict): the Model's fields.

        Returns:
            callable: the __init__ method.
        """
        parameters = ['self']
        setters = []
        defaults = []

        for name, field in fields.items():
            parameters.append('{name}=None'.format(name=name))
            setters.append('    self.{name} = {name}'.format(name=name))

            if field.default is not None:
                setter = '        self.{name} = self.__fields__.{name}.default'.format(name=name)

                if callable(field.default):
                    setter += '(self)'

                defaults.extend(['', '    if self.{name} is None:'.format(name=name), setter])

        definition = 'def __init__({parameters}):'.format(parameters=', '.join(parameters))
        lines = setters + defaults + ['', '    self.validate()']

        return create_function(definition, lines)


class Model(metaclass=ModelType):
    """
    The base Model to be subclassed.

    Models are containers for `~serde.field.Field` elements. Models can be
    serialized to and from dictionaries with `~Model.to_dict` and
    `~Model.from_dict` and to and from JSON with `~Model.to_json` and
    `~Model.from_json`.

    Fields are serialized, deserialized, and validated according to their
    specification, and you can easily create your own Field by subclassing
    `~serde.field.Field`. Models also validate input data using the validators
    specified on the Field classes.

    The `Model.__init__` method will be auto-generated from the Field
    attributes.

    Examples:

        A simple user model

        .. testsetup::

            from serde import Model, Int, Str

        .. testcode::

            class User(Model):
                name = Str()
                age = Int(required=False)

            user = User('Benedict Cumberbatch', age=42)
            assert user.name == 'Benedict Cumberbatch'
            assert user.age == 42

        You can even subclass subclassed `Model` objects.

        .. testcode::

            class SuperUser(User):
                level = Int(default=10)

            user = SuperUser('Benedict Cumberbatch', age=42)
            assert user.name == 'Benedict Cumberbatch'
            assert user.age == 42
            assert user.level == 10
    """

    def __eq__(self, other):
        """
        Whether two Models are the same.
        """
        return (isinstance(other, self.__class__) and
                all(getattr(self, name) == getattr(other, name)
                    for name in self.__fields__.keys()))

    def __hash__(self):
        """
        Return a hash value for this Model.
        """
        values = []

        for name in self.__fields__.keys():
            value = getattr(self, name)

            if isinstance(value, list):
                values.append(frozenset(value))
            else:
                values.append(value)

        return hash(tuple(values))

    def validate(self):
        """
        Validate this Model.

        Raises:
            `~serde.error.ValidationError`: when a Field value is invalid.
        """
        for name, field in self.__fields__.items():
            value = getattr(self, name)

            if value is None:
                if field.required is not True:
                    continue

                raise ValidationError('{!r} is required'.format(name))

            try:
                field.validate(value)
                for validator in field.validators:
                    validator(self, value)
            except ValidationError:
                raise
            except Exception as e:
                raise ValidationError(str(e))

    @classmethod
    def from_dict(cls, d):
        """
        Convert a dictionary to an instance of this Model.

        Args:
            d (dict): a serialized version of this Model.

        Returns:
            Model: an instance of this Model.

        Raises:
            `~serde.error.DeserializationError`: when a Field value can not be
                deserialized or there are unknown dictionary keys.
            `~serde.error.ValidationError`: when a Field value is invalid.

        Examples:

            A simple user model deserialized from a dictionary

            .. testsetup::

                from serde import Model, Int, Str

            .. testcode::

                class User(Model):
                    name = Str()
                    age = Int(required=False)

                user = User.from_dict({
                    'name': 'Benedict Cumberbatch',
                    'age': 42
                })
                assert user.name == 'Benedict Cumberbatch'
                assert user.age == 42
        """
        kwargs = {}

        for name_, field in cls.__fields__.items():
            if field.name:
                name = field.name(cls, name_) if callable(field.name) else field.name
            else:
                name = name_

            if name in d:
                try:
                    value = field.deserialize(d.pop(name))
                except DeserializationError:
                    raise
                except Exception as e:
                    raise DeserializationError(str(e))

                kwargs[name_] = value

        if d:
            unknowns = ', '.join('{!r}'.format(k) for k in d.keys())
            plural = '' if len(d.keys()) == 1 else 's'
            raise DeserializationError('unknown dictionary key{} {}'.format(plural, unknowns))

        return cls(**kwargs)

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

    def to_dict(self):
        """
        Convert this Model to a dictionary.

        Returns:
            dict: the Model serialized as a dictionary.

        Raises:
            `~serde.error.SerializationError`: when a Field value cannot be
                serialized.

        Examples:

            A simple user model serialized as a dictionary

            .. testsetup::

                from serde import Model, Int, Str

            .. testcode::

                class User(Model):
                    name = Str()
                    age = Int(required=False)

                user = User('Benedict Cumberbatch', age=42)
                assert user.to_dict() == {'name': 'Benedict Cumberbatch', 'age': 42}
        """
        result = OrderedDict()

        for name, field in self.__fields__.items():
            value = getattr(self, name)

            if field.name:
                name = field.name(self, name) if callable(field.name) else field.name

            if value is None and field.required is not True:
                continue

            try:
                result[name] = field.serialize(value)
            except SerializationError:
                raise
            except Exception as e:
                raise SerializationError(str(e))

        return result

    def to_json(self, **kwargs):
        """
        Dump the Model as a JSON string.

        Args:
            **kwargs: extra keyword arguments to pass directly to `json.dumps`.

        Returns:
            str: a JSON representation of this Model.
        """
        return json.dumps(self.to_dict(), **kwargs)
