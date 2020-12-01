import collections
import datetime
import decimal
import re
import uuid
from collections import deque

from pytest import raises
from serde import Model, fields, utils, validators
from serde.exceptions import ContextError, ValidationError
from serde.fields import (
    _FIELD_CLASS_MAP,
    Bool,
    Choice,
    Date,
    DateTime,
    Decimal,
    Deque,
    Dict,
    Field,
    Flatten,
    FrozenSet,
    Instance,
    Int,
    IpAddress,
    List,
    Literal,
    Nested,
    Optional,
    OrderedDict,
    Regex,
    Set,
    Str,
    Text,
    Time,
    Tuple,
    Uuid,
    _Base,
    _Container,
    _Mapping,
    _resolve,
    _Sequence,
)


class Reversed(Str):
    def __init__(self, **kwargs):
        serializers = kwargs.setdefault('serializers', [])
        deserializers = kwargs.setdefault('deserializers', [])
        serializers.append(lambda x: x[::-1])
        deserializers.append(lambda x: x[::-1])
        super(Reversed, self).__init__(**kwargs)


def test_overridden_methods():
    # If a Field overrides _serialize/_deserialize/_normalize/_validate then
    # *all* need to be overridden.
    methods = {'_instantiate', '_serialize', '_deserialize', '_normalize', '_validate'}

    for obj in vars(fields).values():
        if not utils.is_subclass(obj, Field) or obj is Field:
            continue
        for sub_name in vars(obj).keys():
            if sub_name in methods:
                assert all(method in vars(obj).keys() for method in methods)


def test__resolve_field():
    # An instance of Field should be passed through.
    field = Field()
    assert _resolve(field) is field


def test__resolve_field_class():
    # A Field class should be instantiated.
    assert _resolve(Field) == Field()


def test__resolve_model_class():
    # A Model class should become a Nested instance, wrapping the Model class.

    class Example(Model):
        pass

    assert _resolve(Example) == Nested(Example)


def test__resolve_model():
    # A Model instance should not be allowed.

    class Example(Model):
        pass

    with raises(TypeError):
        _resolve(Example())


def test__resolve_builtin_types():
    # All the built-in types should resolve to an instance of their
    # corresponding Field.
    for ty, expected in _FIELD_CLASS_MAP.items():
        assert _resolve(ty) == expected()


class TestBase:
    def test___init___basic(self):
        # Construct a basic Base and check values are set correctly.
        base = _Base()
        assert base.id >= 0
        assert base.serializers == []
        assert base.deserializers == []

        # A second Base instantiated should have a higher counter.
        base2 = _Base()
        assert base2.id - base.id == 1

    def test___init___options(self):
        # A Base with extra options set.
        base = _Base(serializers=[None], deserializers=[1, 2, 3])
        assert base.serializers == [None]
        assert base.deserializers == [1, 2, 3]

    def test___eq__(self):
        # Bases with equal values should be equal.
        assert _Base() == _Base()
        assert _Base(serializers=[None]) == _Base(serializers=[None])
        assert _Base(deserializers=[None]) == _Base(deserializers=[None])

    def test___model__(self):
        # Base.__model__ simply returns the _model_cls value.
        obj = object()
        base = _Base()
        base._model_cls = obj
        assert base.__model__ is obj

    def test__attrs(self):
        # Returns a filtered dictionary of filtered attributes.
        base = _Base(serializers=[None], deserializers=[1, 2, 3])
        assert base._attrs() == {'deserializers': [1, 2, 3], 'serializers': [None]}

    def test__bind(self):
        # Make sure _bind can't be called twice.
        obj = object()
        base = _Base()
        base._bind(obj)
        assert base._model_cls is obj

        with raises(ContextError) as e:
            base._bind(object())

        assert e.value.message == "attempted to use '_Base' instance more than once"

    def test__serialize_with(self):
        # Check that the Base field doesn't implement this method.
        with raises(NotImplementedError):
            _Base()._serialize_with(object(), {})

    def test__deserialize_with(self):
        # Check that the Base field doesn't implement this method.
        with raises(NotImplementedError):
            _Base()._deserialize_with(object(), {})

    def test__serialize(self):
        # Check that custom serializers are applied.
        base = _Base(serializers=[lambda x: x[::-1]])
        assert base._serialize('testing') == 'gnitset'

    def test__deserialize(self):
        # Check that custom deserializers are applied.
        base = _Base(deserializers=[lambda x: x[::-1]])
        assert base._deserialize('gnitset') == 'testing'

    def test_serialize(self):
        # Check that serialize simply passes a value through.
        obj = object()
        assert _Base().serialize(obj) is obj

    def test_deserialize(self):
        # Check that deserialize simply passes a value through.
        obj = object()
        assert _Base().deserialize(obj) is obj


