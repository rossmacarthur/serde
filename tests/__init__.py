import mock
import six

from serde import fields


def py2_patch_str_with_basestring(f):
    def decorated_function(*args, **kwargs):
        if six.PY2:
            with mock.patch.dict('serde.fields.BUILTIN_FIELD_CLASSES', {str: fields.BaseString}):
                return f(*args, **kwargs)
        return f(*args, **kwargs)

    return decorated_function


def py3_only(f):
    def decorated_function(*args, **kwargs):
        if six.PY2:
            return
        return f(*args, **kwargs)

    return decorated_function


def py2_only(f):
    def decorated_function(*args, **kwargs):
        if six.PY3:
            return
        return f(*args, **kwargs)

    return decorated_function
