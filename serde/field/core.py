"""
Core Field types for Serde Models.
"""

from serde.error import SerdeError, ValidationError
from serde.util import zip_equal


def resolve_to_field_instance(thing, none_allowed=True):
    """
    Resolve an arbitrary object to a `Field` instance.

    Args:
        thing (object): anything to resolve to a Field instance.
        none_allowed (bool): if set then a thing of None will be resolved to a
            generic Field.

    Returns:
        Field: a field instance.
    """
    # We import Model here to avoid circular dependency problems.
    from serde.model import Model

    # If the things is None
    if none_allowed is True and thing is None:
        return Field()

    # If the thing is a Field then thats great.
    if isinstance(thing, Field):
        return thing

    # If the thing is a subclass of Field then attempt to create an instance.
    # This could fail the Field expects arguments.
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

    # If the thing is a built-in type then create a InstanceField with that type.
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
    deserializing.

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
    __counter__ = 0

    def __init__(self, rename=None, required=True, default=None, validators=None):
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
            validators (list): a list of validator functions taking the value
                to validate as an argument. The functions need to raise an
                `Exception` if they fail.
        """
        super().__init__()

        self.id = Field.__counter__
        Field.__counter__ += 1

        self.rename = rename
        self.required = required
        self.default = default
        self.validators = validators or []

    def __attrs__(self):
        """
        Return all attributes of this Field except "id".
        """
        return {name: value for name, value in vars(self).items()
                if name not in ('id', '__name__')}

    def __eq__(self, other):
        """
        Whether two Fields are the same.
        """
        return isinstance(other, self.__class__) and self.__attrs__() == other.__attrs__()

    def __repr__(self):
        """
        Return the canonical string representation of this Field.
        """
        values = ', '.join('{}={!r}'.format(name, value)
                           for name, value in sorted(self.__attrs__().items()))
        return '{name}({values})'.format(name=self.__class__.__name__, values=values)

    def __setattr__(self, name, value):
        """
        Set a named attribute on a Field.

        Raises:
            `~serde.error.SerdeError`: when the __name__ attribute is set after
                it has already been set.
        """
        if name == '__name__' and hasattr(self, '__name__'):
            raise SerdeError('field instance used multiple times')

        super().__setattr__(name, value)

    def __validate__(self, value):
        """
        Validate the given value according to this Field's specification.

        This method is called by the Model.

        Args:
            value: the value to validate.
        """
        if value is None:
            if self.required is True:
                raise ValidationError('{!r} is required'.format(self.name))

            return

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
        if not hasattr(self, '__name__'):
            raise SerdeError('field is not on a Model')

        if self.rename is None:
            return self.__name__

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
        Validate the given value according to this Field's specification.

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

    def __init__(self, model, **kwargs):
        """
        Create a new ModelField.

        Args:
            model: the Model class that this Field wraps.
            **kwargs: keyword arguments for the `InstanceField` constructor.
        """
        super().__init__(model, **kwargs)

    def serialize(self, value):
        """
        Serialize the given `Model` as a dictionary.

        Args:
            value (Model): the model to serialize.

        Returns:
            dict: the serialized dictionary.
        """
        value = value.to_dict()
        return super().serialize(value)

    def deserialize(self, value):
        """
        Deserialize the given dictionary to a `Model` instance.

        Args:
            value (dict): the dictionary to deserialize.

        Returns:
            Model: the deserialized model.
        """
        value = self.type.from_dict(value)
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
    A dict Field with a required key and value type.

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
        Serialize the given value.

        Args:
            value (dict): the value to serialize.

        Returns:
            dict: the serialized dictionary.
        """
        value = {self.key.serialize(k): self.value.serialize(v) for k, v in value.items()}
        return super().serialize(value)

    def deserialize(self, value):
        """
        Deserialize the given value.

        Args:
            value (dict): the value to deserialize.

        Returns:
            dict: the deserialized dictionary.
        """
        value = super().deserialize(value)
        return {self.key.deserialize(k): self.value.deserialize(v) for k, v in value.items()}

    def validate(self, value):
        """
        Validate the given value according to this Field's specification.

        Args:
            value: the value to validate.

        Raises:
            `~serde.error.ValidationError`: when the given value is invalid.
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

    This field represents the built-in `float` type. But there are a few extra
    options to help constrain the Field further.

    Consider an example model Point, with two `Float` fields, but we constrain
    the x and y such that the Point has to be in the second quadrant.

    .. doctest::

        >>> class Point(Model):
        ...     x = Float(max=0.0)
        ...     y = Float(min=0.0)

        >>> point = Point(-1.5, 5.5)

        >>> Point(1.5, 5.5)
        Traceback (most recent call last):
            ...
        serde.error.ValidationError: expected at most 0.0 but got 1.5
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
        Validate the given value according to this Field's specification.

        Args:
            value: the value to validate.

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

    This field represents the built-in `int` type. But there are a few extra
    options to help constrain the Field further.

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
        Validate the given value according to this Field's specification.

        Args:
            value: the value to validate.

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

    def __init__(self, field=None, min_length=None, max_length=None, **kwargs):
        """
        Create a new List.

        Args:
            field (Field): the Field class/instance for this List's elements.
            min_length (int): the minimum number of elements allowed.
            max_length (int): the maximum number of elements allowed.
            **kwargs: keyword arguments for the `InstanceField` constructor.
        """
        super().__init__(list, **kwargs)
        self.field = resolve_to_field_instance(field)
        self.min_length = min_length
        self.max_length = max_length

    def serialize(self, value):
        """
        Serialize the given value.

        Args:
            value (list): the value to serialize.

        Returns:
            list: the serialized list.
        """
        value = [self.field.serialize(v) for v in value]
        return super().serialize(value)

    def deserialize(self, value):
        """
        Deserialize the given value.

        Args:
            value (list): the value to deserialize.

        Returns:
            list: the deserialized list.
        """
        value = super().deserialize(value)
        return [self.field.deserialize(v) for v in value]

    def validate(self, value):
        """
        Validate the given value according to this Field's specification.

        Args:
            value: the value to validate.

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
            self.field.validate(v)


