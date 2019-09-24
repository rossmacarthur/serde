import sys


def pytest_ignore_collect(path, config):
    return sys.version_info[:2] < (3, 6) and path.basename.endswith('_py36.py')