class TestField:
    def test___init___basic(self):
        # Construct a basic Field and check values are set correctly.
        field = Field()
        assert field.id >= 0
        assert field.rename is None
        assert field.default is None
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
            default=5,
            serializers=[1, 2, 3],
            deserializers=[0.5],
            validators=[None],
        )
        assert field.rename == 'test'
        assert field.default == 5
        assert field.serializers == [1, 2, 3]
        assert field.deserializers == [0.5]
        assert field.validators == [None]

    def test__default(self):
        # Make sure default is correctly returned.
        def returns_5():
            return 5

        assert Field(default=None)._default() is None
        assert Field(default=5)._default() == 5
        assert Field(default=returns_5)._default() == 5

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

        assert e.value.message == "attempted to use 'Field' instance more than once"

    def test__bind_with_rename(self):
        # Make sure _bind rename overrides the passed in name.
        obj = object()
        field = Field(rename='hello')
        field._bind(obj, 'test')
        assert field._attr_name == 'test'
        assert field._serde_name == 'hello'

    def test__instantiate_with(self):
        # Check a basic Field can instantiate a basic value.
        model = Model()
        field = Field(rename='hello')
        field._bind(model.__class__, 'test')
        kwargs = {'test': 'testing...'}
        assert field._instantiate_with(model, kwargs) is None
        assert model.test == 'testing...'

    def test__instantiate_with_default(self):
        # Check a basic Field can instantiate a default when not given.
        model = Model()
        field = Field(rename='hello', default='testing...')
        field._bind(model.__class__, 'test')
        kwargs = {}
        assert field._instantiate_with(model, kwargs) is None
        assert model.test == 'testing...'

    def test__instantiate_with_none_and_default(self):
        # Check a basic Field can instantiate a default.
        model = Model()
        field = Field(rename='hello', default='testing...')
        field._bind(model.__class__, 'test')
        kwargs = {'test': None}
        assert field._instantiate_with(model, kwargs) is None
        assert model.test == 'testing...'

    def test__instantiate_with_type_error(self):
        # Check that a basic Field raises a TypeError when instantiation fails.
        model = Model()
        field = Field(rename='hello')
        field._bind(model.__class__, 'test')
        for kwargs in [{'test': None}, {}]:
            with raises(TypeError) as e:
                field._instantiate_with(model, kwargs)
            assert str(e.value) == "__init__() missing required argument 'test'"

    def test__serialize_with(self):
        # Check a basic Field simply serializes the attribute value.
        model = Model()
        model.test = 'testing...'
        field = Field(rename='hello')
        field._bind(model.__class__, 'test')
        assert field._serialize_with(model, {}) == {'hello': 'testing...'}

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

        with raises(ValidationError) as e:
            field._deserialize_with(model, {})
        assert e.value.messages() == "missing data, expected field 'hello'"

    def test__normalize_with(self):
        # Check a basic Field simply serializes the attribute value.
        model = Model()
        model.test = 'testing...'
        field = Field(rename='hello')
        field._bind(model.__class__, 'test')
        field._normalize_with(model)

    def test__validate_with(self):
        # Check a basic Field simply serializes the attribute value.
        model = Model()
        model.test = 'testing...'
        field = Field(rename='hello')
        field._bind(model.__class__, 'test')
        field._validate_with(model)

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
        field = Optional(Field(validators=[validators.Between(10, 10)]))
        with raises(ValidationError):
            assert field.validate(5)

    def test_integrate_contained(self):
        # An Optional should be able to be contained by other container fields.

        class Example(Model):
            a = Dict(key=str, value=Optional(int))

        assert Example(a={}).to_dict() == {'a': {}}
        assert Example.from_dict({'a': {}}) == Example(a={})

        assert Example(a={'x': 1234, 'y': None, 'z': 0}).to_dict() == {
            'a': {'x': 1234, 'y': None, 'z': 0}
        }
        assert Example.from_dict({'a': {'x': 1234, 'y': None, 'z': 0}}) == Example(
            a={'x': 1234, 'y': None, 'z': 0}
        )

    def test_integrate_contained_model(self):
        # An Optional should be able to contain nested Model.

        class NestedExample(Model):
            a = fields.Int()

        class Example(Model):
            nested = Optional(NestedExample)

        assert Example().to_dict() == {}
        assert Example.from_dict({}) == Example()

        assert Example(nested=NestedExample(a=5)).to_dict() == {'nested': {'a': 5}}
        assert Example.from_dict({'nested': {'a': 5}}) == Example(
            nested=NestedExample(a=5)
        )

    def test_integrate_contained_default(self):
        # An Optional with a default should be able to be contained by other
        # container fields.

        class Example(Model):
            a = Dict(key=str, value=Optional(int, default=0))

        assert Example(a={}).to_dict() == {'a': {}}
        assert Example.from_dict({'a': {}}) == Example(a={})

        assert Example(a={'x': 1234, 'y': None, 'z': 0}).to_dict() == {
            'a': {'x': 1234, 'y': 0, 'z': 0}
        }
        assert Example.from_dict({'a': {'x': 1234, 'y': None, 'z': 0}}) == Example(
            a={'x': 1234, 'y': None, 'z': 0}
        )

    def test_integrate_contained_serializers(self):
        # An Optional with extra serializers should be able to be contained by
        # other container fields.

        class Example(Model):
            a = List(
                Optional(int, serializers=[lambda x: x * 2]),
                serializers=[lambda x: x[1:]],
            )

        assert Example(a=[1, 2, None, 3, 4]).to_dict() == {'a': [4, None, 6, 8]}
        assert Example.from_dict({'a': [1, 2, None, 3, 4]}) == Example(
            a=[1, 2, None, 3, 4]
        )

    def test_integrate_contained_deserializers(self):
        # An Optional with extra deserializers should be able to be contained by
        # other container fields.

        class Example(Model):
            a = List(
                Optional(int, deserializers=[lambda x: x * 2]),
                deserializers=[lambda x: x[1:]],
            )

        assert Example(a=[1, 2, None, 3, 4]).to_dict() == {'a': [1, 2, None, 3, 4]}
        assert Example.from_dict({'a': [1, 2, None, 3, 4]}) == Example(
            a=[4, None, 6, 8]
        )

    def test_integrate_contained_normalizers(self):
        # An Optional with extra normalizers should be able to be contained by
        # other container fields.

        class Example(Model):
            a = Dict(key=str, value=Optional(int, normalizers=[lambda x: x * 2]))

        assert Example(a={'x': 1234, 'y': None, 'z': 0}).a == {
            'x': 2468,
            'y': None,
            'z': 0,
        }
        assert Example.from_dict({'a': {'x': 1234, 'y': None, 'z': 0}}).a == {
            'x': 2468,
            'y': None,
            'z': 0,
        }

    def test_integrate_contained_validators(self):
        # An optional with extra validators should be able to be contained by
        # other container fields.

        class Example(Model):
            a = List(
                Optional(str, validators=[validators.Length(1)]),
                validators=[validators.LengthBetween(1, 5)],
            )

        with raises(ValidationError) as e:
            Example(a=['a', 'b', None, 'c', 'hello there'])
        assert e.value.messages() == {'a': {4: 'expected length 1'}}


