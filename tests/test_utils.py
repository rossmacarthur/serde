from pytest import raises

from serde import Model, fields, utils
from serde.exceptions import MissingDependency


def test_dict_partition():
    d = {'a': 1, 'b': 5}
    assert utils.dict_partition(d, lambda k, v: v == 5) == ({'b': 5}, {'a': 1})


def test_is_subclass():
    assert utils.is_subclass(5, int) is False
    assert utils.is_subclass(int, int) is True


def test_subclasses():
    class Example(object):
        pass

    class A(Example):
        pass

    class B(Example):
        pass

    assert utils.subclasses(Example) == [A, B]


def test_try_lookup():
    assert utils.try_lookup('serde.fields.Str') is fields.Str
    assert utils.try_lookup('serde.Model') is Model

    with raises(MissingDependency) as e:
        utils.try_lookup('not_a_real_pkg.not_a_real_module')

    assert e.value.message == (
        "'not_a_real_pkg' is missing, "
        "did you forget to install the 'ext' feature?"
    )


def test_zip_equal():
    x = [1, 2, 3]
    y = [1, 2, 3, 4]

    with raises(ValueError):
        list(utils.zip_equal(x, y))

    with raises(ValueError):
        list(utils.zip_equal(y, x))

    z = [5, 6, 7]
    assert list(utils.zip_equal(x, z)) == [(1, 5), (2, 6), (3, 7)]


def test_zip_until_right():
    x = [1, 2, 3]
    y = [1, 2, 3, 4]

    with raises(ValueError):
        list(utils.zip_until_right(x, y))

    assert list(utils.zip_until_right(y, x)) == [(1, 1), (2, 2), (3, 3)]
