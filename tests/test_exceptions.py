from pytest import raises

from serde import Model, fields, validate
from serde.exceptions import BaseSerdeError, DeserializationError, SerdeError, ValidationError


def test_base_error():
    error = BaseSerdeError('something failed')

    assert repr(error) == '<serde.exceptions.BaseSerdeError: something failed>'
    assert str(error) == 'something failed'


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
        error.add_context(model=3)

        assert error.cause is None
        assert error.value == 1
        assert error.field == 2
        assert error.model == 3

        with raises(AttributeError):
            assert error.not_a_real_attribute_i_hope

    def test__pretty_context_basic(self):
        # Test that a Context object is correctly pretty formatted.
        class Example(Model):
            a = fields.Int()

        context = SerdeError.Context(
            cause=ValidationError('something failed'),
            value='test',
            field=Example._fields.a,
            model=Example
        )

        assert SerdeError._pretty_context(context, separator='; ', prefix=':: ', indent=0) == (
            ":: value 'test' for field 'a' of type 'Int' on model 'Example'; "
            ':: ValidationError: something failed'
        )

    def test__pretty_context_generic_exception(self):
        # Test that cause can also work with a generic exception.
        context = SerdeError.Context(cause=ValueError(), value=None, field=None, model=None)
        assert SerdeError._pretty_context(context) == '    Due to => ValueError()'

    def test__pretty_context_long_value(self):
        # Test that a Context object is correctly pretty formatted.
        context = SerdeError.Context(cause=None, value='a' * 40, field=None, model=None)
        expected = "    Due to => value 'aaaaaaaaaaaaaaaaaaaaaaaaa..."
        assert SerdeError._pretty_context(context) == expected

    def test_pretty_use_case_nested(self):
        # Test a better use case for the pretty formatted error.

        class SubExample(Model):
            a = fields.Str(validators=[validate.length_between(0, 5)])

        class Example(Model):
            sub = fields.Nested(SubExample)

        try:
            Example.from_dict({
                'sub': {
                    'a': 'testing'
                }
            })
            assert False
        except DeserializationError as e:
            assert e.pretty() == (
                'DeserializationError: expected at most 5 but got 7\n'
                "    Due to => value {'a': 'testing'} for field 'sub' of type 'Nested' on model 'Example'\n"  # noqa: E501
                '    Due to => ValidationError: expected at most 5 but got 7\n'
                "    Due to => value 'testing' for field 'a' of type 'Str' on model 'SubExample'"
            )

    def test_pretty_use_case_missing_keys(self):
        # Test another use case where dictionary keys are missing.

        class Example(Model):
            a = fields.Int()

        try:
            Example.from_dict({})
            assert False
        except DeserializationError as e:
            assert e.pretty() == (
                'DeserializationError: Int value is not allowed to be None\n'
                '    Due to => ValidationError: Int value is not allowed to be None\n'
                "    Due to => for field 'a' of type 'Int' on model 'Example'"
            )

    def test_pretty_use_case_extra_keys(self):
        # Test another use case where there are extra dictionary keys.

        class SubExample(Model):
            pass

        class Example(Model):
            sub = fields.Nested(SubExample)

        try:
            Example.from_dict({
                'sub': {
                    'a': 5
                }
            })
            assert False
        except DeserializationError as e:
            assert e.pretty() == (
                "DeserializationError: unexpected dictionary key 'a'\n"
                "    Due to => value {'a': 5} for field 'sub' of type 'Nested' on model 'Example'"
            )

    def test_pretty_use_case_extra_keys_flat(self):
        # Test another use case where there are extra dictionary keys.

        class Example(Model):
            a = fields.Int()

        try:
            Example.from_dict({'a': 5, 'b': 'test'})
            assert False
        except DeserializationError as e:
            assert e.pretty() == "DeserializationError: unexpected dictionary key 'b'"
