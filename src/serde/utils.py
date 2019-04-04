"""
This module defines some utility functions.
"""

import importlib
from collections import OrderedDict

from six.moves import zip_longest


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


def try_import_all(name, namespace):
    """
    Try import the names from the given library, ignoring ImportErrors.

    Args:
        name (str): the name to import.
        namespace (dict): the namespace to update.
    """
    module = try_import(name)

    if module:
        if hasattr(module, '__all__'):
            all_names = module.__all__
        else:
            all_names = (name for name in dir(module) if not name.startswith('_'))

        namespace.update({name: getattr(module, name) for name in all_names})


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
