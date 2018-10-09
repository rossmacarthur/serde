"""
Field types for Serde Models.
"""

from serde.error import ValidationError
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

    # If the thing is a built-in type then create a TypeField with that type.
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

    Examples:

        Here is a simple example of how Fields can be used on a Model. In this
        example we use the base class Field which does not have any of its own
        validation, and simply passes values through when serializing and
        deserializing.

        .. testsetup::

            from serde import Model, Field, Str

        .. testcode::

            def assert_is_even(value):
                assert value % 2 == 0

            class Person(Model):
                name = Field()
                favourite_number = Field(required=False, validators=[assert_is_even])
                favourite_color = Field(required=False, default='pink')

            person = Person('William Shakespeare', favourite_number=454)
            assert person.name == 'William Shakespeare'
            assert person.favourite_number == 454
            assert person.favourite_color == 'pink'

        Here is a more advanced example where we subclass a field and override
        the serialize, deserialize, and validate methods. As well as use a
        function to generate a Fields default value.

        .. testcode::

            import uuid

            class Uuid(Field):

                def serialize(self, value):
                    return str(value)

                def deserialize(self, value):
                    return uuid.UUID(value)

                def validate(self, value):
                    assert isinstance(value, uuid.UUID)

            class User(Model):
                key = Uuid(default= uuid.uuid4)

            user = User()
            assert isinstance(user.key, uuid.UUID)
    """

    # This is so we can get the order the fields were instantiated in.
    __counter__ = 0

    def __init__(self, name=None, required=True, default=None, validators=None):
        """
        Create a new Field.

        Args:
            name (str): override the name for the field when serializing and
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

        self.name = name
        self.required = required
        self.default = default
        self.validators = validators or []

    def __attrs__(self):
        """
        Return all attributes of this Field except "id".
        """
        return {name: value for name, value in vars(self).items() if name != 'id'}

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


class TypeField(Field):
    """
    A `Field` that validates a value is an instance of the given type.
    """

    def __init__(self, type, **kwargs):
        """
        Create a new TypeField.

        Args:
            type: the type that this Field wraps.
            **kwargs: keyword arguments for the `Field` constructor.
        """
        super().__init__(**kwargs)
        self.type = type

    def validate(self, value):
        """
        Validate the deserialized value.

        Args:
            value: the value to validate.

        Raises:
            `~serde.error.ValidationError`: when the given value is not an
                instance of the specified type.
        """
        if not isinstance(value, self.type):
            raise ValidationError('expected {!r} but got {!r}'
                                  .format(self.type.__name__, value.__class__.__name__))


class ModelField(TypeField):
    """
    A `Field` for `~serde.model.Model` fields.

    This is wrapper Field for Models to support sub-Models. The serialize and
    deserialize methods call the `~serde.model.Model.to_dict()` and
    `~serde.model.Model.from_dict()`  methods on the Model class. This allows
    complex nested Models.

    Examples:

        .. testsetup::

            from serde import Model, ModelField, Str, Int

        Consider a person model that has a birthday

        .. testcode::

            class Birthday(Model):
                day = Int(min=1, max=31)
                month = Str()

            class Person(Model):
                name = Str()
                birthday = ModelField(Birthday, required=False)

            person = Person('Beyonce', birthday=Birthday(4, 'September'))
            assert person.name == 'Beyonce'
            assert person.birthday.day == 4
            assert person.birthday.month == 'September'

        This would be serialized like this

        .. testcode::

            assert person.to_dict() == {
                'name': 'Beyonce',
                'birthday': {
                    'day': 4,
                    'month': 'September'
                }
            }

        And deserialized like this

        .. testcode::

            person = Person.from_dict({
                'name': 'Beyonce',
                'birthday': {
                    'day': 4,
                    'month': 'September'
                }
            })

            assert person.name == 'Beyonce'
            assert person.birthday.day == 4
            assert person.birthday.month == 'September'
    """

    def serialize(self, value):
        """
        Serialize the given `Model` as a dictionary.

        Args:
            value (Model): the model to serialize.

        Returns:
            dict: the serialized dictionary.
        """
        return value.to_dict()

    def deserialize(self, value):
        """
        Deserialize the given dictionary to a `Model` instance.

        Args:
            value (dict): the dictionary to deserialize.

        Returns:
            Model: the deserialized model.
        """
        return self.type.from_dict(value)


