"""
Defines the core Serde Model and the ModelType metaclass.
"""

import json
from collections import OrderedDict

from .error import DeserializationError, SerializationError, ValidationError
from .field import Field
from .util import create_function


def handle_field_errors(error_cls):
    """
    Returns a decorator that handles exceptions from a Field function.

    The decorated function needs to take the model class or instance as the
    first parameter and the field instance as the second parameter.

    Args:
        error_cls (SerdeError): a SerdeError to wrap any generic exceptions that
            are generated by the Field function.

    Returns:
        function: the real decorator.
    """
    def real_decorator(func):

        def decorated_function(model, field, *args, **kwargs):
            try:
                return func(model, field, *args, **kwargs)
            except error_cls as e:
                e.add_context(field=field, model=model)
                raise
            except Exception as e:
                raise error_cls(str(e) or repr(e), cause=e, field=field, model=model)

        return decorated_function

    return real_decorator


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
    and uses them to construct the unique __init__ method on the `Model`. If the
    Model is subclassed and the __init__ method overridden then an intermediate
    class will be created that has this __init__ method.
    """

    def __new__(cls, cname, bases, attrs):
        """
        Create a new `Model` type, overriding the relevant methods.

        Args:
            cname (str): the class name.
            bases (tuple): the classes's base classes.
            attrs (dict): the attributes for this class.

        Returns:
            Model: a new Model class.
        """
        fields = Fields()
        final_attrs = OrderedDict()

        # Add all the base classes _fields attributes.
        for base in bases:
            if hasattr(base, '_fields'):
                fields.update(base._fields)

        # If we are creating an intermediate class, remove this from the attrs
        # and update our _fields.
        if '_fields' in attrs:
            fields.update(attrs.pop('_fields'))

        # Split the attrs into Fields and non-Fields.
        for name, value in attrs.items():
            if isinstance(value, Field):
                value._name = name
                fields[name] = value
            else:
                final_attrs[name] = value

        # Order the fields by the Field identifier. This gets the order that
        # they were defined on the Models.
        fields = Fields(sorted(fields.items(), key=lambda x: x[1].id))

        # Generate the __init__ method for the Model.
        init = cls.create___init__(fields)

        # If the user is trying to override the __init__ method, then we create
        # an intermediate class and make that the base of the class we are
        # creating.
        if '__init__' in final_attrs:
            interm_base = cls(cname + 'Intermediate', bases, {'_fields': fields})
            bases = (interm_base,)

        # Otherwise we add the __init__ method to the Model.
        else:
            final_attrs['__init__'] = init

        # Finally the fields to the Model.
        final_attrs['_fields'] = fields

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
                setter = '        self.{name} = self._fields.{name}.default'.format(name=name)

                if callable(field.default):
                    setter += '()'

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

    Consider a simple example user model and how it can be easily subclassed.

    .. doctest::

        >>> class User(Model):
        ...     name = Str()
        ...     age = Int(required=False)

        >>> user = User('Benedict Cumberbatch', age=42)
        >>> user.name
        'Benedict Cumberbatch'
        >>> user.age
        42

        >>> class SuperUser(User):
        ...     level = Int(default=10)

        >>> user = SuperUser('Benedict Cumberbatch', age=42)
        >>> user.name
        'Benedict Cumberbatch'
        >>> user.age
        42
        >>> user.level
        10
    """

    def __eq__(self, other):
        """
        Whether two Models are the same.
        """
        return (isinstance(other, self.__class__)
                and all(getattr(self, name) == getattr(other, name)
                        for name in self._fields.keys()))

    def __hash__(self):
        """
        Return a hash value for this Model.
        """
        values = []

        for name in self._fields.keys():
            value = getattr(self, name)

            if isinstance(value, list):
                values.append((name, frozenset(value)))
            else:
                values.append((name, value))

        return hash(tuple(values))

    def __repr__(self):
        """
        Return the canonical string representation of this Model.
        """
        values = ', '.join('{}={!r}'.format(name, getattr(self, name))
                           for name in self._fields.keys())
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
        return field.serialize(value)

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
        return field.deserialize(value)

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

    def validate(self):
        """
        Validate this Model.

        This is called by the Model constructor, so this is only needed if you
        modify attributes directly and want to validate the Model.
        """
        for name, field in self._fields.items():
            value = getattr(self, name)
            self._validate_field(field, value)

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

        A simple user model deserialized from a dictionary

        .. doctest:;

            >>> class User(Model):
            ...     name = Str()
            ...     age = Int(required=False)

            >>> user = User.from_dict({
            ...     'name': 'Benedict Cumberbatch',
            ...     'age': 42
            ... })

            >>> user.name
            'Benedict Cumberbatch'
            >>> user.age
            42
        """
        kwargs = OrderedDict()

        for name, field in cls._fields.items():
            if field.name in d:
                value = d.pop(field.name)
                kwargs[name] = cls._deserialize_field(field, value)
            elif field.required:
                message = 'dictionary key {!r} is missing'.format(field.name)
                raise DeserializationError(message, field=field, model=cls)

        if strict and d:
            message = 'unknown dictionary key{} {}'.format(
                '' if len(d.keys()) == 1 else 's',
                ', '.join('{!r}'.format(k) for k in d.keys())
            )
            raise DeserializationError(message, model=cls)

        return cls(**kwargs)

    @classmethod
    def from_json(cls, s, strict=True, **kwargs):
        """
        Load the Model from a JSON string.

        Args:
            s (str): the JSON string.
            **kwargs: extra keyword arguments to pass directly to `json.loads`.

        Returns:
            Model: an instance of this Model.
        """
        return cls.from_dict(json.loads(s, **kwargs), strict=strict)

    def to_dict(self):
        """
        Convert this Model to a dictionary.

        Returns:
            dict: the Model serialized as a dictionary.

        Raises:
            `~serde.error.SerializationError`: when a Field value cannot be
                serialized.

        A simple user model serialized as a dictionary

        .. doctest::

            >>> class User(Model):
            ...     name = Str()
            ...     age = Int(required=False)

            >>> user = User('Benedict Cumberbatch', age=42)
            >>> assert user.to_dict() == {
            ...     'name': 'Benedict Cumberbatch',
            ...     'age': 42
            ... }
        """
        result = OrderedDict()

        for name, field in self._fields.items():
            value = getattr(self, name)

            if field.required or value is not None:
                result[field.name] = self._serialize_field(field, value)

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
