import datetime
import uuid
from collections import OrderedDict

from pytest import raises

from serde import Model, validate
from serde.exceptions import DeserializationError, SerdeError, SkipSerialization, ValidationError
from serde.fields import (
    Bool, Bytes, Choice, Complex, Date, DateTime, Dict, Field, Float, Instance, Int,
    List, Nested, Optional, Str, Time, Tuple, Uuid, _resolve_to_field_instance, create
)


Reversed = create(  # noqa: N806
    'Reversed',
    base=Str,
    serializers=[lambda x: x[::-1]],
    deserializers=[lambda x: x[::-1]]
)


def test__resolve_to_field_instance_field():
    # An instance of Field should be passed through.
    field = Field()
    assert _resolve_to_field_instance(field) is field


def test__resolve_to_field_instance_field_class():
    # A Field class should be instantiated.
    assert _resolve_to_field_instance(Field) == Field()


def test__resolve_to_field_instance_model_class():
    # A Model class should become a Nested instance, wrapping the Model class.

    class Example(Model):
        pass

    assert _resolve_to_field_instance(Example) == Nested(Example)


def test__resolve_to_field_instance_model():
    # A Model instance should not be allowed.

    class Example(Model):
        pass

    with raises(TypeError):
        _resolve_to_field_instance(Example())


def test__resolve_to_field_instance_builtin_types():
    # All the built-in types should resolve to an instance of their
    # corresponding Field.
    assert _resolve_to_field_instance(bool) == Bool()
    assert _resolve_to_field_instance(bytes) == Bytes()
    assert _resolve_to_field_instance(complex) == Complex()
    assert _resolve_to_field_instance(dict) == Dict()
    assert _resolve_to_field_instance(float) == Float()
    assert _resolve_to_field_instance(int) == Int()
    assert _resolve_to_field_instance(list) == List()
    assert _resolve_to_field_instance(str) == Str()
    assert _resolve_to_field_instance(tuple) == Tuple()


class TestField:

    def test___init___basic(self):
        # Construct a basic Field and check values are set correctly.
        field = Field()
        assert field.id >= 0
        assert field.rename is None
        assert field.validators == []

        # A second Field instantiated should have a higher counter.
        field2 = Field()
        assert field2.id - field.id == 1

    def test___init___options(self):
        # A Field with extra options set.
        field = Field(rename='test', validators=[None])
        assert field.rename == 'test'
        assert field.validators == [None]

    def test__setattr__(self):
        # The same Field instance should not be able to be used twice.
        field = Field()
        with raises(SerdeError):
            class Example(Model):
                a = field
                b = field

    def test_name_unused(self):
        # The Field name should not exist until added to a Model.
        field = Field()
        with raises(SerdeError):
            field.name

    def test_name_used(self):
        # The Field name is set when it is added to a Model.
        field = Field()

        class Example(Model):
            a = field

        assert field.name == 'a'

    def test_name_overridden(self):
        # The Field name should be able to be overridden.
        field = Field(rename='not_a')

        class Example(Model):
            a = field

        assert field.name == 'not_a'

    def test_serialize(self):
        # The base Field simply passes things through.
        field = Field()
        value = object()
        assert field.serialize(value) == value

    def test_deserialize(self):
        # The base Field simply passes things through.
        field = Field()
        value = object()
        assert field.deserialize(value) == value

    def test_normalize(self):
        # The base Field simply passes things through.
        field = Field()
        value = object()
        assert field.normalize(value) == value

    def test_validate(self):
        # Any value is allowed on the base Field except None.
        field = Field()
        for value in (0, 'string', object(), type):
            field.validate(value)

        # None should not be allowed.
        with raises(ValidationError):
            field.validate(None)


def test_create_base():
    # By default the created Field should subclass Field.
    Example = create('Example')  # noqa: N806
    assert issubclass(Example, Field)
    assert Example.__mro__[1] == Field


def test_create_str():
    # You should be able to specify a different base Field.
    Example = create('Example', base=Str)  # noqa: N806
    assert issubclass(Example, Str)
    assert Example.__mro__[1] == Str


