"""
Field types for Serde Models.
"""

from .error import ValidationError
from .util import zip_equal


class Field:
    """
    A field on a `~serde.model.Model`.

    Fields handle serializing, deserializing, and validation of individual
    values for Model objects.

    Examples:

        Here is a simple example of how Fields can be used on a Model. In this
        example we use the base class Field which does not have any of its own
        validation, and simply passes values through when serializing and
        deserializing.

        .. testsetup::

            from serde import Model, Field

        .. testcode::

            def assert_is_positive(model, value):
                assert value >= 0

            class Person(Model):
                name = Field()
                age = Field(optional=True, validators=[assert_is_positive])
                favourite_color = Field(optional=True, default='pink')

            person = Person('William Shakespeare', age=454)
            assert person.name == 'William Shakespeare'
            assert person.age == 454
            assert person.favourite_color == 'pink'

        Here is a more advanced example where we subclass a field and override
        the serialize, deserialize, and validate methods. As well as use a
        function to generate a Fields default value.

        .. testcode::

            from uuid import UUID, uuid4

            class Uuid(Field):

                def serialize(self, value):
                    return str(value)

                def deserialize(self, value):
                    return UUID(value)

                def validate(self, value):
                    assert isinstance(value, UUID)

            class User(Model):
                key = Uuid(default=lambda _: uuid4())
                email = String()

            user = User('john@smith.com')
            assert isinstance(user.key, UUID)
            assert user.email == 'john@smith.com'
    """

    # This is so we can get the order the fields were instantiated in. If not
    # done this would cause problems when creating the Model's __init__ method,
    # because we wouldn't know the order of the Field arguments.
    __counter__ = 0

    def __init__(self, optional=False, name=None, default=None, validators=None):
        """
        Create a new Field.

        Args:
            optional (bool): whether this field is optional. Optional fields are
                not required to be present in deserialization, will become
                kwargs on the `Model.__init__` method, and will not be
                serialized if they are None.
            name: override the name for the field when serializing and expect
                this name when deserializing. This can also be a function that
                generates a value. The function needs to take the containing
                `~serde.model.Model` and the default name as arguments.
            default: a value to use if the field value is None. This can also be
                a function that generates the default. The function needs to
                take the containing `~serde.model.Model` as an argument.
            validators (list): a list of validator functions taking
                `~serde.model.Model` and the value as arguments. The functions
                need to raise an `Exception` if they fail.
        """
        super().__init__()

        self.counter = Field.__counter__
        Field.__counter__ += 1

        self.optional = optional
        self.name = name
        self.default = default
        self.validators = validators or []

    def __eq__(self, other):
        """
        Whether two Fields are the same.
        """
        return (isinstance(other, self.__class__) and
                self.optional == other.optional and
                self.name == other.name and
                self.default == other.default and
                self.validators == other.validators)

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
    A `Field` that validates a value is an instance of a type.

    Attributes:
        type (type): the type to validate for this InstanceField.
    """

    def __init__(self, **kwargs):
        """
        Create a new InstanceField.

        Args:
            **kwargs: keyword arguments for the `Field` constructor.
        """
        if type(self) == InstanceField:
            raise TypeError('{!r} class must be subclassed'
                            .format(self.__class__.__name__))

        attr = 'type'
        if not hasattr(self.__class__, attr):
            raise AttributeError('{!r} class must set the attribute {!r}'
                                 .format(self.__class__.__name__, attr))

        super().__init__(**kwargs)

    def validate(self, value):
        """
        Validate the deserialized value.

        Args:
            value: the value to validate.

        Raises:
            `~serde.error.ValidationError`: when the given value is not an
                instance of the specified type.
        """
        if not isinstance(value, self.__class__.type):
            raise ValidationError('expected {!r} but got {!r}'
                                  .format(self.__class__.type.__name__, value.__class__.__name__))


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

    This is wrapper Field for sub-Model fields. The serialize and deserialize
    methods call the `~serde.model.Model.to_dict()` and
    `~serde.model.Model.from_dict()`  methods on the Model class. This allows
    complex nested Models.

    Examples:

        .. testsetup::

            from serde import Model, ModelField, String, Integer

        Consider a person model that has a birthday

        .. testcode::

            class Birthday(Model):
                day = Integer()
                month = String()

            class Person(Model):
                name = String()
                birthday = ModelField(Birthday, optional=True)

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
        Serialize the given `Model` into a dictionary.

        Args:
            value (Model): the model to serialize.

        Returns:
            dict: the serialized dictionary.
        """
        return value.to_dict()

    def deserialize(self, value):
        """
        Deserialize the given dictionary into a `Model`.

        Args:
            value (dict): the dictionary to deserialize.

        Returns:
            Model: the deserialized model.
        """
        return self.type.from_dict(value)


class Boolean(InstanceField):
    """
    A `Field` for the built-in `bool` type.
    """
    type = bool


class Bytes(InstanceField):
    """
    A `Field` for the built-in `bytes` type.
    """
    type = bytes


class Dictionary(InstanceField):
    """
    A `Field` for the built-in `dict` type.
    """
    type = dict


