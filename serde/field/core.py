"""
Core Field types for Serde Models.
"""

from serde.error import SerdeError, ValidationError
from serde.util import list_class_init_parameters, zip_equal


def resolve_to_field_instance(thing, none_allowed=True):
    """
    Resolve an arbitrary object to a `Field` instance.

    Args:
        thing: anything to resolve to a Field instance.
        none_allowed (bool): if set then a thing of None will be resolved to a
            generic Field.

    Returns:
        Field: a field instance.
    """
    # We import Model here to avoid circular dependency problems.
    from serde.model import Model

    # If the thing is None then create a generic Field.
    if none_allowed and thing is None:
        return Field()

    # If the thing is a Field then thats great.
    elif isinstance(thing, Field):
        return thing

    # If the thing is a subclass of Field then attempt to create an instance.
    # This could fail the Field expects positional arguments.
    try:
        if issubclass(thing, Field):
            return thing()
    except TypeError:
        pass

    # If the thing is a subclass of Model then create a ModelField instance.
    try:
        if issubclass(thing, Model):
            return ModelField(thing)
    except TypeError:
        pass

    # If the thing is a built-in type that we support then create an
    # InstanceField with that type.
    field_class = {
        bool: Bool,
        dict: Dict,
        float: Float,
        int: Int,
        list: List,
        str: Str,
        tuple: Tuple
    }.get(thing, None)

    if field_class is not None:
        return field_class()

    raise TypeError('{!r} is not a Field, an instance of a Field, or a supported type'
                    .format(thing))