def test_create_args():
    # You should be able to create a new Field, subclassing a Field that
    # requires positional arguments.
    Example = create('Example', base=Instance, args=(str,))  # noqa: N806
    Example()

    # This is what should happen if you don't give it the arguments!
    Example = create('Example', base=Instance)  # noqa: N806
    with raises(TypeError):
        Example()


def test_create_serializer_and_normalizer_and_deserializer():
    # You should be able to create a new Field with extra serializers,
    # normalizers, and deserializers.

    def reverser(value):
        return value[::-1]

    Reversed = create(  # noqa: N806
        'Reversed',
        base=Str,
        serializers=[reverser],
        deserializers=[reverser],
        normalizers=[reverser]
    )

    class Example(Model):
        a = Reversed()

    example = Example(a='test')
    assert example.a == 'tset'

    example = Example.from_dict({'a': 'test'})
    assert example.a == 'test'
    assert example.to_dict() == {'a': 'tset'}


def test_create_validator():
    # You should be able to create a Field with an arbitrary validate method.

    def assert_is_not_derp(value):
        assert value != 'derp'

    NotDerp = create(  # noqa: N806
        'NotDerp',
        Str,
        validators=[assert_is_not_derp]
    )

    class Example(Model):
        a = NotDerp()

    assert Example('notderp').a == 'notderp'

    with raises(ValidationError):
        Example('derp')


class TestInstance:

    def test___init___basic(self):
        # Construct a basic Instance and check values are set correctly.
        example = Instance(int)
        assert example.type == int
        assert example.validators == []

    def test___init___options(self):
        # Construct an Instance and make sure values are passed to Field.
        example = Instance(int, validators=[None])
        assert example.type == int
        assert example.validators == [None]

    def test_validate(self):
        # Check that it validates that the values are an instance of the
        # specified type.
        example = Instance(int)

        for value in (-1000, 0, 1000):
            assert example.validate(value) is None

        for value in (None, 20.0, 'string', object, type):
            with raises(ValidationError):
                example.validate(value)


class TestNested:

    def test___init___basic(self):
        # Construct a basic Nested and check values are set correctly.
        example = Nested(Model)
        assert example.type == Model
        assert example.dict is None
        assert example.validators == []

    def test___init___options(self):
        # Construct a Nested with extra options and make sure values are passed
        # to Field.
        example = Nested(Model, dict=dict, strict=False, validators=[None])
        assert example.type == Model
        assert example.dict is dict
        assert example.strict is False
        assert example.validators == [None]

    def test_serialize(self):
        # A Nested should serialize as a dictionary representation of the Model.
        class Example(Model):
            a = Field()

        example = Nested(Example)
        assert example.serialize(Example(a=0)) == OrderedDict([('a', 0)])

    def test_serialize_dict(self):
        # You should be able to set the dictionary type when serializing.
        class Example(Model):
            a = Field()

        example = Nested(Example, dict=dict)
        result = example.serialize(Example(a=0))
        assert result == {'a': 0}
        assert not isinstance(result, OrderedDict)

    def test_deserialize(self):
        # A Nested should deserialize as a dictionary representation of the
        # Model.
        class Example(Model):
            a = Field()

        example = Nested(Example)
        assert example.deserialize({'a': 0}) == Example(a=0)

        with raises(DeserializationError):
            example.deserialize({'a': 0, 'b': 1})

    def test_deserialize_strict(self):
        # You should be able to unset strict deserializing.
        class Example(Model):
            a = Field()

        example = Nested(Example, strict=False)
        assert example.deserialize({'a': 0, 'b': 1}) == Example(a=0)


