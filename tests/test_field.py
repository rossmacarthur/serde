import uuid
from collections import OrderedDict

from pytest import raises

from serde import (
    Bool, Choice, Dict, Domain, Email, Field, Float, Instance, Int, List,
    Model, Nested, SerdeError, Slug, Str, Tuple, Url, Uuid, ValidationError
)
from serde.field import create, resolve_to_field_instance


class Stringify(Field):

    def serialize(self, value):
        return str(value)

    def deserialize(self, value):
        return eval(value)


class TestField:

    def test___init__(self):
        field = Field()

        assert field.id >= 0
        assert field.rename is None
        assert field.required is True
        assert field.default is None
        assert field.validators == []

        # A second Field instantiated should have a higher counter.
        field2 = Field()
        assert field2.id > field.id

        # A Field with extra options set.
        field = Field(rename='test', required=False, default=5, validators=[None])
        assert field.rename == 'test'
        assert field.required is False
        assert field.default == 5
        assert field.validators == [None]

    def test__setattr__(self):
        field = Field()

        with raises(SerdeError):
            class Example(Model):
                a = field
                b = field

    def test_name(self):
        field = Field()

        with raises(SerdeError):
            field.name()

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


class TestInstance:

    def test___init__(self):
        example = Instance(int)

        assert example.type == int
        assert example.required is True
        assert example.validators == []

        example = Instance(int, required=False, validators=[None])
        assert example.type == int
        assert example.required is False
        assert example.validators == [None]

    def test_serialize(self):
        example = Instance(int)

        # Validation only happens when this Field is part of a Model. So it
        # still passes all values through.
        for value in (None, 0, 'string', object(), type):
            example.serialize(value) == value

    def test_deserialize(self):
        example = Instance(int)

        # Validation only happens when this Field is part of a Model. So it
        # still passes all values through.
        for value in (None, 0, 'string', object(), type):
            example.deserialize(value) == value

    def test_validate(self):
        example = Instance(int)

        # All integers should pass the validation.
        example.validate(-1000)
        example.validate(0)
        example.validate(1000)

        # Anything that is not an int should raise a ValidationError.
        for value in (None, 20.0, 'string', object, type):
            with raises(ValidationError):
                example.validate(value)


class TestBool:

    def test___init__(self):
        field = Bool(rename='test', required=False, default=False)
        assert field.rename is 'test'
        assert field.required is False
        assert field.default is False
        assert field.validators == []

    def test_deserialize(self):
        field = Bool()
        assert field.deserialize(False) is False
        assert field.deserialize(True) is True

    def test_validate(self):
        field = Bool()
        field.validate(False)
        field.validate(True)

        with raises(ValidationError):
            field.validate('True')


