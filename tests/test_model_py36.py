from pytest import raises

from serde import Model, exceptions, fields


class TestModel:
    def test___new___annotations_basic(self):
        # Check that basic annotations can be used.

        class Example(Model):
            a: fields.Int()
            b: fields.Bool()

        # The field attributes should not be present on the final class.
        assert not hasattr(Example, 'a')
        assert not hasattr(Example, 'b')

        # But they should be in the `__fields__` attribute
        assert Example.__fields__.a == fields.Int()
        assert Example.__fields__.b == fields.Bool()

    def test___new___annotations_resolved(self):
        # Check that annotations that require resolving can be used.

        class NestedExample(Model):
            a = fields.Int()

        class Example(Model):
            a: int
            nested: NestedExample

        # The field attributes should not be present on the final class.
        assert not hasattr(Example, 'a')
        assert not hasattr(Example, 'nested')

        # But they should be in the `__fields__` attribute
        assert Example.__fields__.a == fields.Int()
        assert Example.__fields__.nested == fields.Nested(NestedExample)

    def test___new___both_annotations_and_attributes(self):
        # Check that you cannot use both annotations and class attributes.

        with raises(exceptions.ContextError):

            class Example(Model):
                a: int
                b = fields.Bool()