class TestOptional:

    def test___init___basic(self):
        # Construct a basic Optional and check values are set correctly.
        example = Optional()
        assert example.inner == Field()
        assert example.default is None
        assert example.validators == []

    def test___init___options(self):
        # Construct an Optional with extra options and make sure values are
        # passed to Field.
        example = Optional(Str, default='test', validators=[None])
        assert example.inner == Str()
        assert example.default == 'test'
        assert example.validators == [None]

    def test_normalize_default(self):
        # When default is set, the Optional should return that value when the
        # input is None.
        example = Optional(default='test')
        assert example.normalize(None) == 'test'

    def test_normalize_callable_default(self):
        # When a callable default is set, the Optional should call that function
        # and return that value.
        example = Optional(default=dict)
        assert example.normalize(None) == {}

    def test_normalize_something(self):
        # An Optional should call the wrapped Field's normalize method.
        class Test(Field):
            def normalize(self, value):
                return value[::-1]

        example = Optional(Test)
        assert example.normalize('test') == 'tset'

    def test_normalize_none(self):
        # An Optional always normalizes None to None.
        class Test(Field):
            def normalize(self, value):
                return value[::-1]

        example = Optional(Test)
        assert example.normalize(None) is None

    def test_serialize_something(self):
        # An Optional should call the wrapped Field's _serialize method.
        example = Optional(Reversed)
        assert example.serialize('test') == 'tset'

    def test_serialize_something_extra(self):
        # An Optional should call the wrapped Field's _serialize method.
        example = Optional(Field(serializers=[lambda x: x.strip()]))
        assert example.serialize('test ') == 'test'

    def test_serialize_none(self):
        # An Optional should raise SkipSerialization if the value is None.
        example = Optional(Reversed)

        with raises(SkipSerialization):
            assert example.serialize(None)

    def test_deserialize_something(self):
        # An Optional should call the wrapped Field's _deserialize method.
        example = Optional(Reversed)
        assert example.deserialize('test') == 'tset'

    def test_deserialize_something_extra(self):
        # An Optional should call the wrapped Field's _deserialize method.
        example = Optional(Field(deserializers=[lambda x: x.strip()]))
        assert example.deserialize('test ') == 'test'

    def test_deserialize_none(self):
        # An Optional deserialize None as None.
        example = Optional(Reversed)
        assert example.deserialize(None) is None

    def test_validate_something(self):
        # An Optional should call the wrapped Field's _validate method.
        example = Optional(Reversed)

        with raises(ValidationError):
            assert example.validate(5)

    def test_validate_something_extra(self):
        # An Optional should call the wrapped Field's _validate method.
        example = Optional(Field(validators=[validate.equal(10)]))

        with raises(ValidationError):
            assert example.validate(5)

    def test_validate_none(self):
        # An Optional should not do any validation for None.
        example = Optional(Reversed)
        assert example.validate(None) is None


class TestDict:

    def test___init___basic(self):
        # Construct a basic Dict and check values are set correctly.
        example = Dict()
        assert example.key == Field()
        assert example.value == Field()
        assert example.validators == []

    def test___init___options(self):
        # Construct a Dict with extra options and make sure values are passed to
        # Field.
        example = Dict(key=Str, value=Int, validators=[None])
        assert example.key == Str()
        assert example.value == Int()
        assert example.validators == [None]

    def test_serialize(self):
        # A Dict should serialize values based on the key and value Fields.
        example = Dict(key=Reversed, value=Reversed)
        assert example.serialize({'ab': 'test', 'cd': 'hello'}) == {'ba': 'tset', 'dc': 'olleh'}

    def test_serialize_extra(self):
        # A Dict should serialize values based on the key and value Fields.
        example = Dict(key=Field(serializers=[lambda x: x[::-1]]))
        assert example.serialize({'ab': 'test', 'cd': 'hello'}) == {'ba': 'test', 'dc': 'hello'}

    def test_deserialize(self):
        # A Dict should deserialize values based on the key and value Fields.
        example = Dict(key=Reversed, value=Reversed)
        assert example.deserialize({'ba': 'tset', 'dc': 'olleh'}) == {'ab': 'test', 'cd': 'hello'}

    def test_deserialize_extra(self):
        # A Dict should serialize values based on the key and value Fields.
        example = Dict(key=Field(deserializers=[lambda x: x[::-1]]))
        assert example.deserialize({'ba': 'test', 'dc': 'hello'}) == {'ab': 'test', 'cd': 'hello'}

    def test_validate(self):
        # A Dict should validate values based on the key and value Fields.
        example = Dict(key=Int, value=Str)
        example.validate({0: 'test', 1: 'hello'})

        with raises(ValidationError):
            example.validate({'test': 0})

    def test_validate_extra(self):
        # A Dict should validate values based on the key and value Fields.
        example = Dict(value=Field(validators=[validate.equal(10)]))
        example.validate({'test': 10, 'hello': 10})

        with raises(ValidationError):
            example.validate({'test': 11})


