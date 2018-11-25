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
