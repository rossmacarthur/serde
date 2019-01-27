from pytest import raises

from serde import validate
from serde.exceptions import ValidationError


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


def test_equal():
    value = object()
    validate.equal(value)(value)

    with raises(ValidationError):
        validate.equal(object())(20)


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


def test_length():
    validate.length(10)(range(10))
    validate.length(3)([1, 2, 3])

    with raises(ValidationError):
        validate.length(10)((1, 2))


def test_length_min():
    validate.length_min(5)(range(10))
    validate.length_min(5, inclusive=False)(range(6))

    with raises(ValidationError):
        validate.length_min(5)(range(2))

    with raises(ValidationError):
        validate.length_min(5, inclusive=False)(range(5))


def test_length_max():
    validate.length_max(5)(range(2))

    with raises(ValidationError):
        validate.length_max(5)(range(10))

    with raises(ValidationError):
        validate.length_max(5, inclusive=False)(range(5))


def test_length_between():
    validate.length_between(0, 10)(range(10))

    with raises(ValidationError):
        validate.length_between(10, 100)(range(5))

    with raises(ValidationError):
        validate.length_between(0, 10, inclusive=False)([])


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