class Bool(Field):
    """
    A boolean Field.

    This field represents the built-in `bool` type.

    Examples:

        .. testsetup::

            from serde import Model, Bool

        Consider an example model with two `Bool` fields, one that will coerce
        things and one that won't.

        .. testcode::

            class Example(Model):
                enabled = Bool()
                something = Bool(coerce=True)

            example = Example.from_dict({'enabled': False, 'something': 'Test'})
            assert example.enabled is False
            assert example.something is True
    """

    def __init__(self, coerce=False, **kwargs):
        """
        Create a new Bool.

        Args:
            coerce (bool): whether to apply the `bool` constructor to the data
                before deserializing.
            **kwargs: keyword arguments for the `Field` constructor.
        """
        super().__init__(**kwargs)
        self.coerce = coerce

    def deserialize(self, value):
        """
        Deserialize the given value.

        Args:
            value: the value to deserialize.

        Returns:
            bool: the deserialized bool.
        """
        if self.coerce is True:
            value = bool(value)

        return value

    def validate(self, value):
        """
        Validate the deserialized value.

        Args:
            value: the value to validate.

        Raises:
            `~serde.error.ValidationError`: when the given value is invalid.
        """
        if not isinstance(value, bool):
            raise ValidationError('expected {!r} but got {!r}'
                                  .format(bool.__name__, value.__class__.__name__))


class Dict(Field):
    """
    A dict Field with a required key and value type.

    This field represents the built-in `dict` type. Each key and value will be
    serialized, deserialized, and validated with the specified key and value
    types. The key and value types can be specified using Field classes, Field
    instances, Model classes, or built-in types that have a corresponding Field
    type in this library.

    Examples:

        .. testsetup::

            from serde import Model, Dict

        Consider an example model with a constants attribute which is map of
        strings to floats.

        .. testcode::

            class Example(Model):
                constants = Dict(str, float)

            example = Example({'pi': 3.1415927, 'e': 2.7182818})
            assert example.constants['pi'] == 3.1415927
            assert example.constants['e'] ==  2.7182818

        Invalid keys and values that do not match the specified types will not
        be accepted, for example when instantiating

        .. doctest::

            >>> Example({'pi': '3.1415927'})
            Traceback (most recent call last):
                ...
            serde.error.ValidationError: expected 'float' but got 'str'

        Or when deserializing

        .. doctest::

            >>> Example.from_dict({'constants': {100: 3.1415927}})
            Traceback (most recent call last):
                ...
            serde.error.ValidationError: expected 'str' but got 'int'
    """

    def __init__(self, key=None, value=None, min_length=None, max_length=None, coerce=False,
                 **kwargs):
        """
        Create a new Dict.

        Args:
            key (Field): the Field class/instance for key's in this Dict.
            value (Field): the Field class/instance for values in this Dict.
            min_length (int): the minimum number of elements allowed.
            max_length (int): the maximum number of elements allowed.
            coerce (bool): whether to apply the `dict` constructor to the data
                before deserializing.
            **kwargs: keyword arguments for the `Field` constructor.
        """
        super().__init__(**kwargs)
        self.key = resolve_to_field_instance(key)
        self.value = resolve_to_field_instance(value)
        self.min_length = min_length
        self.max_length = max_length
        self.coerce = coerce

    def serialize(self, value):
        """
        Serialize the given value.

        Args:
            value: the value to serialize.

        Returns:
            dict: the serialized dictionary.
        """
        return {self.key.serialize(k): self.value.serialize(v) for k, v in value.items()}

    def deserialize(self, value):
        """
        Deserialize the given value.

        Args:
            value: the value to deserialize.

        Returns:
            dict: the deserialized dictionary.
        """
        if self.coerce is True:
            value = dict(value)

        return {self.key.deserialize(k): self.value.deserialize(v) for k, v in value.items()}

    def validate(self, value):
        """
        Validate the deserialized value.

        Args:
            value: the value to validate.

        Raises:
            `~serde.error.ValidationError`: when the given value is invalid.
        """
        if not isinstance(value, dict):
            raise ValidationError('expected {!r} but got {!r}'
                                  .format(dict.__name__, value.__class__.__name__))

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


