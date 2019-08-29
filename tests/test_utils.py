import types

from pytest import raises

from serde import utils


def test_chained():
    assert utils.chained([str.strip, str.upper], ' hello ') == 'HELLO'
    assert utils.chained([lambda x: x[::-1], str.lstrip, str.upper], 'hello ') == 'OLLEH'
    assert utils.chained([lambda x: x[::-1], str.rstrip, str.upper], 'hello ') == ' OLLEH'
    assert utils.chained([str.lstrip, str.upper, lambda x: x[::-1]], 'hello ') == ' OLLEH'
    assert utils.chained([str.rstrip, str.upper, lambda x: x[::-1]], 'hello ') == 'OLLEH'


def test_applied():
    def a(d):
        d['a'] = 1

    def b(d):
        d['b'] = 2

    def c(d):
        d['a'] = 2

    d = {}
    utils.applied([a, b], d)
    assert d == {'a': 1, 'b': 2}

    d = {}
    utils.applied([c, a, b], d)
    assert d == {'a': 1, 'b': 2}

    d = {}
    utils.applied([a, b, c], d)
    assert d == {'a': 2, 'b': 2}


def test_dict_partition():
    d = {'a': 1, 'b': 5}
    assert utils.dict_partition(d, lambda k, v: v == 5) == ({'b': 5}, {'a': 1})


def test_subclasses():
    class Example(object):
        pass

    class A(Example):
        pass

    class B(Example):
        pass

    assert utils.subclasses(Example) == [A, B]


def test_try_import():
    # Check that the returned value is a module.
    assert isinstance(utils.try_import('json'), types.ModuleType)

    # Check that the returned value is None.
    assert utils.try_import('not_a_real_package_i_hope') is None


def test_try_import_all():
    ns = {}
    utils.try_import_all('pty', ns)
    assert set(ns.keys()) == {'fork', 'openpty', 'spawn'}


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
