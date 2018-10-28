from pytest import raises

from serde.error import DeserializationError, SerializationError, ValidationError
from serde.field import Bool, Float, Int, List, ModelField, Str
from serde.model import Model


class TestModel:

    def test___new__(self):
        class Example(Model):
            a = Int()
            b = Bool()

        # The field attributes should not be present on the final class.
        assert not hasattr(Example, 'a')
        assert not hasattr(Example, 'b')

        # But they should be in the __fields__ attribute
        assert hasattr(Example.__fields__, 'a')
        assert hasattr(Example.__fields__, 'b')

        with raises(AttributeError):
            Example.__fields__.c

        # When extending a model the parent field attributes should also be
        # present, but subclass fields of the same name should override them.
        class Example2(Example):
            b = Float()
            c = Float()

        assert hasattr(Example2.__fields__, 'a')
        assert isinstance(Example2.__fields__.a, Int)
        assert hasattr(Example2.__fields__, 'b')
        assert isinstance(Example2.__fields__.b, Float)
        assert hasattr(Example2.__fields__, 'c')
        assert isinstance(Example2.__fields__.c, Float)

        class Example3(Example2):
            pass

        assert hasattr(Example2.__fields__, 'a')
        assert isinstance(Example2.__fields__.a, Int)
        assert hasattr(Example2.__fields__, 'b')
        assert isinstance(Example2.__fields__.b, Float)
        assert hasattr(Example2.__fields__, 'c')
        assert isinstance(Example2.__fields__.c, Float)

        class Example4(Model):
            a = Int()
            b = Float()

            def __init__(self):
                super().__init__(a=5, b=50.5)

        assert hasattr(Example4.__fields__, 'a')
        assert isinstance(Example4.__fields__.a, Int)
        assert hasattr(Example4.__fields__, 'b')
        assert isinstance(Example4.__fields__.b, Float)

        example = Example4()
        assert example.a == 5
        assert example.b == 50.5

        class Example5(Example4):
            b = Int()
            c = Float()

            def __init__(self):
                super().__init__(a=5, b=50, c=100.5)

        assert hasattr(Example5.__fields__, 'a')
        assert isinstance(Example5.__fields__.a, Int)
        assert hasattr(Example5.__fields__, 'b')
        assert isinstance(Example5.__fields__.b, Int)
        assert hasattr(Example5.__fields__, 'c')
        assert isinstance(Example5.__fields__.c, Float)

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
        with raises(TypeError):
            Example(None)

        with raises(TypeError):
            Example(a=None)

        # A simple Model with one required field and one optional
        class Example(Model):
            a = Int(required=False)
            b = Bool()

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
            x = Int()

        def assert_value_between_0_and_20(value):
            assert 0 <= value < 20

        class Example(Model):
            a = Int(validators=[assert_value_between_0_and_20])
            b = Bool(required=False, default=False)
            c = ModelField(SubExample, required=False)
            d = ModelField(SubExample)

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
            a = Int()
            b = Bool(required=False)

        assert Example(a=5) != Example(a=6)
        assert Example(a=5) != Example(a=6, b=True)
        assert Example(a=5) == Example(a=5)

    def test___hash__(self):
        # A more complex Model with a sub Model
        class SubExample(Model):
            x = Float()

        class Example(Model):
            a = List(Int)
            b = ModelField(SubExample)

        assert (hash(Example(a=[5], b=SubExample(x=10.5)))
                == hash(Example(a=[5], b=SubExample(x=10.5))))
        assert (hash(Example(a=[5], b=SubExample(x=10.5)))
                != hash(Example(a=[5], b=SubExample(x=10.0))))

    def test_to_dict(self):
        class Example(Model):
            a = Int()
            b = Bool(required=False)

        example = Example(a=5)
        assert example.to_dict() == {'a': 5}

        example = Example(a=5, b=False)
        assert example.to_dict() == {'a': 5, 'b': False}

        # A more complex Model with a sub Model
        class SubExample(Model):
            x = Float()

        class Example(Model):
            a = Int(rename='d')
            b = ModelField(SubExample)
            c = Bool(required=False)

        example = Example(a=5, b=SubExample(x=10.5))
        assert example.a == 5
        assert example.to_dict() == {'d': 5, 'b': {'x': 10.5}}

        example = Example(a=5, b=SubExample(x=10.5), c=True)
        assert example.to_dict() == {'d': 5, 'b': {'x': 10.5}, 'c': True}

        class Example(Model):
            a = List(Int)

        example = Example(a=[1, 2, 3, 4])

        # set a bad value
        example.a = 5

        with raises(SerializationError):
            example.to_dict()

        # Make the field always fail serialization
        def serialize(value):
            raise SerializationError('unable to serialize {}'.format(value))

        example = Example(a=[1, 2, 3, 4])
        Example.__fields__.a.serialize = serialize

        with raises(SerializationError):
            example.to_dict()

    def test_from_dict(self):
        # A simple Model.
        class Example(Model):
            a = Int()
            b = Bool(required=False)

        example = Example(a=5)
        assert Example.from_dict({'a': 5}) == example

        example = Example(a=5, b=False)
        assert Example.from_dict({'a': 5, 'b': False}) == example

        with raises(DeserializationError):
            Example.from_dict({'a': 5, 'b': False, 'c': 'extra'})

        # A more complex Model with a sub Model
        class SubExample(Model):
            x = Float()

        class Example(Model):
            a = Int()
            b = ModelField(SubExample)
            c = Bool(required=False)

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

        Example.__fields__.a.deserialize = deserialize

        with raises(DeserializationError):
            Example.from_dict({'a': 5, 'b': {'x': 10.5}})

        # Generic exceptions should also be mapped to a Deserialization error
        def deserialize(value):
            raise Exception('unable to deserialize {}'.format(value))

        Example.__fields__.a.deserialize = deserialize

        with raises(DeserializationError):
            Example.from_dict({'a': 5, 'b': {'x': 10.5}})

    def test_to_json(self):
        class Example(Model):
            a = Int()
            b = Str()

        example = Example(a=50, b='test')
        assert example.to_json(sort_keys=True) == '{"a": 50, "b": "test"}'

    def test_from_json(self):
        class Example(Model):
            a = Int()
            b = Str()

        assert Example.from_json('{"a": 50, "b": "test"}') == Example(a=50, b='test')
