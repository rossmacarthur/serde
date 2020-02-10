import pytest

from serde import fields
from serde.exceptions import SerdeError, ValidationError, add_context


class TestSerdeError:
    def test___repr__(self):
        assert (
            repr(SerdeError('testing...'))
            == '<serde.exceptions.SerdeError: testing...>'
        )


class TestValidationError:
    def test___init___basic(self):
        # You should be able to construct ValidationError without any value.
        error = ValidationError('something failed')
        assert error.args == ('something failed',)
        assert error.value is None
        assert error._fields == []

    def test___init___value(self):
        # You should be able to construct a ValidationError with a value.
        error = ValidationError('something failed', value=5)
        assert error.args == ('something failed',)
        assert error.value == 5
        assert error._fields == []

    def test_messages(self):
        error = ValidationError('something failed')
        f1 = fields.Field()
        f2 = fields.Field(rename='f-two')
        f3 = fields.Field()
        f1._bind(object(), 'f1')
        f2._bind(object(), 'f2')
        f3._bind(object(), 'f3')
        error._fields.append(f3)
        error._fields.append(f2)
        error._fields.append(f1)

        assert error.messages() == {'f1': {'f-two': {'f3': 'something failed'}}}


def test_add_context():
    field = object()
    with pytest.raises(ValidationError) as e:
        with add_context(field):
            raise ValidationError('something failed')
    assert e.value._fields == [field]
