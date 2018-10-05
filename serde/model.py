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
            name (Text): the attribute lookup.

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

    This metaclass pulls Field attributes off the defined class and uses them
    to construct unique __init__, __eq__, and __hash__ methods on the Model.
    """

    def __new__(cls, cname, bases, attrs):
        """
        Create a new Model type, overriding the relevant methods.

        Args:
            cname (Text): the class name.
            bases (Tuple[type]): the classes's base classes.
            attrs (Dict[Text, Any]): the attributes for this class.

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
        fields = Fields(sorted(fields, key=lambda x: (x[1].optional, x[1].counter)))

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
        Create the __init__ method for the Model.

        The generated function will simply take the actual field values as
        parameters and set them as attributes on the instance. It will also
        validate the field values.

        Args:
            fields (OrderedDict[Text, Field]): the Model's fields.

        Returns:
            Callable: the __init__ method.
        """
        parameters = ['self']
        setters = []
        defaults = []

        for name, field in fields.items():
            parameters.append('{name}=None'.format(name=name) if field.optional else name)
            setters.append('    self.{name} = {name}'.format(name=name))

            if field.default is not None:
                setter = '        self.{name} = self.__fields__.{name}.default'.format(name=name)

                if callable(field.default):
                    setter += '(self)'

                defaults.extend(['', '    if self.{name} is None:'.format(name=name), setter])

        definition = 'def __init__({parameters}):'.format(parameters=', '.join(parameters))
        lines = setters + defaults + ['', '    self.__validate__()']

        return create_function(definition, lines)

    @staticmethod
    def create___eq__(fields):
        """
        Create the __eq__ method for the Model.

        This method simply checks if the class is the same type and the field
        values are equal.

        Args:
            fields (OrderedDict[Text, Field]): the class's fields.

        Returns:
            Callable: the __eq__ method.
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
        Create the __hash__ method for the Model.

        Args:
            fields (OrderedDict[Text, Field]): the class's fields.

        Returns:
            Callable: the __hash__ method.
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
    The base Model.
    """

    def __validate__(self):
        """
        Validate this Model.

        Raises:
            ValidationError: when a field's validation fails.
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
            except Exception as e:
                if isinstance(e, ValidationError):
                    raise
                raise ValidationError(str(e))

    @classmethod
    def from_dict(cls, d):
        """
        Convert the dictionary to an instance of this Model.

        Args:
            d (Dict[Text, Any]): a serialized version of this Model.

        Returns:
            Model: an instance of this Model.
        """
        args = []
        kwargs = {}

        for name, field in cls.__fields__.items():
            if field.name:
                name = field.name(cls, name) if callable(field.name) else field.name

            if name in d:
                value = field.deserialize(d.pop(name))

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
            s (Text): the JSON string.
            **kwargs: extra keyword arguments to pass directly to `json.loads`.

        Returns:
            Model: an instance of this Model.
        """
        return cls.from_dict(json.loads(s, **kwargs))

    def to_dict(self):
        """
        Convert this Model to a dictionary.

        Returns:
            Dict[Text, Any]: the Model serialized as dictionary.
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
            except Exception as e:
                raise SerializationError(str(e))

        return result

    def to_json(self, **kwargs):
        """
        Dump the Model to a JSON string.

        Args:
            **kwargs: extra keyword arguments to pass directly to `json.dumps`.

        Returns:
            Text: a JSON representation of this Model.
        """
        return json.dumps(self.to_dict(), **kwargs)
