from pytest import raises

from serde import validate
from serde.error import ValidationError


def test_instance():
    validate.instance(bool)(True)
    validate.instance(bool)(False)
    validate.instance(int)(1000)
    validate.instance(float)(1000.0)

    with raises(ValidationError):
        validate.instance(bool)(100)

    with raises(ValidationError):
        validate.instance(int)(100.0)

    with raises(ValidationError):
        validate.instance(float)(1)


def test_min():
    validate.min(100)(100)
    validate.min(100)(1000)

    with raises(ValidationError):
        validate.min(100)(50)

    with raises(ValidationError):
        validate.min(100, inclusive=False)(100)


def test_max():
    validate.max(100)(100)
    validate.max(100)(50)

    with raises(ValidationError):
        validate.max(100)(101)

    with raises(ValidationError):
        validate.max(100, inclusive=False)(100)


def test_between():
    validate.between(-100, 100)(-50)
    validate.between(-100, 100)(50)

    with raises(ValidationError):
        validate.between(-100, 100)(150)

    with raises(ValidationError):
        validate.between(-100, 100, inclusive=False)(100)


def test_contains():
    validate.contains(range(5))(3)
    validate.contains((0, 1, 2, 3, 4))(3)
    validate.contains([0, 1, 2, 3, 4])(3)

    with raises(ValidationError):
        validate.contains(range(5))(-1)

    with raises(ValidationError):
        validate.contains((0, 1, 2, 3, 4))(-1)

    with raises(ValidationError):
        validate.contains([0, 1, 2, 3, 4])(-1)


def test_domain():
    validate.domain('www.google.com')

    with raises(ValidationError):
        validate.domain('hello')


def test_email():
    validate.email('someone@website.com')

    with raises(ValidationError):
        validate.email('someone@com')


def test_ip_address():
    validate.ip_address('10.0.0.1')
    validate.ip_address('2001:db8:85a3:0:0:8a2e:370:7334')

    with raises(ValidationError):
        validate.ip_address('10.0.0.256')


def test_ipv4_address():
    validate.ipv4_address('10.0.0.1')

    with raises(ValidationError):
        validate.ipv4_address('10.0.0.256')


def test_ipv6_address():
    validate.ipv6_address('2001:db8:85a3:0:0:8a2e:370:7334')

    with raises(ValidationError):
        validate.ipv6_address('2001:db8:85a3:0:0:8a2e:370:73345')


def test_mac_address():
    validate.mac_address('3a:00:40:82:ad:00')

    with raises(ValidationError):
        validate.mac_address('3a:00:40:82:a:00')


def test_slug():
    validate.slug('a_b-10')

    with raises(ValidationError):
        validate.slug('a!')


def test_url():
    validate.url('http://www.google.com/search?q=test')

    with raises(ValidationError):
        validate.url('derp')
