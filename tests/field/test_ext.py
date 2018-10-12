import uuid

from pytest import raises

from serde.error import ValidationError
from serde.field import Choice, Domain, Email, Slug, Url, Uuid


class TestChoice:

    def test___init__(self):
        field = Choice(range(5), required=False, validators=[])
        assert field.choices == range(5)

    def test_validate(self):
        field = Choice(range(5))

        field.validate(0)
        field.validate(4)

        with raises(ValidationError):
            field.validate('test')


class TestDomain:

    def test_validate(self):
        field = Domain()

        field.validate('www.google.com')

        with raises(ValidationError):
            field.validate('hello')


class TestEmail:

    def test_validate(self):
        field = Email()

        field.validate('someone@website.com')

        with raises(ValidationError):
            field.validate('derp')


class TestSlug:

    def test_validate(self):
        field = Slug()

        field.validate('a_b-10')

        with raises(ValidationError):
            field.validate('a!')


class TestUrl:

    def test_validate(self):
        field = Url()

        field.validate('http://www.google.com/search?q=test')

        with raises(ValidationError):
            field.validate('derp')


class TestUuid:

    def test___init__(self):
        field = Uuid(required=False, default=uuid.UUID('2d7026c8-cc58-11e8-bd7a-784f4386978e'))

        assert field.required is False
        assert field.default == uuid.UUID('2d7026c8-cc58-11e8-bd7a-784f4386978e')

    def test_serialize(self):
        field = Uuid()

        assert field.serialize(uuid.UUID('2d7026c8-cc58-11e8-bd7a-784f4386978e')) == \
            '2d7026c8-cc58-11e8-bd7a-784f4386978e'

    def test_deserialize(self):
        field = Uuid()

        assert field.deserialize('2d7026c8-cc58-11e8-bd7a-784f4386978e') == \
            uuid.UUID('2d7026c8-cc58-11e8-bd7a-784f4386978e')

    def test_validate(self):
        field = Uuid()

        field.validate(uuid.UUID('2d7026c8-cc58-11e8-bd7a-784f4386978e'))

        with raises(ValidationError):
            field.validate('2d7026c8-cc58-11e8-bd7a-784f4386978e')