class TestList:

    def test___init___basic(self):
        # Construct a basic List and check values are set correctly.
        example = List()
        assert example.element == Field()
        assert example.validators == []

    def test___init___options(self):
        # Construct a List with extra options and make sure values are passed to
        # Field.
        example = List(element=Int, validators=[None])
        assert example.element == Int()
        assert example.validators == [None]

    def test_serialize(self):
        # A List should serialize values based on the element Field.
        example = List(element=Reversed)
        assert example.serialize(['test', 'hello']) == ['tset', 'olleh']

    def test_serialize_extra(self):
        # A List should serialize values based on the element Field.
        example = List(element=Field(serializers=[lambda x: x[::-1]]))
        assert example.serialize(['test', 'hello']) == ['tset', 'olleh']

    def test_deserialize(self):
        # A List should deserialize values based on the element Field.
        example = List(element=Reversed)
        assert example.deserialize(['tset', 'olleh']) == ['test', 'hello']

    def test_deserialize_extra(self):
        # A List should deserialize values based on the element Field.
        example = List(element=Field(deserializers=[lambda x: x[::-1]]))
        assert example.deserialize(['tset', 'olleh']) == ['test', 'hello']

    def test_validate(self):
        # A List should validate values based on the element Field.
        example = List(element=Int)
        example.validate([0, 1, 2, 3, 4])

        with raises(ValidationError):
            example.validate(['1', '2', 'a', 'string'])

    def test_validate_extra(self):
        # A List should validate values based on the element Field.
        example = List(element=Field(validators=[validate.equal(10)]))
        example.validate([10, 10, 10])

        with raises(ValidationError):
            example.validate([10, 11, 12, 13])


class TestTuple:

    def test___init___basic(self):
        # Construct a basic Tuple and check values are set correctly.
        example = Tuple()
        example.elements == ()
        assert example.validators == []

    def test___init___options(self):
        # Construct a Tuple with extra options and make sure values are passed to
        # Field.
        example = Tuple(Int, Str, validators=[None])
        assert example.elements == (Int(), Str())
        assert example.validators == [None]

    def test_serialize(self):
        # A Tuple should serialize values based on each element Fields.
        example = Tuple(Uuid, Reversed)
        value = (uuid.UUID('2d7026c8-cc58-11e8-bd7a-784f4386978e'), 'test')
        expected = ('2d7026c8-cc58-11e8-bd7a-784f4386978e', 'tset')
        assert example.serialize(value) == expected

    def test_serialize_extra(self):
        # A Tuple should serialize values based on each element Fields.
        example = Tuple(Field, Field(serializers=[lambda x: x[::-1]]))
        assert example.serialize(('test', 'test')) == ('test', 'tset')

    def test_deserialize(self):
        # A Tuple should deserialize values based on each element Fields.
        example = Tuple(Uuid, Reversed)
        value = ('2d7026c8-cc58-11e8-bd7a-784f4386978e', 'tset')
        expected = (uuid.UUID('2d7026c8-cc58-11e8-bd7a-784f4386978e'), 'test')
        assert example.deserialize(value) == expected

    def test_deserialize_extra(self):
        # A Tuple should deserialize values based on each element Fields.
        example = Tuple(Field, Field(deserializers=[lambda x: x[::-1]]))
        assert example.deserialize(('test', 'test')) == ('test', 'tset')

    def test_validate(self):
        # A Tuple should validate values based on each element Fields.
        example = Tuple(Int, Str, Bool)
        example.validate((5, 'test', True))

        with raises(ValidationError):
            example.validate((5, 'test', 'not a bool'))

    def test_validate_extra(self):
        # A Tuple should validate values based on each element Fields.
        example = Tuple(Field, Field(validators=[validate.equal(10)]))
        example.validate((20, 10))

        with raises(ValidationError):
            example.validate((20, 11))


class TestChoice:

    def test___init__(self):
        # Construct a basic Choice and check values are set correctly.
        example = Choice(range(5), validators=[None])
        assert example.choices == range(5)
        assert example.validators == [None]

    def test_validate(self):
        # A Choice simply validates the given value is in the choices.
        example = Choice(range(5))
        example.validate(0)
        example.validate(4)
        with raises(ValidationError):
            example.validate(6)