class Str(InstanceField):
    """
    A string Field.

    This field represents the built-in `str` type. But there are a few extra
    options to help constrain the Field further.

    Consider an example model User

    .. doctest::

        >>> class User(Model):
        ...     name = Str(min_length=1, strip=True)
        ...     address = Str(required=False)

        >>> user = User.from_dict({'name': '    George Clooney  '})
        >>> user.name
        'George Clooney'

        >>> User('')
        Traceback (most recent call last):
            ...
        serde.error.ValidationError: expected at least 1 characters but got 0 characters
    """

    def __init__(self, min_length=None, max_length=None, strip=False, **kwargs):
        """
        Create a new Str.

        Args:
            min_length (int): the minimum number of characters allowed.
            max_length (int): the maximum number of characters allowed.
            strip (bool): whether to call `str.strip()` on the data when
                deserializing.
            **kwargs: keyword arguments for the `InstanceField` constructor.
        """
        super().__init__(str, **kwargs)
        self.min_length = min_length
        self.max_length = max_length
        self.strip = strip

    def deserialize(self, value):
        """
        Deserialize the given value.

        Args:
            value (str): the value to deserialize.

        Returns:
            str: the deserialized string.
        """
        value = super().deserialize(value)

        if self.strip is True:
            value = value.strip()

        return value

    def validate(self, value):
        """
        Validate the deserialized value.

        Args:
            value: the value to validate.

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

    def __init__(self, *fields, **kwargs):
        """
        Create a new Tuple.

        Args:
            *fields (Field): the Field classes/instances for elements in this
                Tuple.
            **kwargs: keyword arguments for the `InstanceField` constructor.
        """
        super().__init__(tuple, **kwargs)
        self.fields = tuple(resolve_to_field_instance(f, none_allowed=False) for f in fields)

    def serialize(self, value):
        """
        Serialize the given value.

        Args:
            value (tuple): the value to serialize.

        Returns:
            tuple: the serialized tuple.
        """
        return tuple(f.serialize(v) for f, v in zip_equal(self.fields, value))

    def deserialize(self, value):
        """
        Deserialize the given value.

        Args:
            value (tuple): the value to deserialize.

        Returns:
            tuple: the deserialized tuple.
        """
        value = super().deserialize(value)
        return tuple(f.deserialize(v) for f, v in zip_equal(self.fields, value))

    def validate(self, value):
        """
        Validate the given value according to this Field's specification.

        Args:
            value (tuple): the value to validate.

        Raises:
            `~serde.error.ValidationError`: when the given value is invalid.
        """
        super().validate(value)

        if len(self.fields) != len(value):
            raise ValidationError('expected {} elements but got {} elements'
                                  .format(len(self.fields), len(value)))

        for f, v in zip(self.fields, value):
            f.validate(v)
