from serde.exceptions import BaseSerdeError, SerdeError


def test_base_error():
    e = BaseSerdeError('something failed')

    assert repr(e) == '<serde.exceptions.BaseSerdeError: something failed>'
    assert str(e) == 'something failed'


def test_error_context():
    e = SerdeError('something failed')
    cause = ValueError()

    e.add_context(cause=cause)
    assert e.cause == cause
