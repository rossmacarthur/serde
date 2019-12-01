import sys

import mock
import six

from serde import fields


def py2_patch_str_with_basestring(f):
    def decorated_function(*args, **kwargs):
        if six.PY2:
            with mock.patch.dict(
                'serde.fields.FIELD_CLASS_MAP', {str: fields.BaseString}
            ):
                return f(*args, **kwargs)
        return f(*args, **kwargs)

    return decorated_function


def py3(f):
    def decorated_function(*args, **kwargs):
        if six.PY2:
            return
        return f(*args, **kwargs)

    return decorated_function


def py36(f):
    def decorated_function(*args, **kwargs):
        if sys.version_info[:2] < (3, 6):
            return
        return f(*args, **kwargs)

    return decorated_function