class TestInstance:
    def test___init___basic(self):
        # Construct a basic Instance and check values are set correctly.
        field = Instance(int)
        assert field.ty == int
        assert field.validators == []

    def test___init___options(self):
        # Construct an Instance and make sure values are passed to Field.
        field = Instance(int, validators=[None])
        assert field.ty == int
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
        assert field.ty == Model
        assert field.validators == []

    def test___init___options(self):
        # Construct a Nested with extra options and make sure values are passed
        # to Field.
        field = Nested(Model, validators=[None])
        assert field.ty == Model
        assert field.validators == [None]

    def test_serialize(self):
        # A Nested should serialize as a dictionary representation of the Model.
        class Example(Model):
            a = Field()

        field = Nested(Example)
        assert field.serialize(Example(a=0)) == collections.OrderedDict([('a', 0)])

    def test_deserialize(self):
        # A Nested should deserialize as a dictionary representation of the
        # Model.
        class Example(Model):
            a = Field()

        field = Nested(Example)
        assert field.deserialize({'a': 0}) == Example(a=0)

        with raises(ValidationError):
            field.deserialize({'b': 0, 'c': 1})

        with raises(ValidationError) as e:
            field.deserialize([0])
        assert e.value.message == "invalid type, expected 'mapping'"


class TestFlatten:
    def test_integrate_basic(self):
        # A Flatten should serialize and deserialize into the containing Model.

        class NestedExample(Model):
            a = Field()
            b = Field()

        class Example(Model):
            nested = Flatten(NestedExample)
            c = Field()

        assert Example(nested=NestedExample(a='.', b='..'), c='...').to_dict() == {
            'a': '.',
            'b': '..',
            'c': '...',
        }
        assert Example.from_dict({'a': '.', 'b': '..', 'c': '...'}) == Example(
            nested=NestedExample(a='.', b='..'), c='...'
        )


