"""
Utility functions.
"""

import importlib
from itertools import zip_longest


def try_import(name, package=None):
    """
    Try import the given library, ignoring ImportErrors.

    Args:
        name (str): the name to import.
        package (str): the package this module belongs to.

    Returns:
        module: the imported module or None.
    """
    try:
        return importlib.import_module(name, package=package)
    except ImportError:
        pass


def zip_equal(*iterables):
    """
    A zip function that validates that all the iterables have the same length.

    Args:
        *iterables: the iterables to pass to `zip_longest`.

    Yields:
        each zipped element.

    Raises:
        ValueError: if one of the iterables is the wrong length.
    """
    sentinel = object()

    for element in zip_longest(*iterables, fillvalue=sentinel):
        if sentinel in element:
            raise ValueError('iterables have different lengths')

        yield element


def zip_until_right(*iterables):
    """
    A zip function that validates that the right iterable is consumed.

    Args:
        *iterables: the iterables to pass to `zip`.

    Yields:
        each zipped element.

    Raises:
        ValueError: if the left iterable is consumed before the right.
    """
    lefts = iterables[:-1]
    right = iter(iterables[-1])
    iterables = lefts + (right,)

    yield from zip(*iterables)

    try:
        next(right)
        raise ValueError('the rightmost iterable was not consumed')
    except StopIteration:
        pass