class Float(Field):
    """
    A float Field.

    This field represents the built-in `float` type. But there are a few extra
    options to help constrain the Field further.

    Example:

        .. testsetup::

            from serde import Model, Float

        Consider an example model Point, with two `Float` fields, but we
        constrain the x and y such that the Point has to be in the second
        quadrant.

        .. testcode::

            class Point(Model):
                x = Float(max=0.0)
                y = Float(min=0.0)

            point = Point(-1.5, 5.5)

        Invalid values will not be accepted

        .. doctest::

            >>> Point(1.5, 5.5)
            Traceback (most recent call last):
                ...
            serde.error.ValidationError: expected at most 0.0 but got 1.5
    """

    def __init__(self, min=None, max=None, coerce=False, **kwargs):
        """
        Create a new Float.

        Args:
            min (float): the minimum value allowed.
            max (float): the maximum value allowed.
            coerce (bool): whether to apply the `float` constructor to the data
                before deserializing.
            **kwargs: keyword arguments for the `Field` constructor.
        """
        super().__init__(**kwargs)
        self.min = min
        self.max = max
        self.coerce = coerce

    def deserialize(self, value):
        """
        Deserialize the given value.

        Args:
            value: the value to deserialize.

        Returns:
            float: the deserialized integer.
        """
        if self.coerce is True:
            value = float(value)

        return value

    def validate(self, value):
        """
        Validate the deserialized value.

        Args:
            value: the value to validate.

        Raises:
            `~serde.error.ValidationError`: when the given value is invalid.
        """
        if not isinstance(value, float):
            raise ValidationError('expected {!r} but got {!r}'
                                  .format(float.__name__, value.__class__.__name__))

        if self.min is not None and value < self.min:
            raise ValidationError('expected at least {} but got {}'.format(self.min, value))

        if self.max is not None and value > self.max:
            raise ValidationError('expected at most {} but got {}'.format(self.max, value))


class Int(Field):
    """
    An integer Field.

    This field represents the built-in `int` type. But there are a few extra
    options to help constrain the Field further.

    Example:

        .. testsetup::

            from serde import Model, Int

        Consider an example model Point, with two `Int` fields, but we
        constrain the x and y such that the Point has to be in the second
        quadrant.

        .. testcode::

            class Point(Model):
                x = Int(max=0)
                y = Int(min=0)

            point = Point(-1, 5)

        Invalid values will not be accepted

        .. doctest::

            >>> Point(1, 5)
            Traceback (most recent call last):
                ...
            serde.error.ValidationError: expected at most 0 but got 1
    """

    def __init__(self, min=None, max=None, coerce=False, **kwargs):
        """
        Create a new Int.

        Args:
            min (int): the minimum value allowed.
            max (int): the maximum value allowed.
            coerce (bool): whether to apply the `int` constructor to the data
                before deserializing.
            **kwargs: keyword arguments for the `Field` constructor.
        """
        super().__init__(**kwargs)
        self.min = min
        self.max = max
        self.coerce = coerce

    def deserialize(self, value):
        """
        Deserialize the given value.

        Args:
            value: the value to deserialize.

        Returns:
            int: the deserialized integer.
        """
        if self.coerce is True:
            value = int(value)

        return value

    def validate(self, value):
        """
        Validate the deserialized value.

        Args:
            value: the value to validate.

        Raises:
            `~serde.error.ValidationError`: when the given value is invalid.
        """
        if not isinstance(value, int):
            raise ValidationError('expected {!r} but got {!r}'
                                  .format(int.__name__, value.__class__.__name__))

        if self.min is not None and value < self.min:
            raise ValidationError('expected at least {} but got {}'.format(self.min, value))

        if self.max is not None and value > self.max:
            raise ValidationError('expected at most {} but got {}'.format(self.max, value))


