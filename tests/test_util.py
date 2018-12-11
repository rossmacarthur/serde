import types

from pytest import raises

from serde import util


def test_dict_partition():
    d = {'a': 1, 'b': 5}
    assert util.dict_partition(d, lambda k, v: v == 5) == ({'b': 5}, {'a': 1})


def test_try_import():
    # Check that the returned value is a module.
    assert isinstance(util.try_import('toml'), types.ModuleType)

    # Check that the returned value is None.
    assert util.try_import('not_a_real_package_i_hope') is None


def test_zip_equal():
    x = [1, 2, 3]
    y = [1, 2, 3, 4]

    with raises(ValueError):
        list(util.zip_equal(x, y))

    with raises(ValueError):
        list(util.zip_equal(y, x))

    z = [5, 6, 7]
    assert list(util.zip_equal(x, z)) == [(1, 5), (2, 6), (3, 7)]


def test_zip_until_right():
    x = [1, 2, 3]
    y = [1, 2, 3, 4]

    with raises(ValueError):
        list(util.zip_until_right(x, y))

    assert list(util.zip_until_right(y, x)) == [(1, 1), (2, 2), (3, 3)]
