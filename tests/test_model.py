import datetime
from collections import OrderedDict

import mock
from pytest import raises

import serde.model
from serde import Model, fields, validate
from serde.exceptions import (
    DeserializationError,
    InstantiationError,
    MissingDependency,
    NormalizationError,
    SerdeError,
    SerializationError,
    ValidationError
)
from tests import py2, py3


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
            a = fields.Int()
            b = fields.Bool()

        # The field attributes should not be present on the final class.
        assert not hasattr(Example, 'a')
        assert not hasattr(Example, 'b')

        # But they should be in the _fields attribute
        assert isinstance(Example._fields.a, fields.Int)
        assert isinstance(Example._fields.b, fields.Bool)

    def test___new___subclassed_basic(self):
        # When extending a Model the parent field attributes should also be
        # present.

        class Example(Model):
            a = fields.Int()
            b = fields.Bool()

        class Example2(Model):
            pass

        assert isinstance(Example._fields.a, fields.Int)
        assert isinstance(Example._fields.b, fields.Bool)

    def test___new___subclassed_overriding_fields(self):
        # Subclassed Models with Fields of the same name should override the
        # parent Fields.

        class Example(Model):
            a = fields.Int()
            b = fields.Int()

        class Example2(Example):
            b = fields.Float()
            c = fields.Float()

        assert isinstance(Example2._fields.a, fields.Int)
        assert isinstance(Example2._fields.b, fields.Float)
        assert isinstance(Example2._fields.c, fields.Float)

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
            a = fields.Int()

        class Example2(Example):

            def __init__(self):
                super(Example2, self).__init__(a=5)

        assert isinstance(Example2._fields.a, fields.Int)
        assert Example2().a == 5

    def test___new___meta_class(self):
        # Check that a basic Model Meta class works.

        class Example(Model):
            class Meta:
                tag = 'kind'

        assert isinstance(Example._meta, serde.model.Meta)
        assert Example._meta.tag == 'kind'

    def test___init___empty(self):
        # An empty Model with no Fields should work just fine.

        class Example(Model):
            pass

        assert Example().__dict__ == {}

        with raises(InstantiationError):
            Example(a=None)

        with raises(InstantiationError):
            Example(a=None)

    def test___init___normal(self):
        # Check that a normal Field behaves as it should.

        class Example(Model):
            a = fields.Int()

        assert Example(a=5).a == 5

        with raises(InstantiationError):
            Example()

    def test___init___abstract(self):
        # Check that you can't instantiate an abstract Model.

        class Example(Model):
            class Meta:
                abstract = True

        with raises(InstantiationError):
            Example()

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
            a = fields.Int()

        with raises(SerdeError):
            Example(5, a=5)

        with raises(SerdeError):
            Example(5, 6)

    def test___init___normalizers(self):
        # The __init__() method should apply custom normalizers.

        class Example(Model):
            a = fields.Str(normalizers=[lambda x: x[::-1]])

        example = Example(a='test')
        assert example.a == 'tset'

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

        example = Example(nested=NestedExample(a=5))
        assert example.nested == NestedExample(a=5)
        assert example.nested.a == 5

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

    def test___repr___basic(self):
        # Check that a basic Model __repr__ works.

        class Example(Model):
            a = fields.Int()
            b = fields.Str()

        assert repr(Example(a=5, b='test')) == "Example(a=5, b='test')"

    def test___repr___nested(self):
        # Check that a nested Model __repr__ works.

        class NestedExample(Model):
            a = fields.Int()

        class Example(Model):
            nested = fields.Nested(NestedExample)

        assert repr(Example(nested=NestedExample(a=5))) == 'Example(nested=NestedExample(a=5))'

    def test_normalize_all_good(self):
        # normalize_all() should renormalize the Model so that if we have
        # changed values they are normalized.

        class Example(Model):
            a = fields.Str(normalizers=[lambda x: x[::-1]])

        example = Example(a='unused')
        example.a = 'test'
        example.normalize_all()
        assert example.a == 'tset'

    def test_normalize_all_bad_normalizers(self):
        # normalize_all() should raise normalization exceptions.

        class Example(Model):
            a = fields.Str()

        def raises_exception(value):
            raise ValueError

        example = Example(a='test')
        example._fields.a.normalizers = [raises_exception]

        with raises(NormalizationError):
            example.normalize_all()

    def test_normalize_all_bad_normalize(self):
        # normalize_all() should raise a NormalizationError that will be mapped
        # to an InstantiationError.

        class Example(Model):
            a = fields.Str()

        def normalize(self):
            raise ValueError

        example = Example(a='test')
        Example.normalize = normalize

        with raises(NormalizationError):
            example.normalize_all()

    def test_validate_all(self):
        # validate_all() should revalidate the Model so that if we have changed
        # values they are validated.

        class Example(Model):
            a = fields.Int(validators=[validate.min(100)])

        example = Example(a=101)
        example.a = 5
        with raises(ValidationError):
            example.validate_all()

    def test_validate(self):
        # You should be able to specify custom Model validation by overriding
        # the validate() method.

        class Example(Model):
            a = fields.Int()

            def validate(self):
                assert self.a != 0

        with raises(InstantiationError):
            Example(a=0)

        example = Example(a=5)
        example.a = 0
        with raises(ValidationError):
            example.validate_all()

    def test_validation_error_context(self):
        # Check that error context is added to ValidationErrors.

        class Example(Model):
            a = fields.Int()

        try:
            Example(a='not an integer')
        except InstantiationError as e:
            assert e.model is Example
            assert e.field is Example._fields.a
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
                tag = True

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
                tag = 'kind'

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
                tag = 'kind'
                content = 'data'

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

    def test_from_dict_strict(self):
        # Check that if strict is set then unknown keys are not allowed and
        # visa versa.

        class Example(Model):
            a = fields.Int()

        assert Example.from_dict({'a': 5, 'c': 'unknown'}, strict=False) == Example(a=5)

        with raises(DeserializationError):
            Example.from_dict({'a': 5, 'b': 'test', 'c': 'unknown'})

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

    def test_from_dict_untagged_tagged(self):
        # Check that untagged variants work correctly.

        class Example(Model):
            class Meta:
                tag = False
            a = fields.Int()

        class SubExampleA(Example):
            b = fields.Float()

        class SubExampleB(Example):
            c = fields.Float()

        # Deserializing untagged data from the parent (allowed)
        assert Example.from_dict({'a': 5}) == Example(a=5)
        assert Example.from_dict({'a': 5, 'b': 1.0}) == SubExampleA(a=5, b=1.0)
        assert Example.from_dict({'a': 5, 'c': 1.0}) == SubExampleB(a=5, c=1.0)

        # Deserializing untagged data from the variant (not allowed)
        with raises(DeserializationError):
            SubExampleA.from_dict({'a': 5})
        with raises(DeserializationError):
            SubExampleB.from_dict({'a': 5, 'b': 1.0})

        # Deserializing untagged data from the variant (allowed)
        assert SubExampleA.from_dict({'a': 5, 'b': 1.0}) == SubExampleA(a=5, b=1.0)
        assert SubExampleB.from_dict({'a': 5, 'c': 1.0}) == SubExampleB(a=5, c=1.0)

        # Edge case: bad data, all variants tried
        with raises(DeserializationError):
            Example.from_dict({'b': 1.0})

        # Edge case: abstract untagged variant
        Example._meta.abstract = True
        with raises(DeserializationError):
            Example.from_dict({'a': 5})

    def test_from_dict_externally_tagged(self):
        # Check that externally tagged variants work correctly.

        class Example(Model):
            class Meta:
                tag = True
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
        Example._meta.abstract = True
        with raises(DeserializationError):
            Example.from_dict({'Example': {'a': 5}})

    def test_from_dict_internally_tagged(self):
        # Check that internally tagged variants work correctly.

        class Example(Model):
            class Meta:
                tag = 'kind'
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

        # Deserializing tagged data from the variant (not allowed)
        with raises(DeserializationError):
            SubExample.from_dict({'kind': 'SubExample', 'a': 5, 'b': 1.0})

        # Deserializing untagged data from the variant (allowed)
        assert SubExample.from_dict({'a': 5, 'b': 1.0}) == SubExample(a=5, b=1.0)

        # Edge case: abstract externally tagged
        Example._meta.abstract = True
        with raises(DeserializationError):
            Example.from_dict({'kind': 'Example', 'a': 5})

    def test_from_dict_adjacently_tagged(self):
        # Check that adjacently tagged variants work correctly.

        class Example(Model):
            class Meta:
                tag = 'kind'
                content = 'data'
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
        Example._meta.abstract = True
        with raises(DeserializationError):
            Example.from_dict({'kind': 'Example', 'data': {'a': 5}})

    def test_from_dict_override_tag_for(self):
        # Check that from_dict() works when you modify the Meta.tag_for() method

        class Example(Model):
            class Meta:
                tag = 'kind'

                def tag_for(self, variant):
                    return variant.__name__.lower()

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
            a = fields.DateTime()

        try:
            Example.from_dict({'a': 'not a datetime'})
        except DeserializationError as e:
            assert e.model is Example
            assert e.field is Example._fields.a
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

        example = Example.from_dict({'a': 'test'})
        assert example.a == 'tset'

    def test_from_cbor(self):
        # Check that you can deserialize from CBOR.

        class Example(Model):
            a = fields.Int()

        assert Example.from_cbor(b'\xa1aa\x05') == Example(a=5)

        with mock.patch('serde.model.cbor', None):
            with raises(MissingDependency):
                Example(a=5).from_cbor(b'\xa1aa\x05')

    def test_from_json_basic(self):
        # Check that you can deserialize from JSON.

        class Example(Model):
            a = fields.Int()

        assert Example.from_json('{"a": 5}') == Example(a=5)

    def test_from_json_strict(self):
        # Check that the from_json() method passes through the strict option.

        class Example(Model):
            a = fields.Int()

        assert Example.from_json('{"a": 5, "b": "unknown"}', strict=False) == Example(a=5)

        with raises(DeserializationError):
            Example.from_json('{"a": 5, "b": "unknown"}')

    def test_from_json_kwargs(self):
        # Check that extra JSON kwargs can be passed.

        class Example(Model):
            a = fields.Int()

        assert Example.from_json('{"a": 5}', object_hook=OrderedDict) == Example(a=5)

    @py3
    def test_from_pickle(self):
        # Check that you can deserialize from Pickle.

        class Example(Model):
            a = fields.Int()

        assert Example.from_pickle(b'\x80\x03}q\x00X\x01\x00\x00\x00aq\x01K\x05s.') == Example(a=5)

    @py2
    def test_from_pickle_py2(self):
        # Check that you can deserialize from Pickle.

        class Example(Model):
            a = fields.Int()

        assert Example.from_pickle(b"(dp0\nS'a'\np1\nI5\ns.") == Example(a=5)

    def test_from_toml(self):
        # Check that you can deserialize from TOML, if its installed.

        class Example(Model):
            a = fields.Int()

        assert Example.from_toml('a = 5') == Example(a=5)

        with mock.patch('serde.model.toml', None):
            with raises(MissingDependency):
                Example.from_toml('a = 50')

    def test_from_yaml(self):
        # Check that you can deserialize from YAML, if its installed.

        class Example(Model):
            a = fields.Int()

        assert Example.from_yaml('a: 5') == Example(a=5)

        with mock.patch('serde.model.yaml', None):
            with raises(MissingDependency):
                Example.from_yaml('a: 5')

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

    def test_to_dict_type(self):
        # Check that the dictionary type can be modified.

        class Example(Model):
            a = fields.Int()

        class CustomDict(OrderedDict):
            def __eq__(self, other):
                return isinstance(other, CustomDict) and super(CustomDict, self).__eq__(other)

        assert Example(a=5).to_dict(dict=CustomDict) == CustomDict([('a', 5)])

    def test_to_dict_nested(self):
        # Check that nested Models are serialized correctly.

        class NestedExample(Model):
            a = fields.Int()

        class Example(Model):
            nested = fields.Nested(NestedExample)

        assert Example(nested=NestedExample(a=5)).to_dict() == {'nested': {'a': 5}}

    def test_to_dict_untagged_tagged(self):
        # Check that untagged variants work correctly.

        class Example(Model):
            class Meta:
                tag = False
            a = fields.Int()

        class SubExample(Example):
            b = fields.Float()

        # Serializing data from the parent
        assert Example(a=5).to_dict() == {'a': 5}

        # Serializing data from the variant
        assert SubExample(a=5, b=1.0).to_dict() == {'a': 5, 'b': 1.0}

    def test_to_dict_externally_tagged(self):
        # Check that externally tagged variants work correctly.

        class Example(Model):
            class Meta:
                tag = True
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
                tag = 'kind'
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
                tag = 'kind'
                content = 'data'
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

        class Example(Model):
            class Meta:
                tag = 'kind'

                def tag_for(self, variant):
                    return variant.__name__.lower()

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
            a = fields.DateTime()

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
            a = fields.Str(serializers=[lambda x: x[::-1]])

        assert Example(a='tset').to_dict() == {'a': 'test'}

    def test_to_cbor(self):
        # Check that you can serialize to CBOR.

        class Example(Model):
            a = fields.Int()

        Example.to_dict = mock.Mock(return_value={u'a': 5})
        assert Example(a=5).to_cbor() == b'\xa1aa\x05'

        with mock.patch('serde.model.cbor', None):
            with raises(MissingDependency):
                Example(a=5).to_cbor()

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

    @py3
    def test_to_pickle(self):
        # Check that you can serialize to Pickle.

        class Example(Model):
            a = fields.Int()

        assert Example(a=5).to_pickle(dict=dict) == b'\x80\x03}q\x00X\x01\x00\x00\x00aq\x01K\x05s.'

    @py2
    def test_to_pickle_py2(self):
        # Check that you can serialize to Pickle.

        class Example(Model):
            a = fields.Int()

        assert Example(a=5).to_pickle(dict=dict) == b"(dp0\nS'a'\np1\nI5\ns."

    def test_to_toml(self):
        # Check that you can serialize to TOML, if its installed.

        class Example(Model):
            a = fields.Int()

        assert Example(a=5).to_toml() == 'a = 5\n'

        with mock.patch('serde.model.toml', None):
            with raises(MissingDependency):
                Example(a=5).to_toml()

    def test_to_yaml(self):
        # Check that you can serialize to YAML, if its installed.

        class Example(Model):
            a = fields.Int()

        assert Example(a=5).to_yaml(dict=dict, default_flow_style=False) == 'a: 5\n'

        with mock.patch('serde.model.yaml', None):
            with raises(MissingDependency):
                Example(a=5).to_yaml()
