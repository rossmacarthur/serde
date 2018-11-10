"""
Utility functions for Serde.
"""

import hashlib
import importlib
import inspect
import linecache
import re
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

    Yields:
        Any: each zipped element.

    Raises:
        ValueError: if one of the iterables is the wrong length.
    """
    sentinel = object()

    for element in zip_longest(*iterables, fillvalue=sentinel):
        if sentinel in element:
            raise ValueError('iterables have different lengths')

        yield element


def create_function(definition, lines):
    """
    Dynamically create a Python function from the given code.

    Args:
        definition (str): the function definition.
        lines (list): a list of lines of code. These lines must include the
            indentation.

    Raises:
        ValueError: if no name could be determined from the function definition.

    Returns:
        Callable: the resulting function.
    """
    # Determine the function filename.
    match = re.match(r'def\s+(?P<name>\w+)\s*\(', definition)
    if not match:
        raise ValueError('unable to determine function name from definition')

    name = match.groupdict()['name']
    sha1 = hashlib.sha1()
    sha1.update(definition.encode('utf-8'))
    filename = '<serde {name} {sha1}>'.format(name=name, sha1=sha1.hexdigest())

    # Compile the definition and lines of code to bytecode.
    lines = [definition] + lines
    code = '\n'.join(lines)
    bytecode = compile(code, filename, 'exec')

    # Actually run the code, this will create the function.
    locals_ = {}
    eval(bytecode, {}, locals_)

    # Add the code to the linecache (code will show in tracebacks).
    linecache.cache[filename] = (len(code), None, lines, filename)

    return locals_[name]


def list_class_init_parameters(cls):
    """
    Return the names of a class's __init__ parameters.

    Args:
        cls (class): the class to inspect.

    Returns:
        list: a list of parameter names.
    """
    parameters = []

    for base in inspect.getmro(cls):
        parameters.extend([
            name for name, param in inspect.signature(base).parameters.items()
            if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD and name not in parameters
        ])

    return parameters
