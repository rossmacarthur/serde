import datetime
import re
import uuid
from collections import OrderedDict

from pytest import raises

from serde import Model, fields, validators
from serde.exceptions import (
    ContextError,
    DeserializationError,
    InstantiationError,
    NormalizationError,
    SerializationError,
    ValidationError
)
from serde.fields import (
    BaseField,
    Bool,
    Bytes,
    Choice,
    Complex,
    Constant,
    Date,
    DateTime,
    Dict,
    Field,
    Float,
    Instance,
    Int,
    List,
    Nested,
    Optional,
    Regex,
    Str,
    Time,
    Tuple,
    Uuid,
    _resolve_to_field_instance,
    create
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

    try:
        assert _resolve_to_field_instance(basestring) == fields.BaseString()
    except NameError:
        pass

    try:
        assert _resolve_to_field_instance(long) == fields.Long()
    except NameError:
        pass

    try:
        assert _resolve_to_field_instance(unicode) == fields.Unicode()
    except NameError:
        pass


class TestBaseField:

    def test___init___basic(self):
        # Construct a basic Base and check values are set correctly.
        base = BaseField()
        assert base.id >= 0
        assert base.serializers == []
        assert base.deserializers == []

        # A second Base instantiated should have a higher counter.
        base2 = BaseField()
        assert base2.id - base.id == 1

    def test___init___options(self):
        # A Base with extra options set.
        base = BaseField(serializers=[None], deserializers=[1, 2, 3])
        assert base.serializers == [None]
        assert base.deserializers == [1, 2, 3]

    def test___eq__(self):
        # Bases with equal values should be equal.
        assert BaseField() == BaseField()
        assert BaseField(serializers=[None]) == BaseField(serializers=[None])
        assert BaseField(deserializers=[None]) == BaseField(deserializers=[None])

    def test___model__(self):
        # Base.__model__ simply returns the _model_cls value.
        obj = object()
        base = BaseField()
        base._model_cls = obj
        assert base.__model__ is obj

    def test__attrs(self):
        # Returns a filtered dictionary of filtered attributes.
        base = BaseField(serializers=[None], deserializers=[1, 2, 3])
        assert base._attrs() == {'deserializers': [1, 2, 3], 'serializers': [None]}

    def test__bind(self):
        # Make sure _bind can't be called twice.
        obj = object()
        base = BaseField()
        base._bind(obj)
        assert base._model_cls is obj

        with raises(ContextError) as e:
            base._bind(object())

        assert e.value.message == "'BaseField' instance used multiple times"

    def test__serialize_with(self):
        # Check that the Base field doesn't implement this method.
        with raises(NotImplementedError):
            BaseField()._serialize_with(object(), {})

    def test__deserialize_with(self):
        # Check that the Base field doesn't implement this method.
        with raises(NotImplementedError):
            BaseField()._deserialize_with(object(), {})

    def test__serialize(self):
        # Check that custom serializers are applied.
        base = BaseField(serializers=[lambda x: x[::-1]])
        assert base._serialize('testing') == 'gnitset'

    def test__deserialize(self):
        # Check that custom deserializers are applied.
        base = BaseField(deserializers=[lambda x: x[::-1]])
        assert base._deserialize('gnitset') == 'testing'

    def test_serialize(self):
        # Check that serialize simply passes a value through.
        obj = object()
        assert BaseField().serialize(obj) is obj

    def test_deserialize(self):
        # Check that deserialize simply passes a value through.
        obj = object()
        assert BaseField().deserialize(obj) is obj


class TestField:

    def test___init___basic(self):
        # Construct a basic Field and check values are set correctly.
        field = Field()
        assert field.id >= 0
        assert field.rename is None
        assert field.serializers == []
        assert field.deserializers == []
        assert field.normalizers == []
        assert field.validators == []

        # A second Field instantiated should have a higher counter.
        field2 = Field()
        assert field2.id - field.id == 1

    def test___init___options(self):
        # A Field with extra options set.
        field = Field(
            rename='test',
            serializers=[1, 2, 3],
            deserializers=[0.5],
            validators=[None]
        )
        assert field.rename == 'test'
        assert field.serializers == [1, 2, 3]
        assert field.deserializers == [0.5]
        assert field.validators == [None]

    def test__bind(self):
        # Make sure _bind can't be called twice.
        obj = object()
        field = Field()
        field._bind(obj, 'test')
        assert field._model_cls is obj
        assert field._attr_name == 'test'
        assert field._serde_name == 'test'

        with raises(ContextError) as e:
            field._bind(object(), 'test')

        assert e.value.message == "'Field' instance used multiple times"

    def test__bind_with_rename(self):
        # Make sure _bind rename overrides the passed in name.
        obj = object()
        field = Field(rename='hello')
        field._bind(obj, 'test')
        assert field._attr_name == 'test'
        assert field._serde_name == 'hello'

    def test__serialize_with(self):
        # Check a basic Field simply serializes the attribute value.
        model = Model()
        model.test = 'testing...'
        field = Field(rename='hello')
        field._bind(model.__class__, 'test')
        assert field._serialize_with(model, {}) == {'hello': 'testing...'}

    def test__serialize_with_attribute_error(self):
        # Check that the appropriate error is raised when the attr is missing.
        model = Model()
        field = Field(rename='hello')
        field._bind(model.__class__, 'test')

        with raises(SerializationError) as e:
            field._serialize_with(model, {})

        assert e.value.pretty() == """\
SerializationError: expected attribute 'test'
    Due to => field 'test' of type 'Field' on model 'Model'"""

    def test__deserialize_with(self):
        # Check a basic Field simply deserializes the dictionary value.
        model = Model()
        field = Field(rename='hello')
        field._bind(model.__class__, 'test')

        result = field._deserialize_with(model, {'hello': 'testing...'})
        assert result == (model, {'hello': 'testing...'})
        assert model.test == 'testing...'

    def test__deserialize_with_index_error(self):
        # Check that the appropriate error is raised when the key is missing.
        model = Model()
        field = Field(rename='hello')
        field._bind(model.__class__, 'test')

        with raises(DeserializationError) as e:
            field._deserialize_with(model, {})

        assert e.value.pretty() == """\
DeserializationError: expected field 'hello'
    Due to => field 'test' of type 'Field' on model 'Model'"""

    def test__normalize_with(self):
        # Check a basic Field simply serializes the attribute value.
        model = Model()
        model.test = 'testing...'
        field = Field(rename='hello')
        field._bind(model.__class__, 'test')
        field._normalize_with(model)

    def test__normalize_with_attribute_error(self):
        # Check that the appropriate error is raised when the attr is missing.
        model = Model()
        field = Field(rename='hello')
        field._bind(model.__class__, 'test')

        with raises(NormalizationError) as e:
            field._normalize_with(model)

        assert e.value.pretty() == """\
NormalizationError: expected attribute 'test'
    Due to => field 'test' of type 'Field' on model 'Model'"""

    def test__validate_with(self):
        # Check a basic Field simply serializes the attribute value.
        model = Model()
        model.test = 'testing...'
        field = Field(rename='hello')
        field._bind(model.__class__, 'test')
        field._validate_with(model)

    def test__validate_with_attribute_error(self):
        # Check that the appropriate error is raised when the attr is missing.
        model = Model()
        field = Field(rename='hello')
        field._bind(model.__class__, 'test')

        with raises(ValidationError) as e:
            field._validate_with(model)

        assert e.value.pretty() == """\
ValidationError: expected attribute 'test'
    Due to => field 'test' of type 'Field' on model 'Model'"""

    def test_normalize(self):
        # The base Field simply passes things through.
        field = Field()
        value = object()
        assert field.normalize(value) == value

    def test_validate(self):
        # Any value is allowed on the base Field except None.
        field = Field()
        for value in (None, 0, 'string', object(), type):
            field.validate(value)


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

    field = Example(a='test')
    assert field.a == 'tset'

    field = Example.from_dict({'a': 'test'})
    assert field.a == 'test'
    assert field.to_dict() == {'a': 'tset'}


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

    with raises(InstantiationError):
        Example('derp')


class TestOptional:

    def test___init___basic(self):
        # Construct a basic Optional and check values are set correctly.
        field = Optional()
        assert field.inner == Field()
        assert field.default is None
        assert field.validators == []

    def test___init___options(self):
        # Construct an Optional with extra options and make sure values are
        # passed to Field.
        field = Optional(Str, default='test', validators=[None])
        assert field.inner == Str()
        assert field.default == 'test'
        assert field.validators == [None]

    def test__serialize_with(self):
        # Check an Optional serializes using the inner Field.
        model = Model()
        model.test = 'testing...'
        field = Optional(inner=Str, rename='hello')
        field._bind(model.__class__, 'test')
        assert field._serialize_with(model, {}) == {'hello': 'testing...'}
        model.test = None
        assert field._serialize_with(model, {}) == {}

    def test__serialize_with_attribute_error(self):
        # Check that the appropriate error is raised when the attr is missing.
        model = Model()
        field = Optional(rename='hello')
        field._bind(model.__class__, 'test')

        with raises(SerializationError) as e:
            field._serialize_with(model, {})

        assert e.value.pretty() == """\
SerializationError: expected attribute 'test'
    Due to => field 'test' of type 'Optional' on model 'Model'"""

    def test__deserialize_with(self):
        # Check an Optional deserializes using the inner Field.
        model = Model()
        field = Optional(rename='hello', default='testing...')
        field._bind(model.__class__, 'test')
        result = field._deserialize_with(model, {'hello': 'hmmmm'})
        assert result == (model, {'hello': 'hmmmm'})
        assert model.test == 'hmmmm'
        del model.test
        assert field._deserialize_with(model, {}) == (model, {})
        assert not hasattr(model, 'test')

    def test__normalize_with(self):
        # Check an Optional simply normalizes the attribute value.
        model = Model()
        model.test = 'testing...'
        field = Optional(rename='hello')
        field._bind(model.__class__, 'test')
        field._normalize_with(model)

    def test__normalize_with_none(self):
        # Check an Optional simply allows None.
        model = Model()
        field = Optional(rename='hello')
        field._bind(model.__class__, 'test')
        field._normalize_with(model)
        assert model.test is None

    def test__normalize_with_none_default(self):
        # Check an Optional sets a default, if set.
        model = Model()
        field = Optional(rename='hello', default='testing...')
        field._bind(model.__class__, 'test')
        field._normalize_with(model)
        assert model.test == 'testing...'

    def test__normalize_with_none_default_callbable(self):
        # Check an Optional sets a callable default, if set.
        def test():
            return 'testing...'

        model = Model()
        field = Optional(rename='hello', default=test)
        field._bind(model.__class__, 'test')
        field._normalize_with(model)
        assert model.test == 'testing...'

    def test__validate_with(self):
        # Check a basic Field simply serializes the attribute value.
        model = Model()
        model.test = 'testing...'
        field = Optional(rename='hello')
        field._bind(model.__class__, 'test')
        field._validate_with(model)

    def test__validate_with_attribute_error(self):
        # Check that the appropriate error is raised when the attr is missing.
        model = Model()
        field = Optional(rename='hello')
        field._bind(model.__class__, 'test')

        with raises(ValidationError) as e:
            field._validate_with(model)

        assert e.value.pretty() == """\
ValidationError: expected attribute 'test'
    Due to => field 'test' of type 'Optional' on model 'Model'"""

    def test_serialize(self):
        # An Optional should call the wrapped Field's _serialize method.
        field = Optional(Reversed)
        assert field.serialize('test') == 'tset'

    def test_serialize_extra(self):
        # An Optional should call the wrapped Field's _serialize method.
        field = Optional(Reversed(serializers=[lambda x: x.strip()]))
        assert field.serialize('test ') == 'tset'

    def test_deserialize(self):
        # An Optional should call the wrapped Field's _deserialize method.
        field = Optional(Reversed)
        assert field.deserialize('test') == 'tset'

    def test_deserialize_extra(self):
        # An Optional should call the wrapped Field's _deserialize method.
        field = Optional(Field(deserializers=[lambda x: x.strip()]))
        assert field.deserialize('test ') == 'test'

    def test_normalize(self):
        # An Optional should call the wrapped Field's _normalize method.
        field = Optional(Reversed)
        assert field.normalize('test') == 'test'

    def test_validate(self):
        # An Optional should call the wrapped Field's _validate method.
        field = Optional(Reversed)
        with raises(ValidationError):
            assert field.validate(5)

    def test_validate_extra(self):
        # An Optional should call the wrapped Field's _validate method.
        field = Optional(Field(validators=[validators.Equal(10)]))
        with raises(ValidationError):
            assert field.validate(5)


class TestInstance:

    def test___init___basic(self):
        # Construct a basic Instance and check values are set correctly.
        field = Instance(int)
        assert field.type == int
        assert field.validators == []

    def test___init___options(self):
        # Construct an Instance and make sure values are passed to Field.
        field = Instance(int, validators=[None])
        assert field.type == int
        assert field.validators == [None]

    def test_validate(self):
        # Check that it validates that the values are an instance of the
        # specified type.
        field = Instance(int)

        for value in (-1000, 0, 1000):
            assert field.validate(value) is None

        for value in (None, 20.0, 'string', object, type):
            with raises(ValidationError):
                field.validate(value)


class TestNested:

    def test___init___basic(self):
        # Construct a basic Nested and check values are set correctly.
        field = Nested(Model)
        assert field.type == Model
        assert field.validators == []

    def test___init___options(self):
        # Construct a Nested with extra options and make sure values are passed
        # to Field.
        field = Nested(Model, validators=[None])
        assert field.type == Model
        assert field.validators == [None]

    def test_serialize(self):
        # A Nested should serialize as a dictionary representation of the Model.
        class Example(Model):
            a = Field()

        field = Nested(Example)
        assert field.serialize(Example(a=0)) == OrderedDict([('a', 0)])

    def test_deserialize(self):
        # A Nested should deserialize as a dictionary representation of the
        # Model.
        class Example(Model):
            a = Field()

        field = Nested(Example)
        assert field.deserialize({'a': 0}) == Example(a=0)

        with raises(DeserializationError):
            field.deserialize({'b': 0, 'c': 1})


class TestConstant:

    def test___init___basic(self):
        # Construct a basic Constant and check values are set correctly.
        field = Constant(1)
        assert field.value == 1
        assert field.validators == []

    def test___init___options(self):
        # Construct a Constant with extra options and make sure values are
        # passed to Field.
        field = Constant(-1234, validators=[None])
        assert field.value == -1234
        assert field.validators == [None]

    def test_validate(self):
        # Check that values must be equal to the constant value.
        field = Constant(True)
        field.validate(True)

        with raises(ValidationError):
            assert field.validate(False)


class TestDict:

    def test___init___basic(self):
        # Construct a basic Dict and check values are set correctly.
        field = Dict()
        assert field.key == Field()
        assert field.value == Field()
        assert field.validators == []

    def test___init___options(self):
        # Construct a Dict with extra options and make sure values are passed to
        # Field.
        field = Dict(key=Str, value=Int, validators=[None])
        assert field.key == Str()
        assert field.value == Int()
        assert field.validators == [None]

    def test_serialize(self):
        # A Dict should serialize values based on the key and value Fields.
        field = Dict(key=Reversed, value=Reversed)
        assert field.serialize({'ab': 'test', 'cd': 'hello'}) == {'ba': 'tset', 'dc': 'olleh'}

    def test_serialize_extra(self):
        # A Dict should serialize values based on the key and value Fields.
        field = Dict(key=Field(serializers=[lambda x: x[::-1]]))
        assert field.serialize({'ab': 'test', 'cd': 'hello'}) == {'ba': 'test', 'dc': 'hello'}

    def test_deserialize(self):
        # A Dict should deserialize values based on the key and value Fields.
        field = Dict(key=Reversed, value=Reversed)
        assert field.deserialize({'ba': 'tset', 'dc': 'olleh'}) == {'ab': 'test', 'cd': 'hello'}

    def test_deserialize_extra(self):
        # A Dict should serialize values based on the key and value Fields.
        field = Dict(key=Field(deserializers=[lambda x: x[::-1]]))
        assert field.deserialize({'ba': 'test', 'dc': 'hello'}) == {'ab': 'test', 'cd': 'hello'}

    def test_normalize(self):
        # A Dict should normalize values based on the key and value Fields.
        field = Dict(key=Str, value=Str)
        assert field.normalize({'ab': 'test', 'cd': 'hello'}) == {'ab': 'test', 'cd': 'hello'}

    def test_normalize_extra(self):
        # A Dict should normalize values based on the key and value Fields.
        field = Dict(key=Field(normalizers=[lambda x: x[::-1]]))
        assert field.normalize({'ba': 'test', 'dc': 'hello'}) == {'ab': 'test', 'cd': 'hello'}

    def test_validate(self):
        # A Dict should validate values based on the key and value Fields.
        field = Dict(key=Int, value=Str)
        field.validate({0: 'test', 1: 'hello'})

        with raises(ValidationError):
            field.validate({'test': 0})

    def test_validate_extra(self):
        # A Dict should validate values based on the key and value Fields.
        field = Dict(value=Field(validators=[validators.Equal(10)]))
        field.validate({'test': 10, 'hello': 10})

        with raises(ValidationError):
            field.validate({'test': 11})


class TestList:

    def test___init___basic(self):
        # Construct a basic List and check values are set correctly.
        field = List()
        assert field.element == Field()
        assert field.validators == []

    def test___init___options(self):
        # Construct a List with extra options and make sure values are passed to
        # Field.
        field = List(element=Int, validators=[None])
        assert field.element == Int()
        assert field.validators == [None]

    def test_serialize(self):
        # A List should serialize values based on the element Field.
        field = List(element=Reversed)
        assert field.serialize(['test', 'hello']) == ['tset', 'olleh']

    def test_serialize_extra(self):
        # A List should serialize values based on the element Field.
        field = List(element=Field(serializers=[lambda x: x[::-1]]))
        assert field.serialize(['test', 'hello']) == ['tset', 'olleh']

    def test_deserialize(self):
        # A List should deserialize values based on the element Field.
        field = List(element=Reversed)
        assert field.deserialize(['tset', 'olleh']) == ['test', 'hello']

    def test_deserialize_extra(self):
        # A List should deserialize values based on the element Field.
        field = List(element=Field(deserializers=[lambda x: x[::-1]]))
        assert field.deserialize(['tset', 'olleh']) == ['test', 'hello']

    def test_normalize(self):
        # A List should normalize values based on the element Field.
        field = List(element=Field)
        assert field.normalize(['test', 'hello']) == ['test', 'hello']

    def test_normalize_extra(self):
        # A List should normalize values based on the element Field.
        field = List(element=Field(normalizers=[lambda x: x[::-1]]))
        assert field.normalize(['tset', 'olleh']) == ['test', 'hello']

    def test_validate(self):
        # A List should validate values based on the element Field.
        field = List(element=Int)
        field.validate([0, 1, 2, 3, 4])

        with raises(ValidationError):
            field.validate(['1', '2', 'a', 'string'])

    def test_validate_extra(self):
        # A List should validate values based on the element Field.
        field = List(element=Field(validators=[validators.Equal(10)]))
        field.validate([10, 10, 10])

        with raises(ValidationError):
            field.validate([10, 11, 12, 13])


class TestTuple:

    def test___init___basic(self):
        # Construct a basic Tuple and check values are set correctly.
        field = Tuple()
        field.elements == ()
        assert field.validators == []

    def test___init___options(self):
        # Construct a Tuple with extra options and make sure values are passed to
        # Field.
        field = Tuple(Int, Str, validators=[None])
        assert field.elements == (Int(), Str())
        assert field.validators == [None]

    def test_serialize(self):
        # A Tuple should serialize values based on each element Fields.
        field = Tuple(Uuid, Reversed)
        value = (uuid.UUID('2d7026c8-cc58-11e8-bd7a-784f4386978e'), 'test')
        expected = ('2d7026c8-cc58-11e8-bd7a-784f4386978e', 'tset')
        assert field.serialize(value) == expected

    def test_serialize_extra(self):
        # A Tuple should serialize values based on each element Fields.
        field = Tuple(Field, Field(serializers=[lambda x: x[::-1]]))
        assert field.serialize(('test', 'test')) == ('test', 'tset')

    def test_deserialize(self):
        # A Tuple should deserialize values based on each element Fields.
        field = Tuple(Uuid, Reversed)
        value = ('2d7026c8-cc58-11e8-bd7a-784f4386978e', 'tset')
        expected = ('2d7026c8-cc58-11e8-bd7a-784f4386978e', 'test')
        assert field.deserialize(value) == expected

    def test_deserialize_extra(self):
        # A Tuple should deserialize values based on each element Fields.
        field = Tuple(Field, Field(deserializers=[lambda x: x[::-1]]))
        assert field.deserialize(('test', 'test')) == ('test', 'tset')

    def test_normalize(self):
        # A Tuple should normalize values based on each element Fields.
        field = Tuple(Uuid, Field)
        value = ('2d7026c8-cc58-11e8-bd7a-784f4386978e', 'tset')
        expected = (uuid.UUID('2d7026c8-cc58-11e8-bd7a-784f4386978e'), 'tset')
        assert field.normalize(value) == expected

    def test_normalize_extra(self):
        # A Tuple should normalize values based on each element Fields.
        field = Tuple(Field, Field(normalizers=[lambda x: x[::-1]]))
        assert field.normalize(('test', 'test')) == ('test', 'tset')

    def test_validate(self):
        # A Tuple should validate values based on each element Fields.
        field = Tuple(Int, Str, Bool)
        field.validate((5, 'test', True))

        with raises(ValidationError):
            field.validate((5, 'test', 'not a bool'))

    def test_validate_extra(self):
        # A Tuple should validate values based on each element Fields.
        field = Tuple(Field, Field(validators=[validators.Equal(10)]))
        field.validate((20, 10))

        with raises(ValidationError):
            field.validate((20, 11))


class TestRegex:

    def test___init__(self):
        # Construct a basic Regex and check values are set correctly.
        field = Regex(r'[est]{4}', flags=re.DOTALL, validators=[None])
        assert field.pattern == r'[est]{4}'
        assert field.flags == re.DOTALL
        assert field.validators == [None]

    def test_validate(self):
        # A Regex simply validates the given value matches the regex.
        field = Regex(r'[est]{4}')
        field.validate('test')
        field.validate('tset')
        with raises(ValidationError):
            field.validate('btesttest')


class TestChoice:

    def test___init__(self):
        # Construct a basic Choice and check values are set correctly.
        field = Choice(range(5), validators=[None])
        assert field.choices == range(5)
        assert field.validators == [None]

    def test_validate(self):
        # A Choice simply validates the given value is in the choices.
        field = Choice(range(5))
        field.validate(0)
        field.validate(4)
        with raises(ValidationError):
            field.validate(6)


class TestDateTime:

    def test___init__(self):
        # Construct a basic DateTime and check values are set correctly.
        field = DateTime(format='%Y%m%d %H:%M:%S')
        assert field.format == '%Y%m%d %H:%M:%S'

    def test_serialize_iso8601(self):
        # A DateTime should serialize a datetime as a ISO 8601 formatted string.
        field = DateTime()
        value = datetime.datetime(2001, 9, 11, 12, 5, 48)
        assert field.serialize(value) == '2001-09-11T12:05:48'

    def test_serialize_custom(self):
        # A DateTime should serialize a datetime with the given format.
        field = DateTime(format='%Y%m%d %H:%M:%S')
        value = datetime.datetime(2001, 9, 11, 12, 5, 48)
        assert field.serialize(value) == '20010911 12:05:48'

    def test_deserialize_iso8601(self):
        # A DateTime should deserialize a datetime from a ISO 8601 formatted string.
        field = DateTime()
        value = '2001-09-11T12:05:48'
        assert field.deserialize(value) == datetime.datetime(2001, 9, 11, 12, 5, 48)

    def test_deserialize_custom(self):
        # A DateTime should deserialize a datetime with the given format.
        field = DateTime(format='%Y%m%d %H:%M:%S')
        value = '20010911 12:05:48'
        assert field.deserialize(value) == datetime.datetime(2001, 9, 11, 12, 5, 48)


class TestDate:

    def test_serialize_iso8601(self):
        # A Date should serialize a date as a ISO 8601 formatted string.
        field = Date()
        assert field.serialize(datetime.date(2001, 9, 11)) == '2001-09-11'

    def test_serialize_custom(self):
        # A Date should serialize a date with the given format.
        field = Date(format='%Y%m%d')
        assert field.serialize(datetime.date(2001, 9, 11)) == '20010911'

    def test_deserialize_iso8601(self):
        # A Date should deserialize a date from a ISO 8601 formatted string.
        field = Date()
        assert field.deserialize('2001-09-11') == datetime.date(2001, 9, 11)

    def test_deserialize_custom(self):
        # A Date should deserialize a datetime with the given format.
        field = Date(format='%Y%m%d')
        assert field.deserialize('20010911') == datetime.date(2001, 9, 11)


class TestTime:

    def test_serialize_iso8601(self):
        # A Time should serialize a time as a ISO 8601 formatted string.
        field = Time()
        assert field.serialize(datetime.time(12, 5, 48)) == '12:05:48'

    def test_serialize_custom(self):
        # A Time should serialize a time with the given format.
        field = Time(format='%H%M%S')
        assert field.serialize(datetime.time(12, 5, 48)) == '120548'

    def test_deserialize_iso8601(self):
        # A Time should deserialize a time from a ISO 8601 formatted string.
        field = Time()
        assert field.deserialize('12:05:48') == datetime.time(12, 5, 48)

    def test_deserialize_custom(self):
        # A Time should deserialize a time with the given format.
        field = Time(format='%H%M%S')
        assert field.deserialize('120548') == datetime.time(12, 5, 48)


class TestUuid:

    def test___init__(self):
        # Construct a basic Uuid and check values are set correctly.
        field = Uuid()
        assert field.type == uuid.UUID

    def test_serialize(self):
        # A Uuid should serialize a uuid.UUID as a string.
        field = Uuid()
        value = uuid.UUID('2d7026c8-cc58-11e8-bd7a-784f4386978e')
        assert field.serialize(value) == '2d7026c8-cc58-11e8-bd7a-784f4386978e'

    def test_normalize_str(self):
        # A Uuid should normalize a string as a uuid.UUID.
        field = Uuid()
        value = '2d7026c8-cc58-11e8-bd7a-784f4386978e'
        assert field.normalize(value) == uuid.UUID('2d7026c8-cc58-11e8-bd7a-784f4386978e')

    def test_normalize_int(self):
        # A Uuid should normalize a string as a uuid.UUID.
        field = Uuid()
        value = 255874896585658101253640125750883301947
        assert field.normalize(value) == uuid.UUID('c07fb668-b3cb-4719-9b3d-0881d5eeba3b')

    def test_validate(self):
        # A Uuid should validate that the value is an instance of uuid.UUID.
        field = Uuid()
        field.validate(uuid.UUID('2d7026c8-cc58-11e8-bd7a-784f4386978e'))
        with raises(ValidationError):
            field.validate('2d7026c8-cc58-11e8-bd7a-784f4386978e')
