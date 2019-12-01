"""
This module defines some utility functions.
"""

import importlib
from collections import OrderedDict

from six.moves import zip_longest

from serde.exceptions import MissingDependency


def dict_partition(d, keyfunc, dict=OrderedDict):
    """
    Partition a dictionary.

    Args:
        d (dict): the dictionary to operate on.
        keyfunc (function): the function to partition with. It must accept the
            dictionary key and value as arguments, and should return a boolean.
        dict (type): the type of dictionaries to return.

    Return:
        (dict, dict): all of the elements for which the key function returned
            True, and all of the elements for which it returned False.
    """
    left = dict()
    right = dict()

    for key, value in d.items():
        if keyfunc(key, value):
            left[key] = value
        else:
            right[key] = value

    return left, right


def is_subclass(cls, class_or_tuple):
    """
    Return whether 'cls' is a derived from another class or is the same class.

    Does not raise `TypeError` if the given `cls` is not a class.
    """
    try:
        return issubclass(cls, class_or_tuple)
    except TypeError:
        return False


def subclasses(cls):
    """
    Returns the recursed subclasses.

    Args:
        cls (class): the class whose subclasses we should recurse.

    Returns:
        list: the subclasses.
    """
    subs = cls.__subclasses__()
    variants = []

    for sub in subs:
        variants.extend(subclasses(sub))

    return subs + variants


def try_lookup(name):
    """
    Try lookup a fully qualified Python path, importing the module if necessary.

    Args:
        name (str): the fully qualifed Python path. Example: 'validators.email'.

    Returns:
        the object at the path.

    Raises:
        serde.exceptions.MissingDepenency: if the path could not be imported.
    """
    module, path = name.split('.', 1)

    try:
        obj = importlib.import_module(module)
    except ImportError:
        raise MissingDependency(
            "{!r} is missing, did you forget to install the 'ext' feature?".format(
                module
            )
        )

    for attr in path.split('.'):
        obj = getattr(obj, attr)

    return obj


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

    for item in zip(*iterables):
        yield item

    try:
        next(right)
        raise ValueError('the rightmost iterable was not consumed')
    except StopIteration:
        pass