class TestDict:

    def test_serialize(self):
        # A field that is a key value pair of Strs and Stringifys.
        field = Dict(Str, Stringify)

        # Validation only happens when this Field is part of a Model. So it
        # still passes any Dict like value through.
        for value in ({}, OrderedDict()):
            field.serialize(value) == value

        # Any value that is not an Dict will raise a AttributeError
        # because it doesn't have the `.items()` method.
        for value in (None, 20.0, object, type):
            with raises(AttributeError):
                field.serialize(value)

        # Serialize calls the key and value serialize methods.
        assert field.serialize({'a': False, 'b': ['s'], 'c': {'a': 5}}) == \
            {'a': 'False', 'b': "['s']", 'c': "{'a': 5}"}

    def test_deserialize(self):
        # A field that is a key value pair of Strs and Stringifys.
        field = Dict(Str, Stringify)

        # Validation only happens when this Field is part of a Model. So it
        # still passes any Dict like value through.
        for value in ({}, OrderedDict()):
            field.deserialize(value) == value

        # Any value that is not an Dict will raise a AttributeError
        # because it doesn't have the `.items()` method.
        for value in (None, 20.0, object, type):
            with raises((AttributeError, TypeError)):
                field.deserialize(value)

        # Deserialize calls the subfield deserialize method.
        assert field.deserialize({'a': 'False', 'b': "['s']", 'c': "{'a': 5}"}) == \
            {'a': False, 'b': ['s'], 'c': {'a': 5}}

    def test_validate(self):
        # A field that is a key value pair of Strs and Stringifys.
        field = Dict(Str, Stringify, min_length=3, max_length=5)

        # A list of Stringifyiable serializable types will pass validation.
        field.validate({'a': False, 'b': ['s'], 'c': {'a': 5}})

        # Any value that is not an Dict will raise a ValidationError
        for value in (None, 20.0, object, type):
            with raises(ValidationError):
                field.validate(value)

        # A dictionary of with keys that aren't Strs should fail validation.
        with raises(ValidationError):
            field.validate({5: 'hello'})

        # Less than the required amount
        with raises(ValidationError):
            field.validate({'a': 0, 'b': 1})

        # More than the allowed amount
        with raises(ValidationError):
            field.validate({'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5})


class TestFloat:

    def test___init__(self):
        field = Float(rename='test', required=False, default=False)
        assert field.min is None
        assert field.max is None
        assert field.rename is 'test'
        assert field.required is False
        assert field.default is False
        assert field.validators == []

    def test_deserialize(self):
        field = Float()
        assert field.deserialize(0.5) == 0.5
        assert field.deserialize(-1000.0) == -1000.0

    def test_validate(self):
        field = Float(min=-100.0, max=500.0)
        field.validate(-100.0)
        field.validate(0.0)
        field.validate(500.0)

        for value in (0, -1000.0, -100.1, 500.1, 1000.0):
            with raises(ValidationError):
                field.validate(value)


class TestInt:

    def test___init__(self):
        field = Int(rename='test', required=False, default=False)
        assert field.min is None
        assert field.max is None
        assert field.rename is 'test'
        assert field.required is False
        assert field.default is False
        assert field.validators == []

    def test_deserialize(self):
        field = Int()
        assert field.deserialize(0.5) == 0.5
        assert field.deserialize(-1000.0) == -1000.0

    def test_validate(self):
        field = Int(min=-100, max=500)
        field.validate(-100)
        field.validate(0)
        field.validate(500)

        for value in (0.0, -1000, -101, 501, 1000):
            with raises(ValidationError):
                field.validate(value)


class TestList:

    def test_serialize(self):
        # A field that must be a list of Stringifys.
        example = List(Stringify)

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
        example = List(Stringify)

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
        example = List(Stringify, min_length=2, max_length=3)

        # A list of Stryfiable types will pass validation.
        example.validate([False, ['s'], {'a': 5}])

        # Any value that is not an Iterable will raise a ValidationError
        for value in (None, 20.0, object, type, [0], [0, 1, 2, 4]):
            with raises(ValidationError):
                example.validate(value)


class TestStr:

    def test___init__(self):
        field = Str(rename='test', required=False, default=False)
        assert field.min_length is None
        assert field.max_length is None
        assert field.rename is 'test'
        assert field.required is False
        assert field.default is False
        assert field.validators == []

    def test_deserialize(self):
        field = Str()
        assert field.deserialize('a') == 'a'
        assert field.deserialize(' ') == ' '

    def test_validate(self):
        field = Str(min_length=1, max_length=5)
        field.validate('hello')
        field.validate('a')

        for value in (None, 'hello2', ''):
            with raises(ValidationError):
                field.validate(value)


class TestTuple:

    def test_serialize(self):
        # A field that is a tuple (bool, str, Stringify)
        example = Tuple(Bool, Str, Stringify)

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
        example = Tuple(Bool, Str, Stringify)

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
        example = Tuple(Bool, Str, Stringify)

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


class TestChoice:

    def test___init__(self):
        field = Choice(range(5), required=False, validators=[])
        assert field.choices == range(5)

    def test_validate(self):
        field = Choice(range(5))

        field.validate(0)
        field.validate(4)

        with raises(ValidationError):
            field.validate('test')


class TestDomain:

    def test_validate(self):
        field = Domain()

        field.validate('www.google.com')

        with raises(ValidationError):
            field.validate('hello')


class TestEmail:

    def test_validate(self):
        field = Email()

        field.validate('someone@website.com')

        with raises(ValidationError):
            field.validate('derp')


class TestSlug:

    def test_validate(self):
        field = Slug()

        field.validate('a_b-10')

        with raises(ValidationError):
            field.validate('a!')


class TestUrl:

    def test_validate(self):
        field = Url()

        field.validate('http://www.google.com/search?q=test')

        with raises(ValidationError):
            field.validate('derp')


class TestUuid:

    def test___init__(self):
        field = Uuid(required=False, default=uuid.UUID('2d7026c8-cc58-11e8-bd7a-784f4386978e'))

        assert field.required is False
        assert field.default == uuid.UUID('2d7026c8-cc58-11e8-bd7a-784f4386978e')

    def test_serialize(self):
        field = Uuid()

        assert field.serialize(uuid.UUID('2d7026c8-cc58-11e8-bd7a-784f4386978e')) == \
            '2d7026c8-cc58-11e8-bd7a-784f4386978e'

    def test_deserialize(self):
        field = Uuid()

        assert field.deserialize('2d7026c8-cc58-11e8-bd7a-784f4386978e') == \
            uuid.UUID('2d7026c8-cc58-11e8-bd7a-784f4386978e')

    def test_validate(self):
        field = Uuid()

        field.validate(uuid.UUID('2d7026c8-cc58-11e8-bd7a-784f4386978e'))

        with raises(ValidationError):
            field.validate('2d7026c8-cc58-11e8-bd7a-784f4386978e')


def test_resolve_to_field_instance():
    # An instance of a field should work
    assert resolve_to_field_instance(Field()) == Field()

    # A Field class should work
    assert resolve_to_field_instance(Field) == Field()

    # A Model class should work
    class Example(Model):
        pass

    assert resolve_to_field_instance(Example) == Nested(Example)

    # All the base types should resolve correctly
    assert resolve_to_field_instance(bool) == Bool()
    assert resolve_to_field_instance(dict) == Dict()
    assert resolve_to_field_instance(float) == Float()
    assert resolve_to_field_instance(int) == Int()
    assert resolve_to_field_instance(list) == List()
    assert resolve_to_field_instance(str) == Str()
    assert resolve_to_field_instance(tuple) == Tuple()

    # A Model instance should not work
    with raises(TypeError):
        resolve_to_field_instance(Example())

    with raises(TypeError):
        resolve_to_field_instance(Example())


def test_create():
    # Create a Field with a new serialize and deserialize method.
    Reversed = create(   # noqa: N806
        'Example',
        Str,
        serializers=[lambda s: s[::-1]],
        deserializers=[lambda s: s[::-1]]
    )

    class Example(Model):
        a = Reversed()

    example = Example.from_dict({'a': 'test'})
    assert example.a == 'tset'
    assert example.to_dict() == {'a': 'test'}

    # Create a Field with a new validate method.
    def validate_is_not_derp(value):
        assert value != 'derp'

    class Example(Model):
        a = create('NotDerp', Str, validators=[validate_is_not_derp])()

    assert Example('notderp').a == 'notderp'

    with raises(ValidationError):
        Example('derp')