class Field:
    """
    A field on a `~serde.model.Model`.

    Fields handle serializing, deserializing, and validation of input values for
    Model objects.

    Here is a simple example of how Fields can be used on a Model. In this
    example we use the base class Field which does not have any of its own
    validation, and simply passes values through when serializing and
    deserializing. Typically, more constrained Field classes would be used.

    .. doctest::

        >>> def assert_is_odd(value):
        ...     assert value % 2 != 0, 'value is not odd!'

        >>> class Person(Model):
        ...     name = Field()
        ...     fave_number = Field(required=False, validators=[assert_is_odd])
        ...     fave_color = Field(required=False, default='pink')

        >>> person = Person('William Shakespeare', fave_number=455)
        >>> person.name
        'William Shakespeare'
        >>> person.fave_number
        455
        >>> person.fave_color
        'pink'

        >>> Person.from_dict({'name': 'Beyonce', 'fave_number': 4})
        Traceback (most recent call last):
        ...
        serde.error.ValidationError: value is not odd!

    Here is a more advanced example where we subclass a field and override the
    serialize, deserialize, and validate methods.

    .. doctest::

        >>> class Reversed(Field):
        ...
        ...     def serialize(self, value):
        ...         return value[::-1]
        ...
        ...     def deserialize(self, value):
        ...         return value[::-1]
        ...
        ...     def validate(self, value):
        ...         assert isinstance(value, str)

        >>> class Example(Model):
        ...     silly = Reversed(rename='sILLy')

        >>> example = Example('test')
        >>> example.silly
        'test'

        >>> example.to_dict()
        OrderedDict([('sILLy', 'tset')])
    """

    # This is so we can get the order the fields were instantiated in.
    __counter = 0

    def __init__(self, rename=None, required=True, default=None,
                 serializers=None, deserializers=None, validators=None):
        """
        Create a new Field.

        Args:
            rename (str): override the name for the field when serializing and
                expect this name when deserializing.
            required (bool): whether this field is required. Required fields
                have to be present in instantiation and deserialization.
            default: a value to use if there is no input field value. This can
                also be a function that generates the default. The function
                must take no arguments.
            serializers (list): a list of serializer functions taking the value
                to serialize as an argument. The functions need to raise an
                `Exception` if they fail. These serializer functions will be
                applied before the primary serializer on this Field.
            deserializers (list): a list of deserializer functions taking the
                value to deserialize as an argument. The functions need to raise
                an `Exception` if they fail. These deserializer functions will
                be applied after the primary deserializer on this Field.
            validators (list): a list of validator functions taking the value
                to validate as an argument. The functions need to raise an
                `Exception` if they fail.
        """
        super().__init__()

        self.id = Field.__counter
        Field.__counter += 1

        self.rename = rename
        self.required = required
        self.default = default
        self.serializers = serializers or []
        self.deserializers = deserializers or []
        self.validators = validators or []

    def _attrs(self):
        """
        Return all attributes of this Field except "id" and "_name".
        """
        return {
            name: value for name, value in vars(self).items()
            if name not in ('id', '_name')
        }

    def __eq__(self, other):
        """
        Whether two Fields are the same.
        """
        return isinstance(other, self.__class__) and self._attrs() == other._attrs()

    def __repr__(self):
        """
        Return the canonical string representation of this Field.
        """
        parameters = [
            name for name in list_class_init_parameters(self.__class__)
            if hasattr(self, name)
        ]
        values = ', '.join('{}={!r}'.format(name, getattr(self, name)) for name in parameters)
        return '{name}({values})'.format(name=self.__class__.__name__, values=values)

    def __setattr__(self, name, value):
        """
        Set a named attribute on a Field.

        Raises:
            `~serde.error.SerdeError`: when the _name attribute is set after it
                has already been set.
        """
        if name == '_name' and hasattr(self, '_name'):
            raise SerdeError('field instance used multiple times')

        super().__setattr__(name, value)

    def _serialize(self, value):
        """
        Serialize the given value according to this Field's specification.

        Args:
            value: the value to serialize.

        Returns:
            the serialized value.
        """
        for serializer in self.serializers:
            value = serializer(value)

        value = self.serialize(value)

        return value

    def _deserialize(self, value):
        """
        Deserialize the given value according to this Field's specification.

        Args:
            value: the value to deserialize.

        Returns:
            the deserialized value.
        """
        value = self.deserialize(value)

        for deserializer in self.deserializers:
            value = deserializer(value)

        return value

    def _validate(self, value):
        """
        Validate the given value according to this Field's specification.

        This method is called by the Model.

        Args:
            value: the value to validate.
        """
        self.validate(value)

        for validator in self.validators:
            validator(value)

    @property
    def name(self):
        """
        The name of this Field.

        This is the rename value, given when the Field is instantiated,
        otherwise the attribute name of this Field on the Model.
        """
        if not hasattr(self, '_name'):
            raise SerdeError('field is not on a Model')

        if self.rename is None:
            return self._name

        return self.rename

    def serialize(self, value):
        """
        Serialize the given value according to this Field's specification.

        Args:
            value: the value to serialize.

        Returns:
            the serialized value.
        """
        return value

    def deserialize(self, value):
        """
        Deserialize the given value according to this Field's specification.

        Args:
            value: the value to deserialize.

        Returns:
            the deserialized value.
        """
        return value

    def validate(self, value):
        """
        Validate the given value according to this Field's specification.

        Args:
            value: the value to validate.
        """
        pass


class InstanceField(Field):
    """
    A `Field` that validates a value is an instance of the given type.
    """

    def __init__(self, type, **kwargs):
        """
        Create a new InstanceField.

        Args:
            type: the type that this Field wraps.
            **kwargs: keyword arguments for the `Field` constructor.
        """
        super().__init__(**kwargs)
        self.type = type

    def validate(self, value):
        """
        Validate the given value is an instance of the specified type.

        Args:
            value: the value to validate.

        Raises:
            `~serde.error.ValidationError`: when the given value is not an
                instance of the specified type.
        """
        super().validate(value)

        if not isinstance(value, self.type):
            raise ValidationError('expected {!r} but got {!r}'
                                  .format(self.type.__name__, value.__class__.__name__))