class List(Field):
    """
    A list Field with a required element type.

    This field represents the built-in `list` type. Each element will be
    serialized, deserialized, and validated with the specified element type. The
    element type can be specified using Field classes, Field instances, Model
    classes, or built-in types that have a corresponding Field type in this
    library.

    Examples:

        .. testsetup::

            from serde import Model, List

        Consider a user model that can have multiple emails

        .. testcode::

            class User(Model):
                emails = List(str, min_length=1, default=[])

            user = User(['john@smith.com', 'john.smith@email.com'])
            assert user.emails[0] == 'john@smith.com'
            assert user.emails[1] == 'john.smith@email.com'

        Invalid elements that do not match the specified type will not be
        accepted, for example when instantiating

        .. doctest::

            >>> User(emails={'john@smith.com': None })
            Traceback (most recent call last):
                ...
            serde.error.ValidationError: expected 'list' but got 'dict'

        Or when deserializing

        .. doctest::

            >>> User.from_dict({'emails': [1234]})
            Traceback (most recent call last):
                ...
            serde.error.ValidationError: expected 'str' but got 'int'
    """

    def __init__(self, field=None, min_length=None, max_length=None, coerce=False, **kwargs):
        """
        Create a new List.

        Args:
            field (Field): the Field class/instance for this List's elements.
            min_length (int): the minimum number of elements allowed.
            max_length (int): the maximum number of elements allowed.
            coerce (bool): whether to apply the `list` constructor to the data
                before deserializing.
            **kwargs: keyword arguments for the `Field` constructor.
        """
        super().__init__(**kwargs)
        self.field = resolve_to_field_instance(field)
        self.min_length = min_length
        self.max_length = max_length
        self.coerce = coerce

    def serialize(self, value):
        """
        Serialize the given value.

        Args:
            value: the value to serialize.

        Returns:
            list: the serialized list.
        """
        return [self.field.serialize(v) for v in value]

    def deserialize(self, value):
        """
        Deserialize the given value.

        Args:
            value: the value to deserialize.

        Returns:
            list: the deserialized list.
        """
        if self.coerce is True:
            value = list(value)

        return [self.field.deserialize(v) for v in value]

    def validate(self, value):
        """
        Validate the deserialized value.

        Args:
            value: the value to validate.

        Raises:
            `~serde.error.ValidationError`: when the given value is invalid.
        """
        if not isinstance(value, list):
            raise ValidationError('expected {!r} but got {!r}'
                                  .format(list.__name__, value.__class__.__name__))

        count = len(value)

        if self.min_length is not None and count < self.min_length:
            raise ValidationError('expected at least {} elements but got {} elements'
                                  .format(self.min_length, count))

        if self.max_length is not None and count > self.max_length:
            raise ValidationError('expected at most {} elements but got {} elements'
                                  .format(self.max_length, count))

        for v in value:
            self.field.validate(v)


