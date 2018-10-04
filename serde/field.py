"""
Field types for Serde Models.
"""

from .error import ValidationError
from .util import zip_equal


class Field:
    """
    A field on a Model.

    Handles serializing, deserializing, and validation of individual values.
    """

    # This is so we can get the order the fields were instantiated in. If not
    # done this would cause problems when creating the Model's __init__ method,
    # because we wouldn't know the order of the Field arguments.
    __counter__ = 0

    def __init__(self, optional=False, rename=None, validators=None):
        """
        Create a new Field.

        Args:
            optional (bool): whether this field is required for deserialization.
            rename (Text): use this name for the field when serialializing and
                expect this name when deserializing.
            validators (List[Callable]): a list of validator functions taking
                `(self, value)` as arguments. The functions need to raise an
                `Exception` if they fail.
        """
        super().__init__()

        self.counter = Field.__counter__
        Field.__counter__ += 1

        self.optional = optional
        self.rename = rename
        self.validators = validators or []

    def __eq__(self, other):
        """
        Whether two Fields are the same.

        Args:
            other (Field): the field to compare to.

        Returns:
            bool: True if equal, else False.
        """
        return (isinstance(other, self.__class__) and
                self.optional == other.optional and
                self.rename == other.rename and
                self.validators == other.validators)

    def serialize(self, value):
        """
        Serialize the given value according to this Field's specification.

        Args:
            value (Any): the value to serialize.

        Returns:
            Any: the serialized value.
        """
        return value

    def deserialize(self, value):
        """
        Deserialize the given value according to this Field's specification.

        Args:
            value (Any): the value to deserialize.

        Returns:
            Any: the deserialized value.
        """
        return value

    def validate(self, value):
        """
        Validate the deserialized value.

        Args:
            value (Any): the value to validate.
        """
        pass


class InstanceField(Field):
    """
    A Field that simply validates that a value is an instance of a type.
    """

    def __init__(self, **kwargs):
        """
        Create a new InstanceField.

        Args:
            **kwargs: keyword arguments for the Field constructor.

        Raises:
            SerdeError: raised if the subclass did not set the attribute "type".
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
            value (Any): the value to validate.

        Raises:
            ValidationError: when the given value is not an instance of the
                specified type.
        """
        if not isinstance(value, self.__class__.type):
            raise ValidationError('expected {!r} but got {!r}'
                                  .format(self.__class__.type.__name__, value.__class__.__name__))


class TypeField(Field):
    """
    A Field that simply validates that a value is an instance of the given type.
    """

    def __init__(self, type, **kwargs):
        """
        Create a new TypeField.

        Args:
            type: the type that this field wraps.
            **kwargs: keyword arguments for the Field constructor.
        """
        super().__init__(**kwargs)
        self.type = type

    def validate(self, value):
        """
        Validate the deserialized value.

        Args:
            value (Any): the value to validate.

        Raises:
            ValidationError: when the given value is not an instance of the
                specified type.
        """
        if not isinstance(value, self.type):
            raise ValidationError('expected {!r} but got {!r}'
                                  .format(self.type.__name__, value.__class__.__name__))


class ModelField(TypeField):
    """
    A Field for sub-Models.
    """

    def serialize(self, value):
        """
        Serialize the given Model into a dictionary.

        Args:
            value (Model): the model to serialize.

        Returns:
            Dict: the serialized dictionary.
        """
        return value.to_dict()

    def deserialize(self, value):
        """
        Deserialize the given dictionary into a Model.

        Args:
            value (Dict): the dictionary to deserialize.

        Returns:
            Model: the deserialized model.
        """
        return self.type.from_dict(value)


class Boolean(InstanceField):
    """
    A Field for the built-in `bool` type.
    """
    type = bool


class Bytes(InstanceField):
    """
    A Field for the built-in `bytes` type.
    """
    type = bytes


class Dictionary(InstanceField):
    """
    A Field for the built-in `dict` type.
    """
    type = dict


class Float(InstanceField):
    """
    A Field for the built-in `float` type.
    """
    type = float


class Integer(InstanceField):
    """
    A Field for the built-in `int` type.
    """
    type = int


class List(InstanceField):
    """
    A Field for the built-in `list` type.
    """
    type = list


class String(InstanceField):
    """
    A Field for the built-in `str` type.
    """
    type = str


class Tuple(InstanceField):
    """
    A Field for the built-in `tuple` type.
    """
    type = tuple


