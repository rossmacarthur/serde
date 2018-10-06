from pytest import raises

from serde.error import DeserializationError, SerializationError, ValidationError
from serde.field import Array, Boolean, Float, Integer, ModelField, String
from serde.model import Model


class TestModel:

    def test___new__(self):
        # A simple Model with no fields.
        class Example(Model):
            pass

        assert hasattr(Example, '__init__') and callable(Example.__init__)
        assert hasattr(Example, '__eq__') and callable(Example.__eq__)
        assert hasattr(Example, '__hash__') and callable(Example.__eq__)
        assert hasattr(Example, 'validate') and callable(Example.validate)
        assert hasattr(Example, 'to_dict') and callable(Example.to_dict)
        assert hasattr(Example, 'from_dict') and callable(Example.from_dict)

        class Example(Model):
            a = Integer()
            b = Boolean()

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
        assert isinstance(Example2.__fields__.a, Integer)
        assert hasattr(Example2.__fields__, 'b')
        assert isinstance(Example2.__fields__.b, Float)
        assert hasattr(Example2.__fields__, 'c')
        assert isinstance(Example2.__fields__.c, Float)

        class Example3(Example2):
            pass

        assert hasattr(Example2.__fields__, 'a')
        assert isinstance(Example2.__fields__.a, Integer)
        assert hasattr(Example2.__fields__, 'b')
        assert isinstance(Example2.__fields__.b, Float)
        assert hasattr(Example2.__fields__, 'c')
        assert isinstance(Example2.__fields__.c, Float)

    def test___init__(self):
        # A simple Model with no fields.
        class Example(Model):
            pass

        example = Example()
        assert example.__dict__ == {}

        # Instantiating this with parameters should fail.
        with raises(TypeError):
            Example(None)

        # A simple Model with one arg and one kwarg
        # optional fields become kwargs, non optional become args
        class Example(Model):
            a = Integer(optional=True)
            b = Boolean()

        # Just passing in the arg
        example = Example(True)
        assert example.__dict__ == {'b': True, 'a': None}

        # Passing in kwargs as well
        example = Example(False, a=5)
        assert example.__dict__ == {'b': False, 'a': 5}

        # Not passing in any args should fail.
        with raises(TypeError):
            Example()

        # Passing in arguments of the wrong type should fail validation
        with raises(ValidationError):
            Example('test')

        with raises(ValidationError):
            Example(None)

        with raises(ValidationError):
            Example(True, a=5.5)

        # A more complex Model with multiple args and kwargs
        class SubExample(Model):
            x = Integer()

        def assert_value_between_0_and_20(self, value):
            assert 0 <= value < 20

        class Example(Model):
            a = Integer(validators=[assert_value_between_0_and_20])
            b = Boolean(optional=True, default=False)
            c = ModelField(SubExample, optional=True)
            d = ModelField(SubExample)

        # Just passing in args
        example = Example(5, SubExample(10))
        assert example.__dict__ == {'a': 5, 'b': False, 'c': None, 'd': SubExample(10)}

        # Passing in args and kwargs
        example = Example(5, SubExample(10), c=SubExample(50), b=True)
        assert example.__dict__ == {'a': 5, 'b': True, 'c': SubExample(50), 'd': SubExample(10)}

        # Not passing in all the args should fail.
        with raises(TypeError):
            Example(5)

        # Passing in arguments of the wrong type should fail validation
        with raises(ValidationError):
            Example('test', SubExample(10))

        with raises(ValidationError):
            Example(5, Example(5, SubExample(10)))

        with raises(ValidationError):
            Example(5, SubExample(10), b=5)

        with raises(ValidationError):
            Example(5, SubExample(10), c=Example(5, SubExample(10)))

        with raises(ValidationError):
            Example(30, SubExample(10))

    def test___eq__(self):
        class Example(Model):
            a = Integer()
            b = Boolean(optional=True)

        assert Example(5) != Example(6)
        assert Example(5) != Example(6, b=True)
        assert Example(5) == Example(5)

    def test___hash__(self):
        # A more complex Model with a sub Model
        class SubExample(Model):
            x = Float()

        class Example(Model):
            a = Integer()
            b = ModelField(SubExample)

        assert hash(Example(5, SubExample(10.5))) == hash(Example(5, SubExample(10.5)))
        assert hash(Example(5, SubExample(10.5))) != hash(Example(5, SubExample(10.0)))

    def test_to_dict(self):
        class Example(Model):
            a = Integer()
            b = Boolean(optional=True)

        example = Example(5)
        assert example.to_dict() == {'a': 5}

        example = Example(5, b=False)
        assert example.to_dict() == {'a': 5, 'b': False}

        # A more complex Model with a sub Model
        class SubExample(Model):
            x = Float()

        class Example(Model):
            a = Integer(name='d')
            b = ModelField(SubExample)
            c = Boolean(optional=True)

        example = Example(5, SubExample(10.5))
        assert example.a == 5
        assert example.to_dict() == {'d': 5, 'b': {'x': 10.5}}

        example = Example(5, SubExample(10.5), c=True)
        assert example.to_dict() == {'d': 5, 'b': {'x': 10.5}, 'c': True}

        class Example(Model):
            a = Array(Integer)

        example = Example([1, 2, 3, 4])

        # set a bad value
        example.a = 5

        with raises(SerializationError):
            example.to_dict()

        # Make the field always fail serialization
        def serialize(value):
            raise SerializationError('unable to serialize {}'.format(value))

        example = Example([1, 2, 3, 4])
        Example.__fields__.a.serialize = serialize

        with raises(SerializationError):
            example.to_dict()

    def test_from_dict(self):
        # A simple Model.
        class Example(Model):
            a = Integer()
            b = Boolean(optional=True)

        example = Example(5)
        assert Example.from_dict({'a': 5}) == example

        example = Example(5, b=False)
        assert Example.from_dict({'a': 5, 'b': False}) == example

        with raises(DeserializationError):
            Example.from_dict({'a': 5, 'b': False, 'c': 'extra'})

        # A more complex Model with a sub Model
        class SubExample(Model):
            x = Float()

        class Example(Model):
            a = Integer()
            b = ModelField(SubExample)
            c = Boolean(optional=True)

        example = Example(5, SubExample(10.5))
        assert Example.from_dict({'a': 5, 'b': {'x': 10.5}}) == example

        example = Example(5, SubExample(10.5), c=True)
        assert Example.from_dict({'a': 5, 'b': {'x': 10.5}, 'c': True}) == example

        example = Example.from_dict({'a': 5, 'b': {'x': 10.5}})
        assert isinstance(example.b, SubExample)

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
            a = Integer()
            b = String()

        example = Example(50, 'test')
        assert example.to_json(sort_keys=True) == '{"a": 50, "b": "test"}'

    def test_from_json(self):
        class Example(Model):
            a = Integer()
            b = String()

        assert Example.from_json('{"a": 50, "b": "test"}') == Example(50, 'test')