class TestContainer:
    def test__iter(self):
        with raises(NotImplementedError):
            _Container(dict)._iter(object())

    def test__apply(self):
        with raises(NotImplementedError):
            _Container(dict)._apply('_serialize', object())


class TestMapping:
    def test___init___basic(self):
        # Construct a basic _Mapping and check values are set correctly.
        field = _Mapping(dict)
        assert field.ty == dict
        assert field.key == Field()
        assert field.value == Field()
        assert field.validators == []

    def test___init___options(self):
        # Construct a _Mapping with extra options and make sure values are
        # passed to Field.
        field = _Mapping(dict, key=Str, value=Int, validators=[None])
        assert field.ty == dict
        assert field.key == Str()
        assert field.value == Int()
        assert field.validators == [None]

    def test__iter_error(self):
        # Check that an AttributeError on the bad dictionary is caught.
        field = _Mapping(dict)
        value = object()
        with raises(ValidationError) as e:
            list(field._iter(value))
        assert e.value.value is value
        assert e.value.message == "invalid type, expected 'dict'"


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
        assert field.serialize({'ab': 'test', 'cd': 'hello'}) == {
            'ba': 'tset',
            'dc': 'olleh',
        }

    def test_serialize_extra(self):
        # A Dict should serialize values based on the key and value Fields.
        field = Dict(key=Field(serializers=[lambda x: x[::-1]]))
        assert field.serialize({'ab': 'test', 'cd': 'hello'}) == {
            'ba': 'test',
            'dc': 'hello',
        }

    def test_deserialize(self):
        # A Dict should deserialize values based on the key and value Fields.
        field = Dict(key=Reversed, value=Reversed)
        assert field.deserialize({'ba': 'tset', 'dc': 'olleh'}) == {
            'ab': 'test',
            'cd': 'hello',
        }

    def test_deserialize_extra(self):
        # A Dict should serialize values based on the key and value Fields.
        field = Dict(key=Field(deserializers=[lambda x: x[::-1]]))
        assert field.deserialize({'ba': 'test', 'dc': 'hello'}) == {
            'ab': 'test',
            'cd': 'hello',
        }

    def test_normalize(self):
        # A Dict should normalize values based on the key and value Fields.
        field = Dict(key=Str, value=Str)
        assert field.normalize({'ab': 'test', 'cd': 'hello'}) == {
            'ab': 'test',
            'cd': 'hello',
        }

    def test_normalize_extra(self):
        # A Dict should normalize values based on the key and value Fields.
        field = Dict(key=Field(normalizers=[lambda x: x[::-1]]))
        assert field.normalize({'ba': 'test', 'dc': 'hello'}) == {
            'ab': 'test',
            'cd': 'hello',
        }

    def test_validate(self):
        # A Dict should validate values based on the key and value Fields.
        field = Dict(key=Int, value=Str)
        field.validate({0: 'test', 1: 'hello'})

        with raises(ValidationError):
            field.validate({'test': 0})

    def test_validate_extra(self):
        # A Dict should validate values based on the key and value Fields.
        field = Dict(value=Field(validators=[validators.Between(10, 10)]))
        field.validate({'test': 10, 'hello': 10})

        with raises(ValidationError):
            field.validate({'test': 11})


class TestOrderedDict:
    def test___init___basic(self):
        # Construct a basic OrderedDict and check values are set correctly.
        field = OrderedDict()
        assert field.key == Field()
        assert field.value == Field()
        assert field.validators == []

    def test___init___options(self):
        # Construct a OrderedDict with extra options and make sure values are
        # passed to Field.
        field = OrderedDict(key=Str, value=Int, validators=[None])
        assert field.key == Str()
        assert field.value == Int()
        assert field.validators == [None]


class TestSequence:
    def test___init___basic(self):
        # Construct a basic _Sequence and check values are set correctly.
        field = _Sequence(list)
        assert field.ty == list
        assert field.element == Field()
        assert field.validators == []

    def test___init___options(self):
        # Construct a _Sequence with extra options and make sure values are
        # passed to Field.
        field = _Sequence(list, element=Str, validators=[None])
        assert field.ty == list
        assert field.element == Str()
        assert field.validators == [None]

    def test__iter_error(self):
        # Check that an AttributeError on the bad dictionary is caught.
        field = _Sequence(list)
        value = object()
        with raises(ValidationError) as e:
            list(field._iter(value))
        assert e.value.value is value
        assert e.value.message == "invalid type, expected 'list'"


