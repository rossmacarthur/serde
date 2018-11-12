import types

from pytest import raises

from serde.util import try_import, zip_equal


def test_try_import():
    # Check that the returned value is a module.
    assert isinstance(try_import('toml'), types.ModuleType)

    # Check that the returned value is None.
    assert try_import('not_a_real_package_i_hope') is None


def test_zip_equal():
    x = [1, 2, 3]
    y = [1, 2, 3, 4]

    with raises(ValueError):
        list(zip_equal(x, y))

    with raises(ValueError):
        list(zip_equal(y, x))

    z = [5, 6, 7]
    assert list(zip_equal(x, z)) == [(1, 5), (2, 6), (3, 7)]
