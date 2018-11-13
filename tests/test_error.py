from serde import SerdeError


def test_error():
    e = SerdeError('something failed')

    assert repr(e) == '<serde.error.SerdeError: something failed>'
