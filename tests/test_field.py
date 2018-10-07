from collections import OrderedDict
from uuid import UUID

from pytest import raises

from serde.error import ValidationError
from serde.field import (Array, Boolean, Bytes, Dictionary, Field, Float,
                         InstanceField, Integer, List, Map, ModelField, Parts,
                         String, Tuple, TypeField, resolve_to_field_instance)
from serde.model import Model


class Stringify(Field):

    def serialize(self, value):
        return str(value)

    def deserialize(self, value):
        return eval(value)


class TestField:

    def test___init__(self):
        field = Field()

        assert field.id == 0
        assert field.name is None
        assert field.required is True
        assert field.default is None
        assert field.validators == []

        # A second Field instantiated should have a higher counter.
        field2 = Field()
        assert field2.id == 1

        # A Field with extra options set.
        field = Field(name='test', required=False, default=lambda m: 5, validators=[None])
        assert field.name == 'test'
        assert field.required is False
        assert callable(field.default)
        assert field.validators == [None]

    def test_serialize(self):
        field = Field()

        # The base field simply passes things through.
        for value in (None, 0, 'string', object(), type):
            field.serialize(value) == value

    def test_deserialize(self):
        field = Field()

        # The base field simply passes things through.
        for value in (None, 0, 'string', object(), type):
            field.deserialize(value) == value

    def test_validate(self):
        field = Field()

        # Everything is okay on a base field.
        for value in (None, 0, 'string', object(), type):
            field.validate(value)


class TestInstanceField:

    def test___init__(self):
        # You must extend a InstanceField and you should not be able to
        # instantiate it directly.
        with raises(TypeError):
            InstanceField()

        class Example(InstanceField):
            type = int

        example = Example(required=False, validators=[None])
        assert example.required is False
        assert example.validators == [None]

        class Example(InstanceField):
            pass

        # You should not be able to instantiate an InstanceField that has not
        # set the "type" attribute.
        with raises(AttributeError):
            Example()

    def test_serialize(self):
        class Example(InstanceField):
            type = int

        example = Example()

        # Validation only happens when this Field is part of a Model. So it
        # still passes all values through.
        for value in (None, 0, 'string', object(), type):
            example.serialize(value) == value

    def test_deserialize(self):
        class Example(InstanceField):
            type = int

        example = Example()

        # Validation only happens when this Field is part of a Model. So it
        # still passes all values through.
        for value in (None, 0, 'string', object(), type):
            example.deserialize(value) == value

    def test_validate(self):
        class Example(InstanceField):
            type = int

        example = Example()

        # All integers should pass the validation.
        example.validate(-1000)
        example.validate(0)
        example.validate(1000)

        # Anything that is not an int should raise a ValidationError.
        for value in (None, 20.0, 'string', object, type):
            with raises(ValidationError):
                example.validate(value)


class TestTypeField:

    def test___init__(self):
        example = TypeField(int)

        assert example.type == int
        assert example.required is True
        assert example.validators == []

        example = TypeField(int, required=False, validators=[None])
        assert example.type == int
        assert example.required is False
        assert example.validators == [None]

    def test_serialize(self):
        example = TypeField(int)

        # Validation only happens when this Field is part of a Model. So it
        # still passes all values through.
        for value in (None, 0, 'string', object(), type):
            example.serialize(value) == value

    def test_deserialize(self):
        example = TypeField(int)

        # Validation only happens when this Field is part of a Model. So it
        # still passes all values through.
        for value in (None, 0, 'string', object(), type):
            example.deserialize(value) == value

    def test_validate(self):
        example = TypeField(int)

        # All integers should pass the validation.
        example.validate(-1000)
        example.validate(0)
        example.validate(1000)

        # Anything that is not an int should raise a ValidationError.
        for value in (None, 20.0, 'string', object, type):
            with raises(ValidationError):
                example.validate(value)


class TestArray:

    def test_serialize(self):
        # A field that must be a list of Stringifys.
        example = Array(Stringify)

        # Validation only happens when this Field is part of a Model. So it
        # still passes any Iterable value through.
        for value in ((), [], {}):
            example.serialize(value) == value

        # Any value that is not an Iterable will raise a TypeError
        for value in (None, 20.0, object, type):
            with raises(TypeError):
                example.serialize(value)

        # Serialize calls the subfield serialize method.
        assert example.serialize([False, ['s'], {'a': 5}]) == ['False', "['s']", "{'a': 5}"]

    def test_deserialize(self):
        # A field that must be a list of Stringifys.
        example = Array(Stringify)

        # Validation only happens when this Field is part of a Model. So it
        # still passes any Iterable value through.
        for value in ((), [], {}):
            example.deserialize(value) == value

        # Any value that is not an Iterable will raise a TypeError
        for value in (None, 20.0, object, type):
            with raises(TypeError):
                example.deserialize(value)

        # Deserialize calls the subfield deserialize method.
        assert example.deserialize(['False', "['s']", "{'a': 5}"]) == [False, ['s'], {'a': 5}]

    def test_validate(self):
        # A field that must be a list of Stringifys.
        example = Array(Stringify)

        # A list of Stringyfiable types will pass validation.
        example.validate([False, ['s'], {'a': 5}])

        # Any value that is not an Iterable will raise a ValidationError
        for value in (None, 20.0, object, type):
            with raises(ValidationError):
                example.validate(value)


