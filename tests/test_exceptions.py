from pytest import raises

from serde import Model, fields, tags, validate
from serde.exceptions import BaseError, Context, DeserializationError, SerdeError, ValidationError


class TestBaseError:
    def test___init__(self):
        assert BaseError('testing...').args == ('testing...',)

    def test_message(self):
        assert BaseError('testing...').message == 'testing...'

    def test___repr__(self):
        assert repr(BaseError('testing...')) == '<serde.exceptions.BaseError: testing...>'

    def test___str__(self):
        assert str(BaseError('testing...')) == 'testing...'


class TestContext:

    def test_pretty_basic(self):
        # Test that a Context object is correctly pretty formatted.
        class Example(Model):
            a = fields.Int()

        context = Context(
            cause=ValidationError('something failed'),
            value='test',
            field=Example.__fields__.a,
            model_cls=Example
        )

        assert context.pretty(separator='; ', prefix=':: ', indent=0) == (
            ":: value 'test' for field 'a' of type 'Int' on model 'Example'; "
            ':: ValidationError: something failed'
        )

    def test_pretty_tag(self):
        # Test that a Context object behaves correctl with a Tag.
        class Example(Model):
            class Meta:
                tag = tags.Internal(tag='kind')

            a = fields.Int()

        context = Context(
            cause=ValidationError('something failed'),
            value='test',
            field=Example.__tag__,
            model_cls=Example
        )

        assert context.pretty(separator=';', prefix='> ', indent=0) == (
            "> value 'test' for tag 'Internal' on model 'Example';"
            '> ValidationError: something failed'
        )

    def test_pretty_generic_exception(self):
        # Test that cause can also work with a generic exception.
        context = Context(cause=ValueError(), value=None, field=None, model_cls=None)
        assert context.pretty() == '    Due to => ValueError()'

    def test_pretty_context_long_value(self):
        # Test that a Context object is correctly pretty formatted.
        context = Context(cause=None, value='a' * 40, field=None, model_cls=None)
        assert context.pretty() == "    Due to => value 'aaaaaaaaaaaaaaaaaaaaaaaaa... "


class TestSerdeError:

    def test___init___basic(self):
        # You should be able to construct SerdeError without any context.
        error = SerdeError('something failed')
        assert error.message == 'something failed'
        assert error.contexts == []

    def test___init___context(self):
        # You should be able to construct a SerdeError with some context.
        cause = ValueError()
        error = SerdeError('something failed', cause=cause, value=5)
        assert error.message == 'something failed'
        assert error.contexts[0].cause == cause
        assert error.contexts[0].value == 5
        assert error.cause == cause
        assert error.value == 5

    def test_add_context(self):
        # You should be able to add more contexts.
        error = SerdeError('something failed')
        error.add_context(cause=ValueError())
        error.add_context(cause=TypeError())
        assert isinstance(error.contexts[0].cause, ValueError)
        assert isinstance(error.contexts[1].cause, TypeError)

    def test_iter_contexts(self):
        # You should be able to iterate through the contexts.
        error = SerdeError('something failed')
        error.contexts = ['a', 'b', 'c']
        assert list(error.iter_contexts()) == error.contexts[::-1]

    def test_from_exception_generic(self):
        # You should be able to convert any exception into a SerdeError.
        exception = ValueError('something failed')
        error = SerdeError.from_exception(exception)
        assert error.message == 'something failed'
        assert error.contexts[0].cause == exception

    def test_from_exception_serde_error(self):
        # You be able to convert any SerdeError error into another SerdeError.
        exception = ValidationError('it is invalid')
        error = DeserializationError.from_exception(exception)
        assert error.message == 'it is invalid'
        assert error.contexts[0].cause == exception
        assert error.contexts[0].cause.contexts == []

    def test___getattr__valid(self):
        # Test that cause, value, field, and model attributes are accessible.
        error = SerdeError('something failed', value=1)
        error.add_context(field=2)
        error.add_context(model_cls=3)

        assert error.cause is None
        assert error.value == 1
        assert error.field == 2
        assert error.model_cls == 3

        with raises(AttributeError):
            assert error.not_a_real_attribute_i_hope

    def test_pretty_use_case_nested(self):
        # Test a better use case for the pretty formatted error.

        class SubExample(Model):
            a = fields.Str(validators=[validate.length_between(0, 5)])

        class Example(Model):
            sub = fields.Nested(SubExample)

        with raises(DeserializationError) as e:
            Example.from_dict({'sub': {'a': 'testing'}})

        assert e.value.pretty() == (
            'DeserializationError: expected at most 5 but got 7\n'
            "    Due to => value {'a': 'testing'} for field 'sub' of type 'Nested' on model 'Example'\n"  # noqa: E501
            '    Due to => ValidationError: expected at most 5 but got 7\n'
            "    Due to => value 'testing' for field 'a' of type 'Str' on model 'SubExample'"
        )

    def test_pretty_use_case_missing_keys(self):
        # Test another use case where dictionary keys are missing.

        class Example(Model):
            a = fields.Int()

        with raises(DeserializationError) as e:
            Example.from_dict({})

        assert e.value.pretty() == (
            "DeserializationError: expected field 'a'\n"
            "    Due to => field 'a' of type 'Int' on model 'Example'"
        )

    def test_pretty_use_case_extra_keys(self):
        class SubExample(Model):
            a = fields.Str()

        class Example(Model):
            sub = fields.Nested(SubExample)

        with raises(DeserializationError) as e:
            Example.from_dict({'sub': {'a': 5}})

        assert e.value.pretty() == (
            "DeserializationError: expected 'str' but got 'int'\n"
            "    Due to => value {'a': 5} for field 'sub' of type 'Nested' on model 'Example'\n"
            "    Due to => ValidationError: expected 'str' but got 'int'\n"
            "    Due to => value 5 for field 'a' of type 'Str' on model 'SubExample'"
        )
