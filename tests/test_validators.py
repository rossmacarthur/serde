import re

from pytest import raises

from serde.exceptions import ValidationError
from serde.validators import (
    Between,
    Contains,
    Equal,
    Instance,
    Length,
    LengthBetween,
    LengthMax,
    LengthMin,
    Max,
    Min,
    Regex,
    Validator
)


def test_validator():
    with raises(NotImplementedError):
        Validator()(None)


def test_instance():
    Instance(bool)(True)
    Instance(bool)(False)
    Instance(int)(1000)
    Instance(float)(1000.0)

    with raises(ValidationError):
        Instance(bool)(100)

    with raises(ValidationError):
        Instance(int)(100.0)

    with raises(ValidationError):
        Instance(float)(1)


def test_equal():
    value = object()
    Equal(value)(value)

    with raises(ValidationError):
        Equal(object())(20)


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


def test_contains():
    Contains(range(5))(3)
    Contains((0, 1, 2, 3, 4))(3)
    Contains([0, 1, 2, 3, 4])(3)

    with raises(ValidationError):
        Contains(range(5))(-1)

    with raises(ValidationError):
        Contains((0, 1, 2, 3, 4))(-1)

    with raises(ValidationError):
        Contains([0, 1, 2, 3, 4])(-1)


def test_regex():
    Regex(r'[A-Z]+')('TEST')

    Regex(r'TE.ST', re.DOTALL)('TE\nST')

    with raises(ValidationError):
        Regex(r'TE.ST')('TE\nST')

    with raises(ValidationError):
        Regex(r'[A-Z]+')('test')

    with raises(ValidationError):
        Regex(r'test')('a sentence with test inside')