class TestMap:

    def test_serialize(self):
        # A field that is a key value pair of Strings and Stringifys.
        example = Map(String, Stringify)

        # Validation only happens when this Field is part of a Model. So it
        # still passes any Dict like value through.
        for value in ({}, OrderedDict()):
            example.serialize(value) == value

        # Any value that is not an Dictionary will raise a AttributeError
        # because it doesn't have the `.items()` method.
        for value in (None, 20.0, object, type):
            with raises(AttributeError):
                example.serialize(value)

        # Serialize calls the key and value serialize methods.
        assert example.serialize({'a': False, 'b': ['s'], 'c': {'a': 5}}) == \
            {'a': 'False', 'b': "['s']", 'c': "{'a': 5}"}

    def test_deserialize(self):
        # A field that is a key value pair of Strings and Stringifys.
        example = Map(String, Stringify)

        # Validation only happens when this Field is part of a Model. So it
        # still passes any Dict like value through.
        for value in ({}, OrderedDict()):
            example.deserialize(value) == value

        # Any value that is not an Dictionary will raise a AttributeError
        # because it doesn't have the `.items()` method.
        for value in (None, 20.0, object, type):
            with raises(AttributeError):
                example.deserialize(value)

        # Deserialize calls the subfield deserialize method.
        assert example.deserialize({'a': 'False', 'b': "['s']", 'c': "{'a': 5}"}) == \
            {'a': False, 'b': ['s'], 'c': {'a': 5}}

    def test_validate(self):
        # A field that is a key value pair of Strings and Stringifys.
        example = Map(String, Stringify)

        # A list of Stringifyiable serializable types will pass validation.
        example.validate({'a': False, 'b': ['s'], 'c': {'a': 5}})

        # Any value that is not an Dictionary will raise a ValidationError
        for value in (None, 20.0, object, type):
            with raises(ValidationError):
                example.validate(value)

        # A dictionary of with keys that aren't Strings should fail validation.
        with raises(ValidationError):
            example.validate({5: 'hello'})


class TestParts:

    def test_serialize(self):
        # A field that is a tuple (bool, str, Stringify)
        example = Parts(Boolean, String, Stringify)

        # Validation only happens when this Field is part of a Model. So it
        # still passes any Iterable value through as long as its the correct
        # length.
        for value in ((None, None, None), [None, None, None]):
            example.serialize(value) == value

        # Any value that is not an Iterable will raise a TypeError
        for value in (None, 20.0, object, type):
            with raises(TypeError):
                example.serialize(value)

        # Serialize calls the subfields serialize methods.
        assert example.serialize((True, 'test', {'a': 5})) == (True, 'test', "{'a': 5}")

    def test_deserialize(self):
        # A field that is a tuple (bool, str, Stringify)
        example = Parts(Boolean, String, Stringify)

        # Validation only happens when this Field is part of a Model. So it
        # still passes any Iterable value through as long as its the correct
        # length.
        for value in ((None, None, 'None'), [None, None, 'None']):
            example.deserialize(value) == value

        # Any value that is not an Iterable will raise a TypeError
        for value in (None, 20.0, object, type):
            with raises(TypeError):
                example.deserialize(value)

        # Serialize calls the subfields deserialize methods.
        assert example.deserialize((True, 'test', "{'a': 5}")) == (True, 'test', {'a': 5})

    def test_validate(self):
        # A field that is a tuple (bool, str, Stringify)
        example = Parts(Boolean, String, Stringify)

        # A list of a tuple that will pass validation.
        example.validate((True, 'test', None))

        # Any value that is not an Tuple will raise a ValidationError
        for value in (None, 20.0, [None, None, None], object, type, (None, None)):
            with raises(ValidationError):
                example.validate(value)

        # A tuple with the incorrect types should also fail with a
        # ValidationError
        with raises(ValidationError):
            example.validate((None, 'test', None))


def test_resolve_to_field_instance():
    # An instance of a field should work
    assert resolve_to_field_instance(Field()) == Field()

    # A Field class should work
    assert resolve_to_field_instance(Field) == Field()

    # A Model class should work
    class Example(Model):
        pass

    assert resolve_to_field_instance(Example) == ModelField(Example)

    # All the base types should resolve correctly
    assert resolve_to_field_instance(bool) == Boolean()
    assert resolve_to_field_instance(bytes) == Bytes()
    assert resolve_to_field_instance(dict) == Dictionary()
    assert resolve_to_field_instance(float) == Float()
    assert resolve_to_field_instance(int) == Integer()
    assert resolve_to_field_instance(list) == List()
    assert resolve_to_field_instance(str) == String()
    assert resolve_to_field_instance(tuple) == Tuple()

    # Arbitrary types should resolve to a TypeField for that type
    assert resolve_to_field_instance(UUID) == TypeField(UUID)

    # A Model instance should not work
    with raises(TypeError):
        resolve_to_field_instance(Example())

    with raises(TypeError):
        resolve_to_field_instance(Example())
