from pytest import raises

from serde.exceptions import ValidationError
from serde.validators import (
    Between,
    Length,
    LengthBetween,
    LengthMax,
    LengthMin,
    Max,
    Min,
    Validator,
)


def test_validator():
    with raises(NotImplementedError):
        Validator()(None)

    assert Validator() == Validator()


def test_min():
    Min(100)(100)
    Min(100)(1000)

    with raises(ValidationError):
        Min(100)(50)

    with raises(ValidationError):
        Min(100, inclusive=False)(100)


def test_max():
    Max(100)(100)
    Max(100)(50)

    with raises(ValidationError):
        Max(100)(101)

    with raises(ValidationError):
        Max(100, inclusive=False)(100)


def test_between():
    Between(-100, 100)(-50)
    Between(-100, 100)(50)

    with raises(ValidationError):
        Between(-100, 100)(150)

    with raises(ValidationError):
        Between(-100, 100, inclusive=False)(100)


def test_length():
    Length(10)(range(10))
    Length(3)([1, 2, 3])

    with raises(ValidationError):
        Length(10)((1, 2))


def test_length_min():
    LengthMin(5)(range(10))
    LengthMin(5, inclusive=False)(range(6))

    with raises(ValidationError):
        LengthMin(5)(range(2))

    with raises(ValidationError):
        LengthMin(5, inclusive=False)(range(5))


def test_length_max():
    LengthMax(5)(range(2))

    with raises(ValidationError):
        LengthMax(5)(range(10))

    with raises(ValidationError):
        LengthMax(5, inclusive=False)(range(5))


def test_length_between():
    LengthBetween(0, 10)(range(10))

    with raises(ValidationError):
        LengthBetween(10, 100)(range(5))

    with raises(ValidationError):
        LengthBetween(0, 10, inclusive=False)([])