class TestDateTime:

    def test___init__(self):
        # Construct a basic DateTime and check values are set correctly.
        example = DateTime(format='%Y%m%d %H:%M:%S')
        assert example.format == '%Y%m%d %H:%M:%S'

    def test_serialize_iso8601(self):
        # A DateTime should serialize a datetime as a ISO 8601 formatted string.
        example = DateTime()
        value = datetime.datetime(2001, 9, 11, 12, 5, 48)
        assert example.serialize(value) == '2001-09-11T12:05:48'

    def test_serialize_custom(self):
        # A DateTime should serialize a datetime with the given format.
        example = DateTime(format='%Y%m%d %H:%M:%S')
        value = datetime.datetime(2001, 9, 11, 12, 5, 48)
        assert example.serialize(value) == '20010911 12:05:48'

    def test_deserialize_iso8601(self):
        # A DateTime should deserialize a datetime from a ISO 8601 formatted string.
        example = DateTime()
        value = '2001-09-11T12:05:48'
        assert example.deserialize(value) == datetime.datetime(2001, 9, 11, 12, 5, 48)

    def test_deserialize_custom(self):
        # A DateTime should deserialize a datetime with the given format.
        example = DateTime(format='%Y%m%d %H:%M:%S')
        value = '20010911 12:05:48'
        assert example.deserialize(value) == datetime.datetime(2001, 9, 11, 12, 5, 48)


class TestDate:

    def test_serialize_iso8601(self):
        # A Date should serialize a date as a ISO 8601 formatted string.
        example = Date()
        assert example.serialize(datetime.date(2001, 9, 11)) == '2001-09-11'

    def test_serialize_custom(self):
        # A Date should serialize a date with the given format.
        example = Date(format='%Y%m%d')
        assert example.serialize(datetime.date(2001, 9, 11)) == '20010911'

    def test_deserialize_iso8601(self):
        # A Date should deserialize a date from a ISO 8601 formatted string.
        example = Date()
        assert example.deserialize('2001-09-11') == datetime.date(2001, 9, 11)

    def test_deserialize_custom(self):
        # A Date should deserialize a datetime with the given format.
        example = Date(format='%Y%m%d')
        assert example.deserialize('20010911') == datetime.date(2001, 9, 11)


class TestTime:

    def test_serialize_iso8601(self):
        # A Time should serialize a time as a ISO 8601 formatted string.
        example = Time()
        assert example.serialize(datetime.time(12, 5, 48)) == '12:05:48'

    def test_serialize_custom(self):
        # A Time should serialize a time with the given format.
        example = Time(format='%H%M%S')
        assert example.serialize(datetime.time(12, 5, 48)) == '120548'

    def test_deserialize_iso8601(self):
        # A Time should deserialize a time from a ISO 8601 formatted string.
        example = Time()
        assert example.deserialize('12:05:48') == datetime.time(12, 5, 48)

    def test_deserialize_custom(self):
        # A Time should deserialize a time with the given format.
        example = Time(format='%H%M%S')
        assert example.deserialize('120548') == datetime.time(12, 5, 48)


class TestUuid:

    def test___init__(self):
        # Construct a basic Uuid and check values are set correctly.
        example = Uuid()
        assert example.type == uuid.UUID

    def test_serialize(self):
        # A Uuid should serialize a uuid.UUID as a string.
        example = Uuid()
        value = uuid.UUID('2d7026c8-cc58-11e8-bd7a-784f4386978e')
        assert example.serialize(value) == '2d7026c8-cc58-11e8-bd7a-784f4386978e'

    def test_deserialize(self):
        # A Uuid should deserialize a string as a uuid.UUID.
        example = Uuid()
        value = '2d7026c8-cc58-11e8-bd7a-784f4386978e'
        assert example.deserialize(value) == uuid.UUID('2d7026c8-cc58-11e8-bd7a-784f4386978e')

    def test_validate(self):
        # A Uuid should validate that the value is an instance of uuid.UUID.
        example = Uuid()
        example.validate(uuid.UUID('2d7026c8-cc58-11e8-bd7a-784f4386978e'))
        with raises(ValidationError):
            example.validate('2d7026c8-cc58-11e8-bd7a-784f4386978e')