class ModelField(InstanceField):
    """
    A `Field` for `~serde.model.Model` fields.

    This is wrapper Field for Models to support sub-Models. The serialize and
    deserialize methods call the `~serde.model.Model.to_dict()` and
    `~serde.model.Model.from_dict()`  methods on the Model class. This allows
    complex nested Models.

    .. doctest::

        >>> class Birthday(Model):
        ...     day = Int(min=1, max=31)
        ...     month = Str()

        >>> class Person(Model):
        ...     name = Str()
        ...     birthday = ModelField(Birthday, required=False)

        >>> person = Person('Beyonce', birthday=Birthday(4, 'September'))
        >>> person.name
        'Beyonce'
        >>> person.birthday.day
        4
        >>> person.birthday.month
        'September'

        >>> assert person.to_dict() == {
        ...     'name': 'Beyonce',
        ...     'birthday': {
        ...         'day': 4,
        ...         'month': 'September'
        ...     }
        ... }

        >>> Person.from_dict({
        ...     'name': 'Beyonce',
        ...     'birthday': {
        ...         'day': 4,
        ...         'month': 'September'
        ...     }
        ... })
        Person(name='Beyonce', birthday=Birthday(day=4, month='September'))
    """

    def __init__(self, model, dict=None, strict=True, **kwargs):
        """
        Create a new ModelField.

        Args:
            model: the Model class that this Field wraps.
            dict (type): the class of the deserialized dictionary. This defaults
                to an `OrderedDict` so that the fields will be returned in the
                order they were defined on the Model.
            strict (bool): if set to False then no exception will be raised when
                unknown dictionary keys are present when deserializing.
            **kwargs: keyword arguments for the `InstanceField` constructor.
        """
        super().__init__(model, **kwargs)
        self.dict = dict
        self.strict = strict

    def serialize(self, value):
        """
        Serialize the given `Model` instance as a dictionary.

        Args:
            value (Model): the model to serialize.

        Returns:
            dict: the serialized dictionary.
        """
        value = value.to_dict(dict=self.dict)
        return super().serialize(value)

    def deserialize(self, value):
        """
        Deserialize the given dictionary to a `Model` instance.

        Args:
            value (dict): the dictionary to deserialize.

        Returns:
            Model: the deserialized model.
        """
        value = self.type.from_dict(value, strict=self.strict)
        return super().deserialize(value)


class Bool(InstanceField):
    """
    A boolean Field.

    This field represents the built-in `bool` type. The Bool constructor accepts
    all keyword arguments accepted by `InstanceField`.

    Consider an example model with two `Bool` fields, one with extra options and
    one with no arguments.

    .. doctest::

        >>> class Example(Model):
        ...     enabled = Bool()
        ...     something = Bool(required=False, default=True)

        >>> example = Example.from_dict({'enabled': False})
        >>> example.enabled
        False
        >>> example.something
        True
    """

    def __init__(self, **kwargs):
        """
        Create a new Bool.

        Args:
            **kwargs: keyword arguments for the `InstanceField` constructor.
        """
        super().__init__(bool, **kwargs)