class Float(InstanceField):
    """
    A `Field` for the built-in `float` type.
    """
    type = float


class Integer(InstanceField):
    """
    A `Field` for the built-in `int` type.
    """
    type = int


class List(InstanceField):
    """
    A `Field` for the built-in `list` type.
    """
    type = list


class String(InstanceField):
    """
    A `Field` for the built-in `str` type.
    """
    type = str


class Tuple(InstanceField):
    """
    A `Field` for the built-in `tuple` type.
    """
    type = tuple


def resolve_to_field_instance(thing):
    """
    Resolve an arbitrary object to a `Field` instance.

    Args:
        thing (object): anything to resolve to a Field instance.

    Returns:
        Field: a field instance.
    """
    # We import Model here to avoid circular dependency problems.
    from serde.model import Model

    # If the thing is a Field then thats great.
    if isinstance(thing, Field):
        return thing

    try:
        # If the thing is a subclass of Field then attempt to create an
        # instance. This could fail the Field expects arguments.
        if issubclass(thing, Field):
            return thing()
    except TypeError:
        pass

    try:
        # If the thing is a subclass of Model then create a ModelField instance.
        if issubclass(thing, Model):
            return ModelField(thing)
    except TypeError:
        pass

    # If the thing is one of the supported base types, then return an instance
    # of the corresponding Field type.
    type_map = {
        bool: Boolean,
        bytes: Bytes,
        dict: Dictionary,
        float: Float,
        int: Integer,
        list: List,
        str: String,
        tuple: Tuple
    }
    if thing in type_map:
        return type_map[thing]()

    # If the thing is a type then create a TypeField with that type.
    if isinstance(thing, type):
        return TypeField(thing)

    raise TypeError('{!r} is not a Field, an instance of a Field, or a type'.format(thing))


class Array(Field):
    """
    A List Field with a required element type.

    Each element in the list will be serialized, deserialized, and validated
    with the specified type.

    Examples:

        .. testsetup::

            from serde import Model, Array, String

        Consider a user model that can have multiple emails

        .. testcode::

            class User(Model):
                emails = Array(String, default=[])

            user = User(['john@smith.com', 'john.smith@email.com'])
            assert user.emails[0] == 'john@smith.com'
            assert user.emails[1] == 'john.smith@email.com'

        Invalid keys and values that do not match the specified type will not be
        accepted, for example when instantiating

        .. doctest::

            >>> User({})
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

    def __init__(self, field, **kwargs):
        """
        Create a new Array.

        Args:
            field (Field): the Field class/instance for this Array's elements.
            **kwargs: keyword arguments for the `Field` constructor.
        """
        super().__init__(**kwargs)
        self.field = resolve_to_field_instance(field)

    def serialize(self, value):
        """
        Serialize the given value.

        Args:
            value (Iterable): the value to serialize.

        Returns:
            list: the serialized list.
        """
        return [self.field.serialize(v) for v in value]

    def deserialize(self, value):
        """
        Deserialize the given value.

        Args:
            value (Iterable): the value to deserialize.

        Returns:
            list: the deserialized list.
        """
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

        for v in value:
            self.field.validate(v)


class Map(Field):
    """
    A Dictionary Field with a required key and value type.

    Each key and value will be serialized, deserialized, and validated with the
    specified key and value types.

    Examples:

        .. testsetup::

            from serde import Model, Map, String, Float

        Consider an example model with a constants attribute which is map of
        strings to floats

        .. testcode::

            class Example(Model):
                constants = Map(String, Float)

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

    def __init__(self, key, value, **kwargs):
        """
        Create a new Map.

        Args:
            key (Field): the Field class/instance for key's in this Map.
            value (Field): the Field class/instance for values in this Map.
            **kwargs: keyword arguments for the `Field` constructor.
        """
        super().__init__(**kwargs)
        self.key = resolve_to_field_instance(key)
        self.value = resolve_to_field_instance(value)

    def serialize(self, value):
        """
        Serialize the given value.

        Args:
            value (dict): the value to serialize.

        Returns:
            dict: the serialized dictionary.
        """
        return {self.key.serialize(k): self.value.serialize(v) for k, v in value.items()}

    def deserialize(self, value):
        """
        Deserialize the given value.

        Args:
            value (dict): the value to deserialize.

        Returns:
            dict: the deserialized dictionary.
        """
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

        for k, v in value.items():
            self.key.validate(k)
            self.value.validate(v)


class Parts(Field):
    """
    A Tuple Field with required element types.

    Each element will be serialized, deserialized, and validated with the
    specified element type.

    Examples:

        .. testsetup::

            from serde import Model, Parts, Integer, String

        Consider an example person that has a name and a birthday

        .. testcode::

            class Person(Model):
                name = String()
                birthday = Parts(Integer, String, Integer)

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

    def __init__(self, *fields, **kwargs):
        """
        Create a new Parts.

        Args:
            *fields (Field): the Field classes/instances for elements in this
                Parts.
            **kwargs: keyword arguments for the `Field` constructor.
        """
        super().__init__(**kwargs)
        self.fields = tuple(resolve_to_field_instance(f) for f in fields)

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