class TestDeque:
    def test___init__(self):
        # Construct a basic Deque and check values are set correctly.
        field = Deque()
        assert field.element == Field()
        assert field.kwargs == {'maxlen': None}
        assert field.validators == []

    def test___init___options(self):
        # Construct a Deque with extra options and make sure values are passed
        # to Field.
        field = Deque(element=Str, maxlen=5, validators=[None])
        assert field.element == Str()
        assert field.kwargs == {'maxlen': 5}
        assert field.validators == [None]

    def test_serialize(self):
        # A Deque should serialize values based on the element Field.
        field = Deque(element=Reversed, maxlen=1)
        assert field.serialize(deque(['test', 'hello'])) == deque(['olleh'])

    def test_serialize_extra(self):
        # A Deque should serialize values based on the element Field.
        field = Deque(element=Field(serializers=[lambda x: x[::-1]]))
        assert field.serialize(deque(['test', 'hello'], maxlen=1)) == deque(
            ['olleh'], maxlen=1
        )

    def test_deserialize(self):
        # A Deque should deserialize values based on the element Field.
        field = Deque(element=Reversed, maxlen=1)
        assert field.deserialize(deque(['tset', 'olleh'])) == deque(['hello'], maxlen=1)

    def test_deserialize_extra(self):
        # A Deque should deserialize values based on the element Field.
        field = Deque(element=Field(deserializers=[lambda x: x[::-1]]), maxlen=1)
        assert field.deserialize(deque(['tset', 'olleh'])) == deque(['hello'], maxlen=1)

    def test_normalize(self):
        # A Deque should normalize values based on the element Field.
        field = Deque(element=Field, maxlen=1)
        assert field.normalize(deque(['test', 'hello'])) == deque(['hello'], maxlen=1)

    def test_normalize_extra(self):
        # A Deque should normalize values based on the element Field.
        field = Deque(element=Field(normalizers=[lambda x: x[::-1]]), maxlen=1)
        assert field.normalize(deque(['tset', 'olleh'])) == deque(['hello'], maxlen=1)

    def test_validate(self):
        # A Deque should validate values based on the element Field.
        field = Deque(element=Int, maxlen=3)
        field.validate(deque([0, 1, 2, 3, 4], maxlen=3))

        with raises(ValidationError):
            field.validate(deque(['1', '2', 'a', 'string']))
        with raises(ValidationError):
            field.validate(deque([0, 1], maxlen=2))

    def test_validate_extra(self):
        # A Deque should validate values based on the element Field.
        field = Deque(element=Field(validators=[validators.Between(10, 10)]), maxlen=4)
        field.validate(deque([10, 10, 10], maxlen=4))

        with raises(ValidationError):
            field.validate(deque([10, 11, 12, 13], maxlen=4))


class TestFrozenSet:
    def test___init___basic(self):
        # Construct a basic FrozenSet and check values are set correctly.
        field = FrozenSet()
        assert field.element == Field()
        assert field.validators == []

    def test___init___options(self):
        # Construct a FrozenSet with extra options and make sure values are passed to
        # Field.
        field = FrozenSet(element=Int, validators=[None])
        assert field.element == Int()
        assert field.validators == [None]

    def test_serialize(self):
        # A FrozenSet should serialize values based on the element Field.
        field = FrozenSet(element=Reversed)
        assert field.serialize(frozenset({'test', 'hello'})) == frozenset(
            {'tset', 'olleh'}
        )

    def test_serialize_extra(self):
        # A FrozenSet should serialize values based on the element Field.
        field = FrozenSet(element=Field(serializers=[lambda x: x[::-1]]))
        assert field.serialize(frozenset({'test', 'hello'})) == frozenset(
            {'tset', 'olleh'}
        )

    def test_deserialize(self):
        # A FrozenSet should deserialize values based on the element Field.
        field = FrozenSet(element=Reversed)
        assert field.deserialize(frozenset({'tset', 'olleh'})) == frozenset(
            {'test', 'hello'}
        )

    def test_deserialize_extra(self):
        # A FrozenSet should deserialize values based on the element Field.
        field = FrozenSet(element=Field(deserializers=[lambda x: x[::-1]]))
        assert field.deserialize(frozenset({'tset', 'olleh'})) == frozenset(
            {'test', 'hello'}
        )

    def test_normalize(self):
        # A FrozenSet should normalize values based on the element Field.
        field = FrozenSet(element=Field)
        assert field.normalize(frozenset({'test', 'hello'})) == frozenset(
            {'test', 'hello'}
        )

    def test_normalize_extra(self):
        # A FrozenSet should normalize values based on the element Field.
        field = FrozenSet(element=Field(normalizers=[lambda x: x[::-1]]))
        assert field.normalize(frozenset({'tset', 'olleh'})) == frozenset(
            {'test', 'hello'}
        )

    def test_validate(self):
        # A FrozenSet should validate values based on the element Field.
        field = FrozenSet(element=Int)
        field.validate(frozenset({0, 1, 2, 3, 4}))

        with raises(ValidationError):
            field.validate(frozenset({'1', '2', 'a', 'string'}))

    def test_validate_extra(self):
        # A FrozenSet should validate values based on the element Field.
        field = FrozenSet(element=Field(validators=[validators.Between(10, 10)]))
        field.validate(frozenset({10, 10, 10}))

        with raises(ValidationError):
            field.validate(frozenset({10, 11, 12, 13}))


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
        field = List(element=Field(validators=[validators.Between(10, 10)]))
        field.validate([10, 10, 10])

        with raises(ValidationError):
            field.validate([10, 11, 12, 13])


