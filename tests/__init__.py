import mock
import six

from serde import field


def handle_six_strings(f):
    def decorated_function(*args, **kwargs):
        if six.PY2:
            with mock.patch('serde.field.Str', field.BaseString):
                return f(*args, **kwargs)
        else:
            return f(*args, **kwargs)

    return decorated_function
