import datetime

import mock
from pytest import raises

from serde import Model, field
from serde.error import DeserializationError, SerdeError, SerializationError, ValidationError
from tests import py2_patch_str_with_basestring


class TestModel:

    def test___new__(self):
        class Example(Model):
            a = field.Int()
            b = field.Bool()

        # The field attributes should not be present on the final class.
        assert not hasattr(Example, 'a')
        assert not hasattr(Example, 'b')

        # But they should be in the _fields attribute
        assert hasattr(Example._fields, 'a')
        assert hasattr(Example._fields, 'b')

        with raises(AttributeError):
            Example._fields.c

        # When extending a model the parent field attributes should also be
        # present, but subclass fields of the same name should override them.
        class Example2(Example):
            b = field.Float()
            c = field.Float()

        assert hasattr(Example2._fields, 'a')
        assert isinstance(Example2._fields.a, field.Int)
        assert hasattr(Example2._fields, 'b')
        assert isinstance(Example2._fields.b, field.Float)
        assert hasattr(Example2._fields, 'c')
        assert isinstance(Example2._fields.c, field.Float)

        class Example3(Example2):
            pass

        assert hasattr(Example2._fields, 'a')
        assert isinstance(Example2._fields.a, field.Int)
        assert hasattr(Example2._fields, 'b')
        assert isinstance(Example2._fields.b, field.Float)
        assert hasattr(Example2._fields, 'c')
        assert isinstance(Example2._fields.c, field.Float)

        class Example4(Model):
            a = field.Int()
            b = field.Float()

            def __init__(self):
                super(Example4, self).__init__(a=5, b=50.5)

        assert hasattr(Example4._fields, 'a')
        assert isinstance(Example4._fields.a, field.Int)
        assert hasattr(Example4._fields, 'b')
        assert isinstance(Example4._fields.b, field.Float)

        example = Example4()
        assert example.a == 5
        assert example.b == 50.5

        class Example5(Example4):
            b = field.Int()
            c = field.Float()

            def __init__(self):
                super(Example4, self).__init__(a=5, b=50, c=100.5)

        assert hasattr(Example5._fields, 'a')
        assert isinstance(Example5._fields.a, field.Int)
        assert hasattr(Example5._fields, 'b')
        assert isinstance(Example5._fields.b, field.Int)
        assert hasattr(Example5._fields, 'c')
        assert isinstance(Example5._fields.c, field.Float)

        example = Example5()
        assert example.a == 5
        assert example.b == 50
        assert example.c == 100.5

    def test___init__(self):
        # A simple Model with no fields.
        class Example(Model):
            pass

        example = Example()
        assert example.__dict__ == {}

        # Instantiating this with parameters should fail.
        with raises(SerdeError):
            Example(None)

        with raises(SerdeError):
            Example(a=None)

        # A simple Model with one required field and one optional
        class Example(Model):
            a = field.Int(required=False)
            b = field.Bool()

        # Passing in the same argument twice.
        with raises(SerdeError):
            Example(5, a=6)

        # Just passing in the required
        example = Example(b=True)
        assert example.__dict__ == {'b': True, 'a': None}

        # Passing in optional as well
        example = Example(a=5, b=False)
        assert example.__dict__ == {'b': False, 'a': 5}

        # Not passing in any args should fail.
        with raises(ValidationError):
            Example()

        # Passing in arguments of the wrong type should fail validation
        with raises(ValidationError):
            Example(b='test')

        with raises(ValidationError):
            Example(b=None)

        with raises(ValidationError):
            Example(a=5.5, b=True)

        # A more complex Model
        class SubExample(Model):
            x = field.Int()

        def assert_value_between_0_and_20(value):
            assert 0 <= value < 20

        class Example(Model):
            a = field.Int(validators=[assert_value_between_0_and_20])
            b = field.Bool(required=False, default=False)
            c = field.Nested(SubExample, required=False)
            d = field.Nested(SubExample)

        # Just passing in required
        example = Example(a=5, d=SubExample(x=10))
        assert example.__dict__ == {'a': 5, 'b': False, 'c': None, 'd': SubExample(x=10)}

        # Passing in all
        example = Example(a=5, c=SubExample(x=50), b=True, d=SubExample(x=10))
        assert example.__dict__ == {'a': 5, 'b': True, 'c': SubExample(x=50), 'd': SubExample(x=10)}

        # Not passing in all the required kwargs should fail.
        with raises(ValidationError):
            Example(a=5)

        # Passing in arguments of the wrong type should fail validation
        with raises(ValidationError):
            Example(a='test', d=SubExample(x=10))

        with raises(ValidationError):
            Example(a=5, d=Example(a=5, d=SubExample(x=10)))

        with raises(ValidationError):
            Example(a=5, d=SubExample(x=10), b=5)

        with raises(ValidationError):
            Example(a=5, d=SubExample(x=10), c=Example(a=5, d=SubExample(x=10)))

        with raises(ValidationError):
            Example(a=30, d=SubExample(x=10))

    def test___eq__(self):
        class Example(Model):
            a = field.Int()
            b = field.Bool(required=False)

        assert Example(a=5) != Example(a=6)
        assert Example(a=5) != Example(a=6, b=True)
        assert Example(a=5) == Example(a=5)

    def test___hash__(self):
        # A more complex Model with a sub Model
        class SubExample(Model):
            x = field.Float()

        class Example(Model):
            a = field.List(field.Int)
            b = field.Nested(SubExample)

        assert (hash(Example(a=[5], b=SubExample(x=10.5)))
                == hash(Example(a=[5], b=SubExample(x=10.5))))
        assert (hash(Example(a=[5], b=SubExample(x=10.5)))
                != hash(Example(a=[5], b=SubExample(x=10.0))))

    def test_to_dict(self):
        class Example(Model):
            a = field.Int()
            b = field.Bool(required=False)

        example = Example(a=5)
        assert example.to_dict() == {'a': 5}

        example = Example(a=5, b=False)
        assert example.to_dict() == {'a': 5, 'b': False}

        # A more complex Model with a sub Model
        class SubExample(Model):
            x = field.Float(serializers=[lambda x: x])

        class Example(Model):
            a = field.Int(rename='d')
            b = field.Nested(SubExample)
            c = field.Bool(required=False)

        example = Example(a=5, b=SubExample(x=10.5))
        assert example.a == 5
        assert example.to_dict() == {'d': 5, 'b': {'x': 10.5}}

        example = Example(a=5, b=SubExample(x=10.5), c=True)
        assert example.to_dict() == {'d': 5, 'b': {'x': 10.5}, 'c': True}

        class Example(Model):
            a = field.List(field.Int)

        example = Example(a=[1, 2, 3, 4])

        # set a bad value
        example.a = 5

        with raises(SerializationError):
            example.to_dict()

        # Make the field always fail serialization
        def serialize(value):
            raise SerializationError('unable to serialize {}'.format(value))

        example = Example(a=[1, 2, 3, 4])
        Example._fields.a.serialize = serialize

        with raises(SerializationError):
            example.to_dict()

    def test_from_dict(self):
        # A simple Model.
        class Example(Model):
            a = field.Int()
            b = field.Bool(required=False)

        example = Example(a=5)
        assert Example.from_dict({'a': 5}) == example

        example = Example(a=5, b=False)
        assert Example.from_dict({'a': 5, 'b': False}) == example

        with raises(DeserializationError):
            Example.from_dict({'a': 5, 'b': False, 'c': 'extra'})

        with raises(DeserializationError):
            Example.from_dict({'b': False})

        # A more complex Model with a sub Model
        class SubExample(Model):
            x = field.Float(deserializers=[lambda x: x])

        class Example(Model):
            a = field.Int()
            b = field.Nested(SubExample)
            c = field.Bool(required=False)

        example = Example(a=5, b=SubExample(x=10.5))
        assert Example.from_dict({'a': 5, 'b': {'x': 10.5}}) == example

        example = Example(a=5, b=SubExample(x=10.5), c=True)
        assert Example.from_dict({'a': 5, 'b': {'x': 10.5}, 'c': True}) == example

        example = Example.from_dict({'a': 5, 'b': {'x': 10.5}})
        assert isinstance(example.b, SubExample)

        with raises(DeserializationError):
            Example.from_dict({'a': 5, 'b': {'x': 10.5}, 'z': True})

        example = Example.from_dict({'a': 5, 'b': {'x': 10.5}, 'z': True}, strict=False)
        assert not hasattr(example, 'z')

        # Make the field always fail serialization
        def deserialize(value):
            raise DeserializationError('unable to deserialize {}'.format(value))

        Example._fields.a.deserialize = deserialize

        with raises(DeserializationError):
            Example.from_dict({'a': 5, 'b': {'x': 10.5}})

        # Generic exceptions should also be mapped to a Deserialization error
        def deserialize(value):
            raise Exception('unable to deserialize {}'.format(value))

        Example._fields.a.deserialize = deserialize

        with raises(DeserializationError):
            Example.from_dict({'a': 5, 'b': {'x': 10.5}})

    @py2_patch_str_with_basestring
    def test_from_json(self):
        class Example(Model):
            a = field.Int()
            b = field.Str()

        assert Example.from_json('{"a": 50, "b": "test"}') == Example(a=50, b='test')

    def test_to_json(self):
        class Example(Model):
            a = field.Int()
            b = field.Str()

        example = Example(a=50, b='test')
        assert example.to_json(sort_keys=True) == '{"a": 50, "b": "test"}'

    @py2_patch_str_with_basestring
    def test_from_toml(self):
        class Example(Model):
            a = field.Int()
            b = field.Str()

        with mock.patch('serde.model.toml', None):
            with raises(SerdeError):
                Example.from_toml('a = 50\nb = "test"\n')

        assert Example.from_toml('a = 50\nb = "test"\n') == Example(a=50, b='test')

    def test_to_toml(self):
        class Example(Model):
            a = field.Int()
            b = field.Str()

        example = Example(a=50, b='test')
        assert example.to_toml() == 'a = 50\nb = "test"\n'

    def test_from_yaml(self):
        class Example(Model):
            a = field.Int()
            b = field.Str()

        with mock.patch('serde.model.yaml', None):
            with raises(SerdeError):
                Example.from_yaml('a: 50\nb: test\n')

        assert Example.from_yaml('a: 50\nb: test\n') == Example(a=50, b='test')

    def test_to_yaml(self):
        class Example(Model):
            a = field.Int()
            b = field.Str()

        example = Example(a=50, b='test')
        assert example.to_yaml(dict=dict, default_flow_style=False) == 'a: 50\nb: test\n'

    def test_serialization_error_context(self):
        class Example(Model):
            a = field.DateTime()

        try:
            example = Example(a=datetime.datetime.utcnow())
            example.a = 'not a datetime'

        except SerializationError as e:
            assert e.model is Example
            assert e.field is Example._fields.a
            assert e.value == 'not a datetime'

    def test_deserialization_error_context(self):
        class Example(Model):
            a = field.DateTime()

        try:
            Example.from_dict({'a': 'not a datetime'})
        except DeserializationError as e:
            assert e.model is Example
            assert e.field is Example._fields.a
            assert e.value == 'not a datetime'

    def test_validation_error_context(self):
        class Example(Model):
            a = field.Int()

        try:
            Example('not an field.Int')
        except ValidationError as e:
            assert e.model is Example
            assert e.field is Example._fields.a
            assert e.value == 'not an field.Int'
