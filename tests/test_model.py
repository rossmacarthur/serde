import datetime
from collections import OrderedDict

from pytest import raises

from serde import Model, fields, tags, validate
from serde.exceptions import (
    DeserializationError,
    InstantiationError,
    NormalizationError,
    SerdeError,
    SerializationError,
    ValidationError
)
from tests import py3


class TestModel:

    def test___new___empty(self):
        # Check that a Model with no Fields can be created. There should still
        # be a __fields__ attribute.

        class Example(Model):
            pass

        assert Example.__abstract__ is False
        assert Example.__parent__ is Model
        assert Example.__fields__ == {}
        assert Example.__tag__ is None
        assert Example.__tags__ == []

    def test___new___basic(self):
        # Check that the ModelType basic usage works, Fields should be pulled
        # off the class and added as a `__fields__` attribute.

        class Example(Model):
            a = fields.Int()
            b = fields.Bool()

        # The field attributes should not be present on the final class.
        assert not hasattr(Example, 'a')
        assert not hasattr(Example, 'b')

        # But they should be in the _fields attribute
        assert Example.__fields__.a == fields.Int()
        assert Example.__fields__.b == fields.Bool()

    def test___new___subclassed_basic(self):
        # When extending a Model the parent field attributes should also be
        # present.

        class Example(Model):
            a = fields.Int()
            b = fields.Bool()

        class Example2(Example):
            pass

        assert Example2.__fields__.a == fields.Int()
        assert Example2.__fields__.b == fields.Bool()

    def test___new___subclassed_overriding_fields(self):
        # Subclassed Models with Fields of the same name should override the
        # parent Fields.

        class Example(Model):
            a = fields.Int()
            b = fields.Int()

        class Example2(Example):
            b = fields.Float()
            c = fields.Float()

        assert Example2.__fields__.a == fields.Int()
        assert Example2.__fields__.b == fields.Float()
        assert Example2.__fields__.c == fields.Float()

    def test___new___subclassed_overriding_attributes(self):
        # Subclassed Models with functions, attributes, and properties should
        # override the Fields.

        class Example(Model):
            a = fields.Int()
            b = fields.Bool()
            c = fields.Str()

        class Example2(Model):

            @property
            def a(self):
                return 'is a'

            def b(self):
                return 'is b'

            c = 'is c'

        assert not hasattr(Example2.__fields__, 'a')
        assert not hasattr(Example2.__fields__, 'b')
        assert not hasattr(Example2.__fields__, 'c')

        model = Example2()
        assert model.a == 'is a'
        assert model.b() == 'is b'
        assert model.c == 'is c'

    def test___new__subclassed_overriding_model_methods(self):
        # Subclassed Models can easily call override Model methods and call
        # super() if they so wish.

        class Example(Model):
            a = fields.Int()

        class Example2(Example):

            def __init__(self):
                super(Example2, self).__init__(a=5)

        assert Example2.__fields__.a == fields.Int()
        assert Example2().a == 5

    def test___new___meta_class(self):
        # Check that a basic Model Meta class works.

        class Example(Model):
            class Meta:
                tag = tags.Internal(tag='kind')

        assert Example.__tags__ == [tags.Internal(tag='kind')]

    def test___init___empty(self):
        # An empty Model with no Fields should work just fine.

        class Example(Model):
            pass

        assert Example().__dict__ == {}

        with raises(InstantiationError) as e:
            Example(a=None)
        assert e.value.pretty() == """\
InstantiationError: invalid keyword argument 'a'"""

    def test___init___normal(self):
        # Check that a normal Field behaves as it should.

        class Example(Model):
            a = fields.Int()

        assert Example(a=5).a == 5

        with raises(InstantiationError) as e:
            Example()
        assert e.value.pretty() == """\
InstantiationError: expected attribute 'a'
    Due to => NormalizationError: expected attribute 'a'
    Due to => field 'a' of type 'Int' on model 'Example'"""

    def test___init___abstract(self):
        # Check that you can't instantiate an abstract Model.

        class Example(Model):
            class Meta:
                abstract = True

        with raises(InstantiationError) as e:
            Example()
        assert e.value.pretty() == """\
InstantiationError: unable to instantiate abstract Model 'Example'"""

    def test___init___optional(self):
        # Check that an Optional Field behaves as it should.

        class Example(Model):
            a = fields.Optional(fields.Int)

        assert Example().a is None
        assert Example(a=5).a == 5

    def test___init___default(self):
        # Check that the default Field value is applied correctly.

        class Example(Model):
            a = fields.Optional(fields.Int, default=0)

        assert Example().a == 0
        assert Example(a=5).a == 5

    def test___init___args_vs_kwargs(self):
        # Check that you can pass in Field values as arguments.

        class Example(Model):
            a = fields.Int()
            b = fields.Str()

        model = Example(a=5, b='test')
        assert model.a == 5
        assert model.b == 'test'

        model = Example(5, 'test')
        assert model.a == 5
        assert model.b == 'test'

    def test___init___args_multiple(self):
        # Check that you are not allowed to pass the same argument twice and
        # that you can't pass more arguments than fields.

        class Example(Model):
            a = fields.Int()

        with raises(SerdeError) as e:
            Example(5, a=5)
        assert e.value.pretty() == """\
InstantiationError: __init__() got multiple values for keyword argument 'a'"""

        with raises(SerdeError):
            Example(5, 6)

    def test___init___normalizers(self):
        # The __init__() method should apply custom normalizers.

        class Example(Model):
            a = fields.Str(normalizers=[lambda x: x[::-1]])

        model = Example(a='test')
        assert model.a == 'tset'

    def test___init___validation(self):
        # The __init__() method should validate the values.

        class Example(Model):
            a = fields.Int()
            b = fields.Optional(fields.Str)

        Example(a=5, b=None)

        with raises(InstantiationError):
            Example(a=None)

        with raises(InstantiationError):
            Example(a='test')

        with raises(InstantiationError):
            Example(b=5)

    def test___init___validators(self):
        # Check that extra validators work.

        class Example(Model):
            a = fields.Int(validators=[validate.between(100, 200)])

        assert Example(a=101).a == 101

        with raises(InstantiationError):
            Example(a=5)

    def test___init___nested(self):
        # Check that nested Model construction works.

        class NestedExample(Model):
            a = fields.Int()

        class Example(Model):
            nested = fields.Nested(NestedExample)

        model = Example(nested=NestedExample(a=5))
        assert model.nested == NestedExample(a=5)
        assert model.nested.a == 5

    def test___eq__(self):
        # Check that the Model equals method works.

        class Example(Model):
            a = fields.Int()
            b = fields.Optional(fields.Bool)

        assert Example(a=5) != Example(a=6)
        assert Example(a=5) != Example(a=6, b=True)
        assert Example(a=5) == Example(a=5)

    def test___eq___subclass(self):
        # Check that the Model equals method works with subclasses.

        class Example(Model):
            a = fields.Int()
            b = fields.Optional(fields.Bool)

        class SubExample(Example):
            pass

        assert SubExample(a=5, b=True) != Example(a=5, b=True)
        assert Example(a=5, b=True) != SubExample(a=5, b=True)
        assert Example(a=5, b=True) == Example(a=5, b=True)
        assert SubExample(a=5, b=True) == SubExample(a=5, b=True)

    def test___hash___basic(self):
        # Check that a basic Model hash works.

        class Example(Model):
            a = fields.Int()

        assert hash(Example(5)) == hash(Example(a=5))
        assert hash(Example(5)) != hash(Example(a=4))

    def test___hash___nested(self):
        # Check that a nested Model hash works.

        class NestedExample(Model):
            a = fields.Int()

        class Example(Model):
            nested = fields.Nested(NestedExample)

        assert hash(Example(NestedExample(5))) == hash(Example(nested=NestedExample(a=5)))
        assert hash(Example(NestedExample(5))) != hash(Example(nested=NestedExample(a=4)))

    @py3
    def test___repr___basic(self):
        # Check that a basic Model __repr__ works.

        class Example(Model):
            a = fields.Int()
            b = fields.Str()

        r = repr(Example(a=5, b='test'))
        print(r)
        assert r.startswith(
            '<tests.test_model.TestModel.'
            'test___repr___basic.<locals>.Example model at'
        )

    @py3
    def test___repr___nested(self):
        # Check that a nested Model __repr__ works.

        class NestedExample(Model):
            a = fields.Int()

        class Example(Model):
            nested = fields.Nested(NestedExample)

        r = repr(Example(nested=NestedExample(a=5)))
        assert r.startswith(
            '<tests.test_model.TestModel.'
            'test___repr___nested.<locals>.Example model at'
        )

    def test__normalize_good(self):
        # _normalize() should renormalize the Model so that if we have
        # changed values they are normalized.

        class Example(Model):
            a = fields.Str(normalizers=[lambda x: x[::-1]])

        model = Example(a='unused')
        model.a = 'test'
        model._normalize()
        assert model.a == 'tset'

    def test__normalize_bad_normalizers(self):
        # _normalize() should raise normalization exceptions.

        def raises_exception(value):
            raise ValueError

        class Example(Model):
            a = fields.Str()

        model = Example(a='test')
        model.__class__._fields.a.normalizers = [raises_exception]

        with raises(NormalizationError):
            model._normalize()

    def test__normalize_bad_normalize(self):
        # _normalize() should raise a NormalizationError that will be mapped
        # to an InstantiationError.

        class Example(Model):
            a = fields.Str()

        def normalize(self):
            raise ValueError

        model = Example(a='test')
        Example.normalize = normalize

        with raises(NormalizationError):
            model._normalize()

    def test__validate(self):
        # _validate() should revalidate the Model so that if we have changed
        # values they are validated.

        class Example(Model):
            a = fields.Int(validators=[validate.min(100)])

        model = Example(a=101)
        model.a = 5
        with raises(ValidationError):
            model._validate()

    def test_validate(self):
        # You should be able to specify custom Model validation by overriding
        # the validate() method.

        class Example(Model):
            a = fields.Int()

            def validate(self):
                assert self.a != 0

        with raises(InstantiationError):
            Example(a=0)

        model = Example(a=5)
        model.a = 0
        with raises(ValidationError):
            model._validate()

    def test_validation_error_context(self):
        # Check that error context is added to ValidationErrors.

        class Example(Model):
            a = fields.Int()

        try:
            Example(a='not an integer')
        except InstantiationError as e:
            assert e.model_cls is Example
            assert e.field is Example.__fields__.a
            assert e.value == 'not an integer'

    def test_from_dict_empty(self):
        # Check that an empty Model deserializes from empty dictionary.

        class Example(Model):
            pass

        assert Example.from_dict({}) == Example()

    def test_from_dict_consumed(self):
        # Check that a dictionary is left untouched during deserialization.

        class NestedExample(Model):
            a = fields.Int()

        class Example(Model):
            nested = fields.Nested(NestedExample)

        d = {'nested': {'a': 5}}
        Example.from_dict(d)
        assert d == {'nested': {'a': 5}}

    def test_from_dict_consumed_externally_tagged(self):
        # Check that a dictionary is left untouched during deserialization of an
        # externally tagged Model.

        class NestedExample(Model):
            a = fields.Int()

        class Example(Model):
            class Meta:
                tag = tags.External()

            nested = fields.Nested(NestedExample)

        d = {'Example': {'nested': {'a': 5}}}
        Example.from_dict(d)
        assert d == {'Example': {'nested': {'a': 5}}}

    def test_from_dict_consumed_internally_tagged(self):
        # Check that a dictionary is left untouched during deserialization of an
        # internally tagged Model.

        class NestedExample(Model):
            a = fields.Int()

        class Example(Model):
            class Meta:
                tag = tags.Internal(tag='kind')

            nested = fields.Nested(NestedExample)

        d = {'kind': 'Example', 'nested': {'a': 5}}
        Example.from_dict(d)
        assert d == {'kind': 'Example', 'nested': {'a': 5}}

    def test_from_dict_consumed_adjacently_tagged(self):
        # Check that a dictionary is left untouched during deserialization of an
        # adjacently tagged Model.

        class NestedExample(Model):
            a = fields.Int()

        class Example(Model):
            class Meta:
                tag = tags.Adjacent(tag='kind', content='data')

            nested = fields.Nested(NestedExample)

        d = {'kind': 'Example', 'data': {'nested': {'a': 5}}}
        Example.from_dict(d)
        assert d == {'kind': 'Example', 'data': {'nested': {'a': 5}}}

    def test_from_dict_required(self):
        # Check that required Fields have to be present when deserializing.

        class Example(Model):
            a = fields.Int()

        assert Example.from_dict({'a': 5}) == Example(a=5)

        with raises(DeserializationError):
            Example.from_dict({})

    def test_from_dict_optional(self):
        # Check that optional Fields do not have to be present when
        # deserializing.

        class Example(Model):
            a = fields.Optional(fields.Int)

        assert Example.from_dict({'a': 5}) == Example(a=5)
        assert Example.from_dict({}) == Example()

    def test_from_dict_rename(self):
        # Check that renaming a Field deserializes that value.

        class Example(Model):
            a = fields.Int(rename='b')

        assert Example.from_dict({'b': 5}) == Example(a=5)

        with raises(DeserializationError):
            Example.from_dict({'a': 5})

    def test_from_dict_modified___init__(self):
        # Check that overriding the __init__ method does not break from_dict().

        class Example(Model):
            a = fields.Int()

            def __init__(self):
                super(Example, self).__init__(a=5)

        assert Example.from_dict({'a': 5}) == Example()

    def test_from_dict_nested(self):
        # Check that nested Models are parsed correctly.

        class NestedExample(Model):
            a = fields.Int()

        class Example(Model):
            nested = fields.Nested(NestedExample)

        assert Example.from_dict({'nested': {'a': 5}}) == Example(nested=NestedExample(a=5))

        with raises(DeserializationError):
            Example.from_dict({'nested': 'not the nested'})

    def test_from_dict_externally_tagged(self):
        # Check that externally tagged variants work correctly.

        class Example(Model):
            class Meta:
                tag = tags.External()
            a = fields.Int()

        class SubExample(Example):
            b = fields.Float()

        # Deserializing tagged data from the parent (allowed)
        assert Example.from_dict({'Example': {'a': 5}}) == Example(a=5)
        assert Example.from_dict({'SubExample': {'a': 5, 'b': 1.0}}) == SubExample(a=5, b=1.0)

        # Deserializing untagged data from the parent (not allowed)
        with raises(DeserializationError):
            Example.from_dict({'a': 5, 'b': 1.0})

        # Deserializing tagged data from the variant (not allowed)
        with raises(DeserializationError):
            SubExample.from_dict({'SubExample': {'a': 5, 'b': 1.0}})

        # Deserializing untagged data from the variant (allowed)
        assert SubExample.from_dict({'a': 5, 'b': 1.0}) == SubExample(a=5, b=1.0)

        # Edge case: empty data no tag
        with raises(DeserializationError):
            Example.from_dict({})

        # Edge case: abstract externally tagged
        Example._abstract = True
        with raises(DeserializationError):
            Example.from_dict({'Example': {'a': 5}})

    def test_from_dict_internally_tagged(self):
        # Check that internally tagged variants work correctly.

        class Example(Model):
            class Meta:
                tag = tags.Internal(tag='kind')
            a = fields.Int()

        class SubExample(Example):
            b = fields.Float()

        # Deserializing tagged data from the parent (allowed)
        serialized = {'kind': 'Example', 'a': 5}
        assert Example.from_dict(serialized) == Example(a=5)
        serialized = {'kind': 'SubExample', 'a': 5, 'b': 1.0}
        assert Example.from_dict(serialized) == SubExample(a=5, b=1.0)

        # Deserializing untagged data from the parent (not allowed)
        with raises(DeserializationError):
            Example.from_dict({'a': 5, 'b': 1.0})

        # Deserializing untagged data from the variant (allowed)
        assert SubExample.from_dict({'a': 5, 'b': 1.0}) == SubExample(a=5, b=1.0)

        # Edge case: abstract externally tagged
        Example._abstract = True
        with raises(DeserializationError):
            Example.from_dict({'kind': 'Example', 'a': 5})

    def test_from_dict_adjacently_tagged(self):
        # Check that adjacently tagged variants work correctly.

        class Example(Model):
            class Meta:
                tag = tags.Adjacent(tag='kind', content='data')
            a = fields.Int()

        class SubExample(Example):
            b = fields.Float()

        # Deserializing tagged data from the parent (allowed)
        serialized = {'kind': 'Example', 'data': {'a': 5}}
        assert Example.from_dict(serialized) == Example(a=5)
        serialized = {'kind': 'SubExample', 'data': {'a': 5, 'b': 1.0}}
        assert Example.from_dict(serialized) == SubExample(a=5, b=1.0)

        # Deserializing untagged data from the parent (not allowed)
        with raises(DeserializationError):
            Example.from_dict({'a': 5, 'b': 1.0})

        # Deserializing tagged data from the variant (not allowed)
        with raises(DeserializationError):
            SubExample.from_dict({'kind': 'SubExample', 'data': {'a': 5, 'b': 1.0}})

        # Deserializing untagged data from the variant (allowed)
        assert SubExample.from_dict({'a': 5, 'b': 1.0}) == SubExample(a=5, b=1.0)

        # Edge case: if the tag is correct but there is no content field
        with raises(DeserializationError):
            Example.from_dict({'kind': 'SubExample', 'content': {'a': 5, 'b': 1.0}})

        # Edge case: abstract adjacently tagged
        Example._abstract = True
        with raises(DeserializationError):
            Example.from_dict({'kind': 'Example', 'data': {'a': 5}})

    def test_from_dict_override_tag_for(self):
        # Check that from_dict() works when you modify the Meta.tag_for() method

        class ExampleTag(tags.Internal):
            def lookup_tag(self, variant):
                return variant.__name__.lower()

        class Example(Model):
            class Meta:
                tag = ExampleTag('kind')
            a = fields.Int()

        class SubExample(Example):
            b = fields.Float()

        serialized = {'kind': 'subexample', 'a': 5, 'b': 1.0}
        assert Example.from_dict(serialized) == SubExample(a=5, b=1.0)

    def test_from_dict_errors(self):
        # Check that all exceptions are mapped to DeserializationErrors.

        def always_raise(e):
            def actual_function(value):
                raise e()
            return actual_function

        class Example(Model):
            a = fields.Int()

        Example.__fields__.a.deserialize = always_raise(AssertionError)
        with raises(DeserializationError):
            Example.from_dict({'a': 5})

        Example.__fields__.a.deserialize = always_raise(DeserializationError)
        with raises(DeserializationError):
            Example.from_dict({'a': 5})

        Example.__fields__.a.deserialize = always_raise(Exception)
        with raises(DeserializationError):
            Example.from_dict({'a': 5})

    def test_deserialization_error_context(self):
        # Check that error context is added to DeserializationErrors.

        class Example(Model):
            a = fields.DateTime()

        try:
            Example.from_dict({'a': 'not a datetime'})
        except DeserializationError as e:
            assert e.model_cls is Example
            assert e.field is Example.__fields__.a
            assert e.value == 'not a datetime'

    def test_from_dict_deserializers(self):
        # Check that custom deserializers are applied.

        class Example(Model):
            a = fields.Str(deserializers=[lambda x: x[::-1]])

        assert Example.from_dict({'a': 'test'}) == Example(a='tset')

    def test_from_dict_normalizers(self):
        # Check that custom normalizers are applied.

        class Example(Model):
            a = fields.Str(normalizers=[lambda x: x[::-1]])

        model = Example.from_dict({'a': 'test'})
        assert model.a == 'tset'

    def test_from_json_basic(self):
        # Check that you can deserialize from JSON.

        class Example(Model):
            a = fields.Int()

        assert Example.from_json('{"a": 5}') == Example(a=5)

    def test_from_json_kwargs(self):
        # Check that extra JSON kwargs can be passed.

        class Example(Model):
            a = fields.Int()

        assert Example.from_json('{"a": 5}', object_hook=OrderedDict) == Example(a=5)

    def test_to_dict_empty(self):
        # Check that an empty Model serializes to an empty dictionary.

        class Example(Model):
            pass

        assert Example().to_dict() == {}

    def test_to_dict_normal(self):
        # Check that Fields need to be present when serializing.

        class Example(Model):
            a = fields.Int()

        assert Example(a=5).to_dict() == {'a': 5}

    def test_to_dict_optional(self):
        # Check that unset optional Fields are not present when serializing.

        class Example(Model):
            a = fields.Optional(fields.Int)

        assert Example().to_dict() == {}

    def test_to_dict_rename(self):
        # Check that renaming a Field serializes that value.

        class Example(Model):
            a = fields.Int(rename='b')

        assert Example(a=5).to_dict() == {'b': 5}

    def test_to_dict_nested(self):
        # Check that nested Models are serialized correctly.

        class NestedExample(Model):
            a = fields.Int()

        class Example(Model):
            nested = fields.Nested(NestedExample)

        assert Example(nested=NestedExample(a=5)).to_dict() == {'nested': {'a': 5}}

    def test_to_dict_externally_tagged(self):
        # Check that externally tagged variants work correctly.

        class Example(Model):
            class Meta:
                tag = tags.External()
            a = fields.Int()

        class SubExample(Example):
            b = fields.Float()

        # Serializing data from the parent
        assert Example(a=5).to_dict() == {'Example': {'a': 5}}

        # Serializing data from the variant
        assert SubExample(a=5, b=1.0).to_dict() == {'SubExample': {'a': 5, 'b': 1.0}}

    def test_to_dict_internally_tagged(self):
        # Check that internally tagged variants work correctly.

        class Example(Model):
            class Meta:
                tag = tags.Internal(tag='kind')
            a = fields.Int()

        class SubExample(Example):
            b = fields.Float()

        # Serializing data from the parent
        assert Example(a=5).to_dict() == {'kind': 'Example', 'a': 5}

        # Serializing data from the variant
        assert SubExample(a=5, b=1.0).to_dict() == {'kind': 'SubExample', 'a': 5, 'b': 1.0}

    def test_to_dict_adjacently_tagged(self):
        # Check that adjacently tagged variants work correctly.

        class Example(Model):
            class Meta:
                tag = tags.Adjacent(tag='kind', content='data')
            a = fields.Int()

        class SubExample(Example):
            b = fields.Float()

        # Serializing data from the parent
        assert Example(a=5).to_dict() == {'kind': 'Example', 'data': {'a': 5}}

        # Serializing data from the variant
        expected = {'kind': 'SubExample', 'data': {'a': 5, 'b': 1.0}}
        assert SubExample(a=5, b=1.0).to_dict() == expected

    def test_to_dict_override_tag_for(self):
        # Check that to_dict() works when you modify the Meta.tag_for() method
        class ExampleTag(tags.Internal):
            def lookup_tag(self, variant):
                return variant.__name__.lower()

        class Example(Model):
            class Meta:
                tag = ExampleTag(tag='kind')
            a = fields.Int()

        class SubExample(Example):
            b = fields.Float()

        assert SubExample(a=5, b=1.0).to_dict() == {'kind': 'subexample', 'a': 5, 'b': 1.0}

    def test_to_dict_errors(self):
        # Check that all exceptions are mapped to SerializationErrors.

        def always_raise(e):
            def actual_function(value):
                raise e()
            return actual_function

        class Example(Model):
            a = fields.Int()

        Example.__fields__.a.serialize = always_raise(AssertionError)
        with raises(SerializationError):
            Example(a=5).to_dict()

        Example.__fields__.a.serialize = always_raise(SerializationError)
        with raises(SerializationError):
            Example(a=5).to_dict()

        Example.__fields__.a.serialize = always_raise(Exception)
        with raises(SerializationError):
            Example(a=5).to_dict()

    def test_serialization_error_context(self):
        # Check that error context is added to SerializationErrors.

        class Example(Model):
            a = fields.DateTime()

        try:
            model = Example(a=datetime.datetime.utcnow())
            model.a = 'not a datetime'
        except SerializationError as e:
            assert e.model_cls is Example
            assert e.field is Example.__fields__.a
            assert e.value == 'not a datetime'

    def test_to_dict_serializers(self):
        # Check that custom serializers are applied.

        class Example(Model):
            a = fields.Str(serializers=[lambda x: x[::-1]])

        assert Example(a='tset').to_dict() == {'a': 'test'}

    def test_to_json_basic(self):
        # Check that you can serialize to JSON.

        class Example(Model):
            a = fields.Int()

        assert Example(a=50).to_json() == '{"a": 50}'

    def test_to_json_kwargs(self):
        # Check that extra JSON kwargs can be passed.

        class Example(Model):
            b = fields.Str()
            a = fields.Int()

        assert Example(a=5, b='test').to_json(sort_keys=True) == '{"a": 5, "b": "test"}'
