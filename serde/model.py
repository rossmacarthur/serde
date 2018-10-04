"""
Defines the core Serde Model and the ModelMeta metaclass.
"""

import json
from collections import OrderedDict

from .error import DeserializationError, ModelError, SerializationError, ValidationError
from .field import Field
from .util import create_function


class ModelType(type):
    """
    A metaclass for Models.

    This metaclass pulls Field attributes off the defined class and uses them
    to construct unique __init__, __validate__, __eq__, to_dict, and from_dict
    methods on the Model.
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

        # Order the fields by the Field counter, this gets the order that they
        # are defined in their class.
        fields = OrderedDict(sorted(fields, key=lambda x: x[1].counter))

        # Create all the necessary functions for a ModelMeta. This will override
        # user defined methods with no warning.
        for func_name in cls.__dict__:
            if func_name.startswith('create_'):
                final_func_name = func_name[7:]

                # if the function is already user defined, raise an error
                if not final_func_name.startswith('__') and final_func_name in final_attrs:
                    raise ModelError('unable to set function {!r} of class {!r}, '
                                     'it already exists'.format(cname, final_func_name))

                final_attrs[final_func_name] = getattr(cls, func_name)(fields)

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
        args = ['self']
        kwargs = []
        lines = []

        for name, field in fields.items():
            if field.optional:
                kwargs.append('{name}=None'.format(name=name))
            else:
                args.append(name)

            lines.append('    self.{name} = {name}'.format(name=name))

        definition = 'def __init__({parameters}):'.format(parameters=', '.join(args + kwargs))
        lines.append('    self.__validate__()')

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
        lines = [
            '    return (isinstance(other, self.__class__)',
            *('   and self.{name} == other.{name}'.format(name=name) for name in fields.keys()),
            '    )'
        ]
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
        lines = [
            '    return hash((',
            *('        frozenset(self.{name}) if isinstance(self.{name}, list) else self.{name},'
              .format(name=name) for name in fields.keys()),
            '    ))'
        ]
        return create_function(definition, lines)

    @staticmethod
    def create___validate__(fields):
        """
        Create the __validate__ method for the Model.

        This method is used to validate that the resulting Model's attributes
        are correct for the specified fields. It is called when the Model is
        instantiated.

        Args:
            fields (OrderedDict[Text, Field]): the Model's fields.

        Returns:
            Callable: the __validate__ method.
        """
        def validate(self):
            """
            Validate this Model.

            Raises:
                ValidationError: when a field's validation fails.
            """
            for name, field in fields.items():
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

        return validate

    @staticmethod
    def create_to_dict(fields):
        """
        Create the the to_dict method for the Model.

        This method converts the Model to a dictionary, serializing each field
        on the Model.

        Args:
            fields (OrderedDict[Text, Field]): the Model's fields.

        Returns:
            Callable: the to_dict method.
        """
        def to_dict(self):
            """
            Convert this Model to a dictionary.

            Returns:
                Dict[Text, Any]: the Model serialized as dictionary.
            """
            result = OrderedDict()

            for name, field in fields.items():
                value = getattr(self, name)

                if value is None and field.optional:
                    continue

                try:
                    result[name] = field.serialize(value)
                except Exception as e:
                    raise SerializationError(str(e))

            return result

        return to_dict

    @staticmethod
    def create_from_dict(fields):
        """
        Create the the from_dict method for the Model.

        This method converts the Model from a dictionary, de serializing each
        field and creates a Model instance.

        Args:
            fields (OrderedDict[Text, Field]): the Model's fields.

        Returns:
            Callable: the from_dict class method.
        """
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

            for name, field in fields.items():
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

        return classmethod(from_dict)


class Model(metaclass=ModelType):
    """
    The base Model.
    """

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

    def to_json(self, **kwargs):
        """
        Dump the Model to a JSON string.

        Args:
            **kwargs: extra keyword arguments to pass directly to `json.dumps`.

        Returns:
            Text: a JSON representation of this Model.
        """
        return json.dumps(self.to_dict(), **kwargs)