class Str(Field):
    """
    A string Field.

    This field represents the built-in `str` type. But there are a few extra
    options to help constrain the Field further.

    Example:

        .. testsetup::

            from serde import Model, Str

        Consider an example model User

        .. testcode::

            class User(Model):
                name = Str(min_length=1, strip=True)
                address = Str(required=False)

            user = User.from_dict({'name': '    George Clooney  '})
            assert user.name == 'George Clooney'

        Invalid values will not be accepted

        .. doctest::

            >>> User('')
            Traceback (most recent call last):
                ...
            serde.error.ValidationError: expected at least 1 characters but got 0 characters
    """

    def __init__(self, min_length=None, max_length=None, strip=False, coerce=False, **kwargs):
        """
        Create a new Str.

        Args:
            min_length (int): the minimum number of characters allowed.
            max_length (int): the maximum number of characters allowed.
            strip (bool): whether to call `str.strip()` the data when
                deserializing.
            coerce (bool): whether to apply the `str` constructor to the data
                before deserializing. Warning: all this does is apply the `str`
                constructor so it can have unexpected interactions. For example

                .. doctest::

                    >>> value = b'some bytes'
                    >>> str(value)
                    "b'some bytes'"

            **kwargs: keyword arguments for the `Field` constructor.
        """
        super().__init__(**kwargs)
        self.min_length = min_length
        self.max_length = max_length
        self.strip = strip
        self.coerce = coerce

    def deserialize(self, value):
        """
        Deserialize the given value.

        Args:
            value: the value to deserialize.

        Returns:
            int: the deserialized integer.
        """
        if self.coerce is True:
            value = str(value)

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
        if not isinstance(value, str):
            raise ValidationError('expected {!r} but got {!r}'
                                  .format(str.__name__, value.__class__.__name__))

        count = len(value)

        if self.min_length is not None and count < self.min_length:
            raise ValidationError('expected at least {} characters but got {} characters'
                                  .format(self.min_length, count))

        if self.max_length is not None and count > self.max_length:
            raise ValidationError('expected at most {} characters but got {} characters'
                                  .format(self.max_length, count))


class Tuple(Field):
    """
    A tuple Field with required element types.

    Each element will be serialized, deserialized, and validated with the
    specified element type. The given element types can be specified using Field
    classes, Field instances, Model classes, or built-in types that have a
    corresponding Field type in this library.

    Examples:

        .. testsetup::

            from serde import Model, Str, Tuple

        Consider an example person that has a name and a birthday

        .. testcode::

            class Person(Model):
                name = Str()
                birthday = Tuple(int, str, int)

            person = Person('Ross MacArthur', (19, 'June', 1994))
            assert person.name == 'Ross MacArthur'
            assert person.birthday[0] == 19
            assert person.birthday[1] == 'June'
            assert person.birthday[2] == 1994

        Invalid keys and values that do not match the specified types will not
        be accepted, for example when instantiating

        .. doctest::

            >>> Person('Beyonce', birthday=(4, 'September'))
            Traceback (most recent call last):
                ...
            serde.error.ValidationError: expected 3 elements but got 2 elements

        Or when deserializing

        .. doctest::

            >>> Person.from_dict({'name': 'Beyonce', 'birthday': (4, 9, 1994)})
            Traceback (most recent call last):
                ...
            serde.error.ValidationError: expected 'str' but got 'int'
    """

    def __init__(self, *fields, coerce=False, **kwargs):
        """
        Create a new Tuple.

        Args:
            *fields (Field): the Field classes/instances for elements in this
                Tuple.
            coerce (bool): whether to apply the `tuple` constructor to the data
                before deserializing.
            **kwargs: keyword arguments for the `Field` constructor.
        """
        super().__init__(**kwargs)
        self.fields = tuple(resolve_to_field_instance(f, none_allowed=False) for f in fields)
        self.coerce = coerce

    def serialize(self, value):
        """
        Serialize the given value.

        Args:
            value: the value to serialize.

        Returns:
            tuple: the serialized tuple.
        """
        return tuple(f.serialize(v) for f, v in zip_equal(self.fields, value))

    def deserialize(self, value):
        """
        Deserialize the given value.

        Args:
            value: the value to deserialize.

        Returns:
            tuple: the deserialized tuple.
        """
        if self.coerce is True:
            value = tuple(value)

        return tuple(f.deserialize(v) for f, v in zip_equal(self.fields, value))

    def validate(self, value):
        """
        Validate the deserialized value.

        Args:
            value: the value to validate.

        Raises:
            `~serde.error.ValidationError`: when the given value is invalid.
        """
        if not isinstance(value, tuple):
            raise ValidationError('expected {!r} but got {!r}'
                                  .format(tuple.__name__, value.__class__.__name__))

        if len(self.fields) != len(value):
            raise ValidationError('expected {} elements but got {} elements'
                                  .format(len(self.fields), len(value)))

        for f, v in zip(self.fields, value):
            f.validate(v)
