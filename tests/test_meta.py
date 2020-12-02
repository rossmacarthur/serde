import doctest
import os
from itertools import groupby

from serde import fields
from tests import REPO_DIR


def test_readme():
    failures, _ = doctest.testfile('../README.rst')

    if failures:
        raise Exception('doctests in README.rst failed')


def test_dev_requirements_sorted():
    """
    Check that dev-requirements.in is sorted (within sections).
    """
    with open(os.path.join(REPO_DIR, 'dev-requirements.in'), 'r') as f:
        lines = f.readlines()

    def is_comment_or_empty(line):
        return not line.strip() or line.lstrip().startswith('#')

    for _, group in groupby(lines, key=is_comment_or_empty):
        grouped = list(group)
        assert grouped == sorted(grouped)


def test_module___all__s():
    """
    Check that there is nothing bad in any module __all__ by importing *.
    """

    def module_from_path(p):
        p = p[: -len('/__init__')] if p.endswith('__init__') else p
        return p.replace('/', '.')

    src_dir = os.path.join(REPO_DIR, 'src')
    filenames = [
        os.path.splitext(os.path.relpath(os.path.join(dirpath, filename), src_dir))[0]
        for dirpath, dirnames, filenames in os.walk(src_dir)
        for filename in filenames
        if filename.endswith('.py')
    ]
    for module in [module_from_path(f) for f in filenames]:
        exec(f'from {module} import *', {}, {})  # noqa: E211


def test_field_class_map():
    """
    Check that all Instance type fields are in the FIELD_CLASS_MAP.
    """
    for name in fields.__all__:
        field_cls = getattr(fields, name)
        if fields.is_subclass(field_cls, fields.Instance):
            try:
                ty = field_cls().ty
            except TypeError:
                pass
            else:
                msg = f'{ty.__name__!r} not in FIELD_CLASS_MAP'
                assert ty in fields._FIELD_CLASS_MAP, msg
