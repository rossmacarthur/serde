import datetime
from collections import OrderedDict

import mock
from pytest import raises

from serde import Model, field, validate
from serde.error import DeserializationError, SerdeError, SerializationError, ValidationError


class TestModel:

    def test___new___empty(self):
        # Check that a Model with no Fields can be created. There should still
        # be a _fields attribute.

        class Example(Model):
            pass

        assert Example._fields == {}

    def test___new___basic(self):
        # Check that the ModelType basic usage works, Fields should be pulled
        # off the class and added as a `_fields` attribute.

        class Example(Model):
            a = field.Int()
            b = field.Bool()

        # The field attributes should not be present on the final class.
        assert not hasattr(Example, 'a')
        assert not hasattr(Example, 'b')

        # But they should be in the _fields attribute
        assert isinstance(Example._fields.a, field.Int)
        assert isinstance(Example._fields.b, field.Bool)

    def test___new___subclassed_basic(self):
        # When extending a Model the parent field attributes should also be
        # present.

        class Example(Model):
            a = field.Int()
            b = field.Bool()

        class Example2(Model):
            pass

        assert isinstance(Example._fields.a, field.Int)
        assert isinstance(Example._fields.b, field.Bool)

    def test___new___subclassed_overriding_fields(self):
        # Subclassed Models with Fields of the same name should override the
        # parent Fields.

        class Example(Model):
            a = field.Int()
            b = field.Int()

        class Example2(Example):
            b = field.Float()
            c = field.Float()

        assert isinstance(Example2._fields.a, field.Int)
        assert isinstance(Example2._fields.b, field.Float)
        assert isinstance(Example2._fields.c, field.Float)

    def test___new___subclassed_overriding_attributes(self):
        # Subclassed Models with functions, attributes, and properties should
        # override the Fields.

        class Example(Model):
            a = field.Int()
            b = field.Bool()
            c = field.Str()

        class Example2(Model):

            @property
            def a(self):
                return 'is a'

            def b(self):
                return 'is b'

            c = 'is c'

        assert not hasattr(Example2._fields, 'a')
        assert not hasattr(Example2._fields, 'b')
        assert not hasattr(Example2._fields, 'c')

        example = Example2()
        assert example.a == 'is a'
        assert example.b() == 'is b'
        assert example.c == 'is c'

    def test___new__subclassed_overriding_model_methods(self):
        # Subclassed Models can easily call override Model methods and call
        # super() if they so wish.

        class Example(Model):
            a = field.Int()

        class Example2(Example):

            def __init__(self):
                super(Example2, self).__init__(a=5)

        assert isinstance(Example2._fields.a, field.Int)
        assert Example2().a == 5

    def test___init___empty(self):
        # An empty Model with no Fields should work just fine.

        class Example(Model):
            pass

        assert Example().__dict__ == {}

        with raises(SerdeError):
            Example(a=None)

        with raises(SerdeError):
            Example(a=None)

    def test___init___required(self):
        # Check that a required Field behaves as it should.

        class Example(Model):
            a = field.Int()

        assert Example(a=5).a == 5

        with raises(SerdeError):
            Example()

    def test___init___optional(self):
        # Check that a non required Field behaves as it should.

        class Example(Model):
            a = field.Int(required=False)

        assert Example().a is None
        assert Example(a=5).a == 5

    def test___init___default(self):
        # Check that the default Field value is applied correctly.

        class Example(Model):
            a = field.Int(default=0)

        assert Example().a == 0
        assert Example(a=5).a == 5

    def test___init___args_vs_kwargs(self):
        # Check that you can pass in Field values as arguments.

        class Example(Model):
            a = field.Int()
            b = field.Str()

        example = Example(a=5, b='test')
        assert example.a == 5
        assert example.b == 'test'

        example = Example(5, 'test')
        assert example.a == 5
        assert example.b == 'test'

    def test___init___args_multiple(self):
        # Check that you are not allowed to pass the same argument twice and
        # that you can't pass more arguments than fields.

        class Example(Model):
            a = field.Int()

        with raises(SerdeError):
            Example(5, a=5)

        with raises(SerdeError):
            Example(5, 6)

    def test___init___validation(self):
        # The __init__() method should validate the values.

        class Example(Model):
            a = field.Int()
            b = field.Str(required=False)

        Example(a=5, b=None)

        with raises(ValidationError):
            Example(a=None)

        with raises(ValidationError):
            Example(a='test')

        with raises(ValidationError):
            Example(b=5)

    def test___init___validators(self):
        # Check that extra validators work.

        class Example(Model):
            a = field.Int(validators=[validate.between(100, 200)])

        assert Example(a=101).a == 101

        with raises(ValidationError):
            Example(a=5)

    def test___init___nested(self):
        # Check that nested Model construction works.

        class SubExample(Model):
            a = field.Int()

        class Example(Model):
            sub = field.Nested(SubExample)

        example = Example(sub=SubExample(a=5))
        assert example.sub == SubExample(a=5)
        assert example.sub.a == 5

    def test___eq__(self):
        # Check that the Model equals method works.

        class Example(Model):
            a = field.Int()
            b = field.Bool(required=False)

        assert Example(a=5) != Example(a=6)
        assert Example(a=5) != Example(a=6, b=True)
        assert Example(a=5) == Example(a=5)

    def test___hash___basic(self):
        # Check that a basic Model hash works.

        class Example(Model):
            a = field.Int()

        assert hash(Example(5)) == hash(Example(a=5))
        assert hash(Example(5)) != hash(Example(a=4))

    def test___hash___nested(self):
        # Check that a nested Model hash works.

        class SubExample(Model):
            a = field.Int()

        class Example(Model):
            sub = field.Nested(SubExample)

        assert hash(Example(SubExample(5))) == hash(Example(sub=SubExample(a=5)))
        assert hash(Example(SubExample(5))) != hash(Example(sub=SubExample(a=4)))

    def test___repr___basic(self):
        # Check that a basic Model __repr__ works.

        class Example(Model):
            a = field.Int()
            b = field.Str()

        assert repr(Example(a=5, b='test')) == "Example(a=5, b='test')"

    def test___repr___nested(self):
        # Check that a nested Model __repr__ works.

        class SubExample(Model):
            a = field.Int()

        class Example(Model):
            sub = field.Nested(SubExample)

        assert repr(Example(sub=SubExample(a=5))) == 'Example(sub=SubExample(a=5))'

    def test_validate_all(self):
        # validate_all() should revalidate the Model so that if we have changed
        # values they are validated.

        class Example(Model):
            a = field.Int(validators=[validate.min(100)])

        example = Example(a=101)
        example.a = 5
        with raises(ValidationError):
            example.validate_all()

    def test_validate(self):
        # You should be able to specify custom Model validation by overriding
        # the validate() method.

        class Example(Model):
            a = field.Int()

            def validate(self):
                assert self.a != 0

        with raises(ValidationError):
            Example(a=0)

        example = Example(a=5)
        example.a = 0
        with raises(ValidationError):
            example.validate_all()

    def test_validation_error_context(self):
        # Check that error context is added to ValidationErrors.

        class Example(Model):
            a = field.Int()

        try:
            Example(a='not an integer')
        except ValidationError as e:
            assert e.model is Example
            assert e.field is Example._fields.a
            assert e.value == 'not an integer'

    def test_from_dict_empty(self):
        # Check that an empty Model deserializes from empty dictionary.

        class Example(Model):
            pass

        assert Example.from_dict({}) == Example()

    def test_from_dict_required(self):
        # Check that required Fields have to be present when deserializing.

        class Example(Model):
            a = field.Int()

        assert Example.from_dict({'a': 5}) == Example(a=5)

        with raises(DeserializationError):
            Example.from_dict({})

    def test_from_dict_optional(self):
        # Check that optional Fields do not have to be present when
        # deserializing.

        class Example(Model):
            a = field.Int(required=False)

        assert Example.from_dict({'a': 5}) == Example(a=5)
        assert Example.from_dict({}) == Example()

    def test_from_dict_rename(self):
        # Check that renaming a Field deserializes that value.

        class Example(Model):
            a = field.Int(rename='b')

        assert Example.from_dict({'b': 5}) == Example(a=5)

        with raises(DeserializationError):
            Example.from_dict({'a': 5})

    def test_from_dict_strict(self):
        # Check that if strict is set then unknown keys are not allowed and
        # visa versa.

        class Example(Model):
            a = field.Int()

        assert Example.from_dict({'a': 5, 'c': 'unknown'}, strict=False) == Example(a=5)

        with raises(DeserializationError):
            Example.from_dict({'a': 5, 'b': 'test', 'c': 'unknown'})

    def test_from_dict_modified___init__(self):
        # Check that overriding the __init__ method does not break from_dict().

        class Example(Model):
            a = field.Int()

            def __init__(self):
                super(Example, self).__init__(a=5)

        assert Example.from_dict({'a': 5}) == Example()

    def test_from_dict_nested(self):
        # Check that nested Models are parsed correctly.

        class SubExample(Model):
            a = field.Int()

        class Example(Model):
            sub = field.Nested(SubExample)

        assert Example.from_dict({'sub': {'a': 5}}) == Example(sub=SubExample(a=5))

        with raises(DeserializationError):
            Example.from_dict({'sub': 'not the nested'})

    def test_from_dict_errors(self):
        # Check that all exceptions are mapped to DeserializationErrors.

        def always_raise(e):
            def actual_function(value):
                raise e()
            return actual_function

        class Example(Model):
            a = field.Int()

        Example._fields.a.deserialize = always_raise(AssertionError)
        with raises(DeserializationError):
            Example.from_dict({'a': 5})

        Example._fields.a.deserialize = always_raise(DeserializationError)
        with raises(DeserializationError):
            Example.from_dict({'a': 5})

        Example._fields.a.deserialize = always_raise(Exception)
        with raises(DeserializationError):
            Example.from_dict({'a': 5})

    def test_deserialization_error_context(self):
        # Check that error context is added to DeserializationErrors.

        class Example(Model):
            a = field.DateTime()

        try:
            Example.from_dict({'a': 'not a datetime'})
        except DeserializationError as e:
            assert e.model is Example
            assert e.field is Example._fields.a
            assert e.value == 'not a datetime'

    def test_from_dict_deserializers(self):
        # Check that custom deserializers are applied.

        class Example(Model):
            a = field.Str(deserializers=[lambda x: x[::-1]])

        assert Example.from_dict({'a': 'test'}) == Example(a='tset')

    def test_from_json_basic(self):
        # Check that you can deserialize from JSON.

        class Example(Model):
            a = field.Int()

        assert Example.from_json('{"a": 5}') == Example(a=5)

    def test_from_json_strict(self):
        # Check that the from_json() method passes through the strict option.

        class Example(Model):
            a = field.Int()

        assert Example.from_json('{"a": 5, "b": "unknown"}', strict=False) == Example(a=5)

        with raises(DeserializationError):
            Example.from_json('{"a": 5, "b": "unknown"}')

    def test_from_json_kwargs(self):
        # Check that extra JSON kwargs can be passed.

        class Example(Model):
            a = field.Int()

        assert Example.from_json('{"a": 5}', object_hook=OrderedDict) == Example(a=5)

    def test_from_toml(self):
        # Check that you can deserialize from TOML, if its installed.

        class Example(Model):
            a = field.Int()

        assert Example.from_toml('a = 5') == Example(a=5)

        with mock.patch('serde.model.toml', None):
            with raises(SerdeError):
                Example.from_toml('a = 50')

    def test_from_yaml(self):
        # Check that you can deserialize from YAML, if its installed.

        class Example(Model):
            a = field.Int()

        assert Example.from_yaml('a: 5') == Example(a=5)

        with mock.patch('serde.model.yaml', None):
            with raises(SerdeError):
                Example.from_yaml('a: 5')

    def test_to_dict_empty(self):
        # Check that an empty Model serializes to an empty dictionary.

        class Example(Model):
            pass

        assert Example().to_dict() == {}

    def test_to_dict_required(self):
        # Check that required Fields are present when serializing.

        class Example(Model):
            a = field.Int()

        assert Example(a=5).to_dict() == {'a': 5}

    def test_to_dict_optional(self):
        # Check that optional Fields are not present when serializing.

        class Example(Model):
            a = field.Int(required=False)

        assert Example().to_dict() == {}

    def test_to_dict_rename(self):
        # Check that renaming a Field serializes that value.

        class Example(Model):
            a = field.Int(rename='b')

        assert Example(a=5).to_dict() == {'b': 5}

    def test_to_dict_type(self):
        # Check that the dictionary type can be modified.

        class Example(Model):
            a = field.Int()

        class CustomDict(OrderedDict):
            def __eq__(self, other):
                return isinstance(other, CustomDict) and super(CustomDict, self).__eq__(other)

        assert Example(a=5).to_dict(dict=CustomDict) == CustomDict([('a', 5)])

    def test_to_dict_nested(self):
        # Check that nested Models are serialized correctly.

        class SubExample(Model):
            a = field.Int()

        class Example(Model):
            sub = field.Nested(SubExample)

        assert Example(sub=SubExample(a=5)).to_dict() == {'sub': {'a': 5}}

    def test_to_dict_errors(self):
        # Check that all exceptions are mapped to SerializationErrors.

        def always_raise(e):
            def actual_function(value):
                raise e()
            return actual_function

        class Example(Model):
            a = field.Int()

        Example._fields.a.serialize = always_raise(AssertionError)
        with raises(SerializationError):
            Example(a=5).to_dict()

        Example._fields.a.serialize = always_raise(SerializationError)
        with raises(SerializationError):
            Example(a=5).to_dict()

        Example._fields.a.serialize = always_raise(Exception)
        with raises(SerializationError):
            Example(a=5).to_dict()

    def test_serialization_error_context(self):
        # Check that error context is added to SerializationErrors.

        class Example(Model):
            a = field.DateTime()

        try:
            example = Example(a=datetime.datetime.utcnow())
            example.a = 'not a datetime'
        except SerializationError as e:
            assert e.model is Example
            assert e.field is Example._fields.a
            assert e.value == 'not a datetime'

    def test_to_dict_serializers(self):
        # Check that custom serializers are applied.

        class Example(Model):
            a = field.Str(serializers=[lambda x: x[::-1]])

        assert Example(a='tset').to_dict() == {'a': 'test'}

    def test_to_json_basic(self):
        # Check that you can serialize to JSON.

        class Example(Model):
            a = field.Int()

        assert Example(a=50).to_json() == '{"a": 50}'

    def test_to_json_kwargs(self):
        # Check that extra JSON kwargs can be passed.

        class Example(Model):
            b = field.Str()
            a = field.Int()

        assert Example(a=5, b='test').to_json(sort_keys=True) == '{"a": 5, "b": "test"}'

    def test_to_toml(self):
        # Check that you can serialize to TOML, if its installed.

        class Example(Model):
            a = field.Int()

        assert Example(a=5).to_toml() == 'a = 5\n'

        with mock.patch('serde.model.toml', None):
            with raises(SerdeError):
                Example(a=5).to_toml()

    def test_to_yaml(self):
        # Check that you can serialize to YAML, if its installed.

        class Example(Model):
            a = field.Int()

        assert Example(a=5).to_yaml(dict=dict, default_flow_style=False) == 'a: 5\n'

        with mock.patch('serde.model.yaml', None):
            with raises(SerdeError):
                Example(a=5).to_yaml()
