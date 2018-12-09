from serde.error import SerdeError


def test_error():
    e = SerdeError('something failed')

    assert repr(e) == '<serde.error.SerdeError: something failed>'
    assert str(e) == 'something failed'


def test_error_context():
    e = SerdeError('something failed')
    cause = ValueError()

    e.add_context(cause=cause)
    assert e.cause == cause