class TestSet:
    def test___init___basic(self):
        # Construct a basic Set and check values are set correctly.
        field = Set()
        assert field.element == Field()
        assert field.validators == []

    def test___init___options(self):
        # Construct a Set with extra options and make sure values are passed to
        # Field.
        field = Set(element=Int, validators=[None])
        assert field.element == Int()
        assert field.validators == [None]

    def test_serialize(self):
        # A Set should serialize values based on the element Field.
        field = Set(element=Reversed)
        assert field.serialize({'test', 'hello'}) == {'tset', 'olleh'}

    def test_serialize_extra(self):
        # A Set should serialize values based on the element Field.
        field = Set(element=Field(serializers=[lambda x: x[::-1]]))
        assert field.serialize({'test', 'hello'}) == {'tset', 'olleh'}

    def test_deserialize(self):
        # A Set should deserialize values based on the element Field.
        field = Set(element=Reversed)
        assert field.deserialize({'tset', 'olleh'}) == {'test', 'hello'}

    def test_deserialize_extra(self):
        # A Set should deserialize values based on the element Field.
        field = Set(element=Field(deserializers=[lambda x: x[::-1]]))
        assert field.deserialize({'tset', 'olleh'}) == {'test', 'hello'}

    def test_normalize(self):
        # A Set should normalize values based on the element Field.
        field = Set(element=Field)
        assert field.normalize({'test', 'hello'}) == {'test', 'hello'}

    def test_normalize_extra(self):
        # A Set should normalize values based on the element Field.
        field = Set(element=Field(normalizers=[lambda x: x[::-1]]))
        assert field.normalize({'tset', 'olleh'}) == {'test', 'hello'}

    def test_validate(self):
        # A Set should validate values based on the element Field.
        field = Set(element=Int)
        field.validate({0, 1, 2, 3, 4})

        with raises(ValidationError):
            field.validate({'1', '2', 'a', 'string'})

    def test_validate_extra(self):
        # A Set should validate values based on the element Field.
        field = Set(element=Field(validators=[validators.Between(10, 10)]))
        field.validate({10, 10, 10})

        with raises(ValidationError):
            field.validate({10, 11, 12, 13})


class TestTuple:
    def test___init___basic(self):
        # Construct a basic Tuple and check values are set correctly.
        field = Tuple()
        field.elements = ()
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
        field = Tuple(Field, Field(validators=[validators.Between(10, 10)]))
        field.validate((20, 10))

        with raises(ValidationError):
            field.validate((20, 11))

    def test_integrate_incorrect_length(self):
        # A Tuple should handle incorrect length inputs.

        class Example(Model):
            a = Tuple(Int, Str, Int)

        with raises(ValidationError) as e:
            Example.from_dict({'a': (1, 'testing...')})
        assert e.value.messages() == {'a': 'invalid length, expected 3 elements'}