class Dict(InstanceField):
    """
    A dictionary Field with a required key and value type.

    This field represents the built-in `dict` type. Each key and value will be
    serialized, deserialized, and validated with the specified key and value
    types. The key and value types can be specified using Field classes, Field
    instances, Model classes, or built-in types that have a corresponding Field
    type in this library.

    Consider an example model with a constants attribute which is map of strings
    to floats.

    .. doctest::

        >>> class Example(Model):
        ...     constants = Dict(str, float)

        >>> example = Example({'pi': 3.1415927, 'e': 2.7182818})
        >>> example.constants['pi']
        3.1415927
        >>> example.constants['e']
        2.7182818

        >>> d = example.to_dict()
        >>> d['constants']['pi']
        3.1415927
        >>> d['constants']['e']
        2.7182818

        >>> Example({'pi': '3.1415927'})
        Traceback (most recent call last):
            ...
        serde.error.ValidationError: expected 'float' but got 'str'

        >>> Example.from_dict({'constants': {100: 3.1415927}})
        Traceback (most recent call last):
            ...
        serde.error.ValidationError: expected 'str' but got 'int'
    """

    def __init__(self, key=None, value=None, min_length=None, max_length=None, **kwargs):
        """
        Create a new Dict.

        Args:
            key (Field): the Field class/instance for keys in this Dict.
            value (Field): the Field class/instance for values in this Dict.
            min_length (int): the minimum number of elements allowed.
            max_length (int): the maximum number of elements allowed.
            **kwargs: keyword arguments for the `InstanceField` constructor.
        """
        super().__init__(dict, **kwargs)
        self.key = resolve_to_field_instance(key)
        self.value = resolve_to_field_instance(value)
        self.min_length = min_length
        self.max_length = max_length

    def serialize(self, value):
        """
        Serialize the given dictionary.

        Each key and value in the dictionary will be serialized with the
        specified key and value Field instances.

        Args:
            value (dict): the dictionary to serialize.

        Returns:
            dict: the serialized dictionary.
        """
        value = {self.key.serialize(k): self.value.serialize(v) for k, v in value.items()}
        return super().serialize(value)

    def deserialize(self, value):
        """
        Deserialize the given dictionary.

        Each key and value in the dictionary will be deserialized with the
        specified key and value Field instances.

        Args:
            value (dict): the dictonary to deserialize.

        Returns:
            dict: the deserialized dictionary.
        """
        value = super().deserialize(value)
        return {self.key.deserialize(k): self.value.deserialize(v) for k, v in value.items()}

    def validate(self, value):
        """
        Validate the given dictionary.

        Each key and value in the dictionary will be validated with the
        specified key and value Field instances. The dictionary will also be
        validated to have the specified minimum number of elements and maximum
        number of elements.

        Args:
            value (dict): the dictionary to validate.

        Raises:
            `~serde.error.ValidationError`: when the given dictionary is
                invalid.
        """
        super().validate(value)

        count = len(value.keys())

        if self.min_length is not None and count < self.min_length:
            raise ValidationError('expected at least {} elements but got {} elements'
                                  .format(self.min_length, count))

        if self.max_length is not None and count > self.max_length:
            raise ValidationError('expected at most {} elements but got {} elements'
                                  .format(self.max_length, count))

        for k, v in value.items():
            self.key.validate(k)
            self.value.validate(v)


class Float(InstanceField):
    """
    A float Field.

    This field represents the built-in `float` type. The Float constructor
    accepts all keyword arguments accepted by `InstanceField`.

    Consider an example model TestMark, with a percentage `Float` field.

    .. doctest::

        >>> class TestMark(Model):
        ...     result = Float(min=0.0, max=100.0)

        >>> TestMark(75.1)
        TestMark(result=75.1)

        >>> TestMark(101.5)
        Traceback (most recent call last):
            ...
        serde.error.ValidationError: expected at most 100.0 but got 101.5
    """

    def __init__(self, min=None, max=None, **kwargs):
        """
        Create a new Float.

        Args:
            min (float): the minimum value allowed.
            max (float): the maximum value allowed.
            **kwargs: keyword arguments for the `InstanceField` constructor.
        """
        super().__init__(float, **kwargs)
        self.min = min
        self.max = max

    def validate(self, value):
        """
        Validate the given float.

        The given value will be validated to be an instance of `float`. And is
        required to be between the specified minimum and maximum values.

        Args:
            value (float): the float to validate.

        Raises:
            `~serde.error.ValidationError`: when the given value is invalid.
        """
        super().validate(value)

        if self.min is not None and value < self.min:
            raise ValidationError('expected at least {} but got {}'.format(self.min, value))

        if self.max is not None and value > self.max:
            raise ValidationError('expected at most {} but got {}'.format(self.max, value))


