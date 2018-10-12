from serde.error import SerdeError


def test_error():
    e = SerdeError('something failed')

    assert repr(e) == '<serde.error.SerdeError: something failed>'