def resolve_to_field_instance(thing):
    """
    Resolve an arbitrary object to a Field instance.

    Args:
        thing (Any): the object to resolve to a Field instance.

    Returns:
        Field: a field instance.
    """
    from serde.model import Model

    # If the thing is a Field then thats great.
    if isinstance(thing, Field):
        return thing

    try:
        # If the thing is a subclass of Field then create an instance.
        if issubclass(thing, Field):
            return thing()

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
    """

    def __init__(self, field, **kwargs):
        """
        Create a new Array.

        Args:
            field (Field): the Field class for this Array's elements.
            **kwargs: keyword arguments for the Field constructor.
        """
        super().__init__(**kwargs)
        self.field = resolve_to_field_instance(field)

    def serialize(self, value):
        """
        Serialize the given value.

        Args:
            value (Iterable): the value to serialize.

        Returns:
            List[Any]: the serialized list.
        """
        return [self.field.serialize(v) for v in value]

    def deserialize(self, value):
        """
        Deserialize the given value.

        Args:
            value (Iterable): the value to deserialize.

        Returns:
            List[Any]: the deserialized list.
        """
        return [self.field.deserialize(v) for v in value]

    def validate(self, value):
        """
        Validate the deserialized value.

        Args:
            value (Any): the value to validate.

        Raises:
            ValidationError: when the given value is invalid.
        """
        if not isinstance(value, list):
            raise ValidationError('expected {!r} but got {!r}'
                                  .format(list.__name__, value.__class__.__name__))

        for v in value:
            self.field.validate(v)


class Map(Field):
    """
    A Dictionary Field with a required key and value type.
    """

    def __init__(self, key, value, **kwargs):
        """
        Create a new Map.

        Args:
            key (Field): the Field class for key's in this Map.
            value (Field): the Field class for values in this Map.
            **kwargs: keyword arguments for the Field constructor.
        """
        super().__init__(**kwargs)
        self.key = resolve_to_field_instance(key)
        self.value = resolve_to_field_instance(value)

    def serialize(self, value):
        """
        Serialize the given value.

        Args:
            value (Dict): the value to serialize.

        Returns:
            Dict: the serialized dictionary.
        """
        return {self.key.serialize(k): self.value.serialize(v) for k, v in value.items()}

    def deserialize(self, value):
        """
        Deserialize the given value.

        Args:
            value (Dict): the value to deserialize.

        Returns:
            Dict: the deserialized dictionary.
        """
        return {self.key.deserialize(k): self.value.deserialize(v) for k, v in value.items()}

    def validate(self, value):
        """
        Validate the deserialized value.

        Args:
            value (Any): the value to validate.

        Raises:
            ValidationError: when the given value is invalid.
        """
        if not isinstance(value, dict):
            raise ValidationError('expected {!r} but got {!r}'
                                  .format(dict.__name__, value.__class__.__name__))

        for k, v in value.items():
            self.key.validate(k)
            self.value.validate(v)


class Parts(Tuple):
    """
    A Tuple Field with required element types.
    """

    def __init__(self, *fields, **kwargs):
        """
        Create a new Parts.

        Args:
            *fields (Field): the Field classes for elements in this Parts.
            **kwargs: keyword arguments for the Field constructor.
        """
        super().__init__(**kwargs)
        self.fields = tuple(resolve_to_field_instance(f) for f in fields)

    def serialize(self, value):
        """
        Serialize the given value.

        Args:
            value (Tuple): the value to serialize.

        Returns:
            Tuple: the serialized tuple.
        """
        return tuple(f.serialize(v) for f, v in zip_equal(self.fields, value))

    def deserialize(self, value):
        """
        Deserialize the given value.

        Args:
            value (Tuple): the value to deserialize.

        Returns:
            Tuple: the deserialized tuple.
        """
        return tuple(f.deserialize(v) for f, v in zip_equal(self.fields, value))

    def validate(self, value):
        """
        Validate the deserialized value.

        Args:
            value (Any): the value to validate.

        Raises:
            ValidationError: when the given value is invalid.
        """
        if not isinstance(value, tuple):
            raise ValidationError('expected {!r} but got {!r}'
                                  .format(tuple.__name__, value.__class__.__name__))

        if len(self.fields) != len(value):
            raise ValidationError('expected {} length tuple but got length {}'
                                  .format(len(self.fields), len(value)))

        for f, v in zip(self.fields, value):
            f.validate(v)