class TestLiteral:
    def test___init___basic(self):
        # Construct a basic Literal and check values are set correctly.
        field = Literal(1)
        assert field.value == 1
        assert field.validators == []

    def test___init___options(self):
        # Construct a Literal with extra options and make sure values are
        # passed to Field.
        field = Literal(-1234, validators=[None])
        assert field.value == -1234
        assert field.validators == [None]

    def test_validate(self):
        # Check that values must be equal to the constant value.
        field = Literal(True)
        field.validate(True)

        with raises(ValidationError):
            assert field.validate(False)


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

        value = '20010911 12:05:48'
        with raises(ValidationError) as e:
            field.deserialize(value)
        assert e.value.value == value
        assert e.value.message == 'invalid ISO 8601 datetime'

    def test_deserialize_custom(self):
        # A DateTime should deserialize a datetime with the given format.
        field = DateTime(format='%Y%m%d %H:%M:%S')

        value = '20010911 12:05:48'
        assert field.deserialize(value) == datetime.datetime(2001, 9, 11, 12, 5, 48)

        value = '2001-09-11T12:05:48'
        with raises(ValidationError) as e:
            field.deserialize(value)
        assert e.value.value == value
        assert e.value.message == "invalid datetime, expected format '%Y%m%d %H:%M:%S'"


class TestDecimal:
    def test_serialize(self):
        # A Decimal should serialize a Decimal object as a str equivalent.
        field = Decimal()
        assert field.serialize(decimal.Decimal("100.76753")) == "100.76753"

    def test_serialize_diff_places(self):
        # A Decimal should serialize a Decimal object as a str equivalent.
        field = Decimal(resolution=10)
        assert field.serialize(decimal.Decimal("100.1234567891")) == "100.1234567891"

    def test_deserialize(self):
        # A Decimal should deserialize a decimal value from a str equivalent
        field = Decimal()

        assert field.deserialize("100.76753") == decimal.Decimal("100.76753")

    def test_deserialize_diff_places(self):
        # A Decimal should deserialize a decimal value from a str equivalent
        field = Decimal(resolution=10)

        assert field.deserialize("100.1234567891") == decimal.Decimal("100.1234567891")


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

        with raises(ValidationError) as e:
            field.deserialize('2-00-1-01')
        assert e.value.value == '2-00-1-01'
        assert e.value.message == 'invalid ISO 8601 date'

    def test_deserialize_custom(self):
        # A Date should deserialize a datetime with the given format.
        field = Date(format='%Y%m%d')

        assert field.deserialize('20010911') == datetime.date(2001, 9, 11)

        with raises(ValidationError) as e:
            field.deserialize('2001-09-11')
        assert e.value.value == '2001-09-11'
        assert e.value.message == "invalid date, expected format '%Y%m%d'"


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

        with raises(ValidationError) as e:
            field.deserialize('1-20548')
        assert e.value.value == '1-20548'
        assert e.value.message == 'invalid ISO 8601 time'

    def test_deserialize_custom(self):
        # A Time should deserialize a time with the given format.
        field = Time(format='%H%M%S')

        assert field.deserialize('120548') == datetime.time(12, 5, 48)

        with raises(ValidationError) as e:
            field.deserialize('12:05:48')
        assert e.value.value == '12:05:48'
        assert e.value.message == "invalid time, expected format '%H%M%S'"


class TestText:
    def test___init__(self):
        # Construct a basic Text and check values are set correctly.
        field = Text(encoding='utf-8', errors='ignore', validators=[None])
        assert field.encoding == 'utf-8'
        assert field.errors == 'ignore'
        assert field.validators == [None]

    def test_normalize(self):
        # A Text should normalize bytes to a string, and pass through all other
        # values.
        field = Text(encoding='utf-8', errors='ignore')
        assert field.normalize(None) is None
        assert field.normalize('test') == u'test'
        assert field.normalize(b'test') == u'test'
        assert field.normalize(b'\xc3\xa9') == u'\xe9'

    def test_normalize_detect(self):
        # A Text should normalize arbitrary bytes to a string by detecting the
        # encoding.
        field = Text()
        assert field.normalize(None) is None
        assert field.normalize('test') == u'test'
        assert field.normalize(b'test') == u'test'
        assert field.normalize(b'\xef\xbb\xbf\xc3\xa9') == u'\xe9'  # utf-8
        assert field.normalize(b'\xff\xfet\x00e\x00s\x00t\x00') == u'test'  # utf-16-le

    def test_integrate(self):
        # Check that the behaviour of a Text field makes sense on a Model.

        class Example(Model):
            a = Text(encoding='utf-8')

        assert Example(a=b'test').a == u'test'


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
        field.validate(u'test')
        field.validate(u'tset')
        with raises(ValidationError):
            field.validate(u'btesttest')