class Int(InstanceField):
    """
    An integer Field.

    This field represents the built-in `int` type. The Int constructor accepts
    all keyword arguments accepted by `InstanceField`.

    Consider an example model Point, with two `Int` fields, but we constrain the
    x and y such that the Point has to be in the second quadrant.

    .. doctest::

        >>> class Point(Model):
        ...     x = Int(max=0)
        ...     y = Int(min=0)

        >>> point = Point(-1, 5)

        >>> Point(1, 5)
        Traceback (most recent call last):
        ...
        serde.error.ValidationError: expected at most 0 but got 1
    """

    def __init__(self, min=None, max=None, **kwargs):
        """
        Create a new Int.

        Args:
            min (int): the minimum value allowed.
            max (int): the maximum value allowed.
            **kwargs: keyword arguments for the `InstanceField` constructor.
        """
        super().__init__(int, **kwargs)
        self.min = min
        self.max = max

    def validate(self, value):
        """
        Validate the given integer.

        The given value will be validated to be an instance of `int`. And is
        required to be between the specified minimum and maximum values.

        Args:
            value (int): the integer to validate.

        Raises:
            `~serde.error.ValidationError`: when the given value is invalid.
        """
        super().validate(value)

        if self.min is not None and value < self.min:
            raise ValidationError('expected at least {} but got {}'.format(self.min, value))

        if self.max is not None and value > self.max:
            raise ValidationError('expected at most {} but got {}'.format(self.max, value))


class List(InstanceField):
    """
    A list Field with a required element type.

    This field represents the built-in `list` type. Each element will be
    serialized, deserialized, and validated with the specified element type. The
    element type can be specified using Field classes, Field instances, Model
    classes, or built-in types that have a corresponding Field type in this
    library.

    Consider a user model that can have multiple emails

    .. doctest::

        >>> class User(Model):
        ...     emails = List(str, min_length=1, default=[])

        >>> user = User(['john@smith.com', 'john.smith@email.com'])
        >>> user.emails[0]
        'john@smith.com'
        >>> user.emails[1]
        'john.smith@email.com'

        >>> User(emails={'john@smith.com': None })
        Traceback (most recent call last):
            ...
        serde.error.ValidationError: expected 'list' but got 'dict'

        >>> User.from_dict({'emails': [1234]})
        Traceback (most recent call last):
            ...
        serde.error.ValidationError: expected 'str' but got 'int'
    """

    def __init__(self, element=None, min_length=None, max_length=None, **kwargs):
        """
        Create a new List.

        Args:
            element (Field): the Field class/instance for this List's elements.
            min_length (int): the minimum number of elements allowed.
            max_length (int): the maximum number of elements allowed.
            **kwargs: keyword arguments for the `InstanceField` constructor.
        """
        super().__init__(list, **kwargs)
        self.element = resolve_to_field_instance(element)
        self.min_length = min_length
        self.max_length = max_length

    def serialize(self, value):
        """
        Serialize the given list.

        Each element in the list will be serialized with the specified element
        Field instance.

        Args:
            value (list): the list to serialize.

        Returns:
            list: the serialized list.
        """
        value = [self.element.serialize(v) for v in value]
        return super().serialize(value)

    def deserialize(self, value):
        """
        Deserialize the given list.

        Each element in the list will be deserialized with the specified element
        Field instance.

        Args:
            value (list): the list to deserialize.

        Returns:
            list: the deserialized list.
        """
        value = super().deserialize(value)
        return [self.element.deserialize(v) for v in value]

    def validate(self, value):
        """
        Validate the given list.

        Each element in the list will be validated with the specified element
        Field instance. The list will also be validated to have the specified
        minimum number of elements and maximum number of elements.

        Args:
            value (list): the list to validate.

        Raises:
            `~serde.error.ValidationError`: when the given value is invalid.
        """
        super().validate(value)

        count = len(value)

        if self.min_length is not None and count < self.min_length:
            raise ValidationError('expected at least {} elements but got {} elements'
                                  .format(self.min_length, count))

        if self.max_length is not None and count > self.max_length:
            raise ValidationError('expected at most {} elements but got {} elements'
                                  .format(self.max_length, count))

        for v in value:
            self.element.validate(v)


