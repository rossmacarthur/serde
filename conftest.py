"""
Pytest extra test fixtures.
"""

import pytest

import serde


@pytest.fixture(autouse=True)
def add_all(doctest_namespace):
    """
    Add serde.__all__ to all doctests.
    """
    for name in serde.__all__:
        doctest_namespace[name] = getattr(serde, name)
