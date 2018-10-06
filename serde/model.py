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

        # Order the fields by the base Fields then by Field counter, this gets
        # the order that they are defined in their class, with args first then
        # kwargs.
        def key(x):
            name, field = x
            return (field.optional, field.default is not None, field.counter)

        fields = Fields(sorted(fields, key=key))

        # Create all the necessary functions for a ModelType. This will override
        # user defined methods with no warning.
        for func_name in cls.__dict__:
            if func_name.startswith('create_'):
                final_attrs[func_name[7:]] = getattr(cls, func_name)(fields)

        # Finally, add the fields to the Model.
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
            if field.optional or field.default is not None:
                parameters.append('{name}=None'.format(name=name))
            else:
                parameters.append(name)

            setters.append('    self.{name} = {name}'.format(name=name))

            if field.default is not None:
                setter = '        self.{name} = self.__fields__.{name}.default'.format(name=name)

                if callable(field.default):
                    setter += '(self)'

                defaults.extend(['', '    if self.{name} is None:'.format(name=name), setter])

        definition = 'def __init__({parameters}):'.format(parameters=', '.join(parameters))
        lines = setters + defaults + ['', '    self.validate()']

        return create_function(definition, lines)

    @staticmethod
    def create___eq__(fields):
        """
        Create the __eq__ method for the `Model`.

        This method simply checks if the class is the same type and the field
        values are equal.

        Args:
            fields (OrderedDict): the class's fields.

        Returns:
            callable: the __eq__ method.
        """
        definition = 'def __eq__(self, other):'
        lines = ['    return (isinstance(other, self.__class__)']
        lines.extend(
            '   and self.{name} == other.{name}'.format(name=name) for name in fields.keys()
        )
        lines.append('    )')
        return create_function(definition, lines)

    @staticmethod
    def create___hash__(fields):
        """
        Create the __hash__ method for the `Model`.

        Args:
            fields (OrderedDict): the class's fields.

        Returns:
            callable: the __hash__ method.
        """
        definition = 'def __hash__(self):'
        lines = ['    return hash((']
        lines.extend(
            '        frozenset(self.{name}) if isinstance(self.{name}, list) else self.{name},'
            .format(name=name) for name in fields.keys()
        )
        lines.append('    ))')

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
    attributes. Required Fields will become arguments and optional or default
    Fields will become keyword arguments.

    Examples:

        A simple user model

        .. testsetup::

            from serde import Model, Integer, String

        .. testcode::

            class User(Model):
                name = String()
                age = Integer(optional=True)

            user = User('Benedict Cumberbatch', age=42)
            assert user.name == 'Benedict Cumberbatch'
            assert user.age == 42

        You can even subclass subclassed `Model` objects.

        .. testcode::

            class SuperUser(User):
                level = Integer(default=10)

            user = SuperUser('Benedict Cumberbatch', age=42)
            assert user.name == 'Benedict Cumberbatch'
            assert user.age == 42
            assert user.level == 10
    """

    def validate(self):
        """
        Validate this Model.

        Raises:
            `~serde.error.ValidationError`: when a Field value is invalid.
        """
        for name, field in self.__fields__.items():
            value = getattr(self, name)

            if value is None:
                if field.optional:
                    continue
                else:
                    raise ValidationError('{!r} can not be None'.format(name))

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

                from serde import Model, Integer, String

            .. testcode::

                class User(Model):
                    name = String()
                    age = Integer(optional=True)

                user = User.from_dict({
                    'name': 'Benedict Cumberbatch',
                    'age': 42
                })
                assert user.name == 'Benedict Cumberbatch'
                assert user.age == 42
        """
        args = []
        kwargs = {}

        for name, field in cls.__fields__.items():
            if field.name:
                name = field.name(cls, name) if callable(field.name) else field.name

            if name in d:
                try:
                    value = field.deserialize(d.pop(name))
                except DeserializationError:
                    raise
                except Exception as e:
                    raise DeserializationError(str(e))

                if field.optional:
                    kwargs[name] = value
                else:
                    args.append(value)

        if d:
            unknowns = ', '.join('{!r}'.format(k) for k in d.keys())
            plural = '' if len(d.keys()) == 1 else 's'
            raise DeserializationError('unknown dictionary key{} {}'.format(plural, unknowns))

        return cls(*args, **kwargs)

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

                from serde import Model, Integer, String

            .. testcode::

                class User(Model):
                    name = String()
                    age = Integer(optional=True)

                user = User('Benedict Cumberbatch', age=42)
                assert user.to_dict() == {'name': 'Benedict Cumberbatch', 'age': 42}
        """
        result = OrderedDict()

        for name, field in self.__fields__.items():
            value = getattr(self, name)

            if field.name:
                name = field.name(self, name) if callable(field.name) else field.name

            if value is None and field.optional:
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