class Str(InstanceField):
    """
    A string Field.

    This field represents the built-in `str` type.

    Consider an example model User

    .. doctest::

        >>> class User(Model):
        ...     name = Str(min_length=1, deserializers=[lambda s: s.strip()])
        ...     address = Str(required=False)

        >>> user = User.from_dict({'name': '    George Clooney  '})
        >>> user.name
        'George Clooney'

        >>> User('')
        Traceback (most recent call last):
            ...
        serde.error.ValidationError: expected at least 1 characters but got 0 characters
    """

    def __init__(self, min_length=None, max_length=None, **kwargs):
        """
        Create a new Str.

        Args:
            min_length (int): the minimum number of characters allowed.
            max_length (int): the maximum number of characters allowed.
            **kwargs: keyword arguments for the `InstanceField` constructor.
        """
        super().__init__(str, **kwargs)
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, value):
        """
        Validate the given string.

        The given value will be validated to be an instance of `str`. And is
        required to be between the specified minimum and maximum values.

        Args:
            value (str): the string to validate.

        Raises:
            `~serde.error.ValidationError`: when the given value is invalid.
        """
        super().validate(value)

        count = len(value)

        if self.min_length is not None and count < self.min_length:
            raise ValidationError('expected at least {} characters but got {} characters'
                                  .format(self.min_length, count))

        if self.max_length is not None and count > self.max_length:
            raise ValidationError('expected at most {} characters but got {} characters'
                                  .format(self.max_length, count))


class Tuple(InstanceField):
    """
    A tuple Field with required element types.

    Each element will be serialized, deserialized, and validated with the
    specified element type. The given element types can be specified using Field
    classes, Field instances, Model classes, or built-in types that have a
    corresponding Field type in this library.

    Consider an example person that has a name and a birthday

    .. doctest::

        >>> class Person(Model):
        ...     name = Str()
        ...     birthday = Tuple(int, str, int)

        >>> person = Person('Ross MacArthur', (19, 'June', 1994))
        >>> person.name
        'Ross MacArthur'
        >>> person.birthday[0]
        19
        >>> person.birthday[1]
        'June'
        >>> person.birthday[2]
        1994

        >>> Person('Beyonce', birthday=(4, 'September'))
        Traceback (most recent call last):
            ...
        serde.error.ValidationError: expected 3 elements but got 2 elements

        >>> Person.from_dict({'name': 'Beyonce', 'birthday': (4, 9, 1994)})
        Traceback (most recent call last):
            ...
        serde.error.ValidationError: expected 'str' but got 'int'
    """

    def __init__(self, *elements, **kwargs):
        """
        Create a new Tuple.

        Args:
            *elements (Field): the Field classes/instances for elements in this
                Tuple.
            **kwargs: keyword arguments for the `InstanceField` constructor.
        """
        super().__init__(tuple, **kwargs)
        self.elements = tuple(resolve_to_field_instance(e, none_allowed=False) for e in elements)

    def serialize(self, value):
        """
        Serialize the given tuple.

        Each element in the tuple will be serialized with the specified element
        Field instance.

        Args:
            value (tuple): the tuple to serialize.

        Returns:
            tuple: the serialized tuple.
        """
        return tuple(e.serialize(v) for e, v in zip_equal(self.elements, value))

    def deserialize(self, value):
        """
        Deserialize the given tuple.

        Each element in the tuple will be deserialized with the specified
        element Field instance.

        Args:
            value (tuple): the tuple to deserialize.

        Returns:
            tuple: the deserialized tuple.
        """
        value = super().deserialize(value)
        return tuple(e.deserialize(v) for e, v in zip_equal(self.elements, value))

    def validate(self, value):
        """
        Validate the given tuple.

        Each element in the tuple will be validated with the specified element
        Field instance.

        Args:
            value (tuple): the tuple to validate.

        Raises:
            `~serde.error.ValidationError`: when the given value is invalid.
        """
        super().validate(value)

        if len(self.elements) != len(value):
            raise ValidationError('expected {} elements but got {} elements'
                                  .format(len(self.elements), len(value)))

        for e, v in zip(self.elements, value):
            e.validate(v)