class TestUuid:
    def test___init___basic(self):
        # Construct a basic Uuid and check values are set correctly.
        field = Uuid()
        assert field.ty == uuid.UUID
        assert field.output_form == 'str'

    def test___init___options(self):
        # Construct a Uuid with extra options and check values are set correctly.
        field = Uuid(output_form='hex', validators=[None])
        assert field.ty == uuid.UUID
        assert field.output_form == 'hex'

    def test___init___invalid_output_form(self):
        # Check that an invalid output form is denied.
        with raises(ValueError):
            Uuid(output_form='invalid')

    def test_serialize(self):
        # A Uuid should serialize a uuid.UUID as a string.
        field = Uuid()
        value = uuid.UUID('2d7026c8-cc58-11e8-bd7a-784f4386978e')
        assert field.serialize(value) == '2d7026c8-cc58-11e8-bd7a-784f4386978e'

    def test_serialize_output_form(self):
        # A Uuid should serialize a uuid.UUID based on the output form.
        value = uuid.UUID('c07fb668-b3cb-4719-9b3d-0881d5eeba3b')
        cases = [
            ('str', 'c07fb668-b3cb-4719-9b3d-0881d5eeba3b'),
            ('urn', 'urn:uuid:c07fb668-b3cb-4719-9b3d-0881d5eeba3b'),
            ('hex', 'c07fb668b3cb47199b3d0881d5eeba3b'),
            ('int', 255874896585658101253640125750883301947),
            ('bytes', b'\xc0\x7f\xb6h\xb3\xcbG\x19\x9b=\x08\x81\xd5\xee\xba;'),
            ('fields', (3229595240, 46027, 18201, 155, 61, 9353732995643)),
        ]
        for output_form, expected in cases:
            field = Uuid(output_form=output_form)
            assert field.serialize(value) == expected

    def test_normalize_uuid(self):
        # A Uuid should normalize a uuid.UUID as a uuid.UUID
        field = Uuid()
        value = uuid.uuid4()
        assert field.normalize(value) is value

    def test_normalize_str(self):
        # A Uuid should normalize a string as a uuid.UUID.
        field = Uuid()
        value = '2d7026c8-cc58-11e8-bd7a-784f4386978e'
        assert field.normalize(value) == uuid.UUID(
            '2d7026c8-cc58-11e8-bd7a-784f4386978e'
        )

    def test_normalize_bytes(self):
        # A Uuid should normalize a byte string a a uuid.UUID.
        field = Uuid()
        value = b'\x99\x1a\xf7\xc7\xee\x17G\x02\xb6C\xe2\x93<\xe8:\x01'
        assert field.normalize(value) == uuid.UUID(
            '991af7c7-ee17-4702-b643-e2933ce83a01'
        )


    def test_normalize_int(self):
        # A Uuid should normalize an integer as a uuid.UUID.
        field = Uuid()
        value = 255874896585658101253640125750883301947
        assert field.normalize(value) == uuid.UUID(
            'c07fb668-b3cb-4719-9b3d-0881d5eeba3b'
        )

    def test_normalize_fields(self):
        # A Uuid should normalize a tuple/list as a uuid.UUID.
        field = Uuid()
        value = (3375074170, 20614, 19730, 172, 202, 2390245548685)
        assert field.normalize(value) == uuid.UUID(
            'c92b8b7a-5086-4d12-acca-022c85bca28d'
        )
        assert field.normalize(list(value)) == uuid.UUID(
            'c92b8b7a-5086-4d12-acca-022c85bca28d'
        )

    def test_normalize_invalid(self):
        # A Uuid should not raise an error on a normalization failure.
        field = Uuid()
        value = b'\x99'
        assert field.normalize(value) == value

    def test_validate(self):
        # A Uuid should validate that the value is an instance of uuid.UUID.
        field = Uuid()
        field.validate(uuid.UUID('2d7026c8-cc58-11e8-bd7a-784f4386978e'))
        with raises(ValidationError):
            field.validate('2d7026c8-cc58-11e8-bd7a-784f4386978e')


class TestIpAddress:
    def test___init__(self):
        # Construct a basic IpAddress and check values are set correctly.
        field = IpAddress(validators=[None])
        assert field.validators == [None]

    def test_validate(self):
        # An IpAddress simply validates that the text is an IP address.
        field = IpAddress()
        field.validate(u'123.0.0.7')
        field.validate(u'::ffff:192.0.2.12')
        with raises(ValidationError):
            field.validate(u'900.80.70.11')
