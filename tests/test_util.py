import traceback

from pytest import raises

from serde.util import create_function, zip_equal


def test_zip_equal():
    x = [1, 2, 3]
    y = [1, 2, 3, 4]

    with raises(ValueError):
        list(zip_equal(x, y))

    with raises(ValueError):
        list(zip_equal(y, x))

    z = [5, 6, 7]
    assert list(zip_equal(x, z)) == [(1, 5), (2, 6), (3, 7)]


def test_create_function():
    # A simple function that returns the sum of numbers arguments.
    definition = 'def summer(*args):'
    lines = ['    return sum(args)']
    func = create_function(definition, lines)
    assert func(*range(1, 5)) == 10

    # A function with bad definition
    definition = 'def(a):'
    lines = ['    return a']
    with raises(ValueError):
        create_function(definition, lines)

    # A function that raises an Exception, should have the code in the traceback
    definition = 'def raiser():'
    lines = ['    raise NotImplementedError()']
    func = create_function(definition, lines)

    try:
        func()
        assert False, 'func() did not raise NotImplementedError'
    except NotImplementedError:
        tb = """
  File "<serde raiser 4451c84efb0b2c237bba61aedd92044a0ec2d747>", line 2, in raiser
    raise NotImplementedError()
NotImplementedError
"""
        assert tb in traceback.format_exc()
