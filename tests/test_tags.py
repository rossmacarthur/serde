import mock
import six
from pytest import raises

from serde import Model
from serde.exceptions import DeserializationError
from serde.tags import Adjacent, External, Internal, Tag


class TestTag:
    def test___init___basic(self):
        tag = Tag()
        assert tag.recurse is False
        assert tag.serializers == []
        assert tag.deserializers == []

    def test___init___options(self):
        tag = Tag(recurse=True, serializers=[None], deserializers=[1, 2, 3])
        assert tag.recurse is True
        assert tag.serializers == [None]
        assert tag.deserializers == [1, 2, 3]

    def test_variants_none(self):
        class Example(Model):
            pass

        tag = Tag()
        tag._bind(Example)
        assert tag.variants() == [Example]

    def test_variants_basic(self):
        class Example(Model):
            pass

        class Example2(Example):
            pass

        class Example3(Example2):
            pass

        tag = Tag()
        tag._bind(Example)
        assert tag.variants() == [Example, Example2]

    def test_variants_recurse(self):
        class Example(Model):
            pass

        class Example2(Example):
            pass

        class Example3(Example):
            pass

        tag = Tag(recurse=True)
        tag._bind(Example)
        assert tag.variants() == [Example, Example2, Example3]

    def test_variants_abstract(self):
        class Example(Model):
            class Meta:
                abstract = True

        class Example2(Example):
            pass

        tag = Tag(recurse=True)
        tag._bind(Example)
        assert tag.variants() == [Example2]

    def test_lookup_tag(self):
        class Example(Model):
            pass

        if six.PY2:
            prefix = 'tests.test_tags'
        else:
            prefix = 'tests.test_tags.TestTag.test_lookup_tag.<locals>'
        assert Tag().lookup_tag(Example) == prefix + '.Example'

    def test_lookup_variant(self):
        class Example(Model):
            pass

        class Example2(Example):
            pass

        class Example3(Example):
            pass

        tag = Tag(recurse=True)
        tag._bind(Example)
        if six.PY2:
            prefix = 'tests.test_tags'
        else:
            prefix = 'tests.test_tags.TestTag.test_lookup_variant.<locals>'
        assert tag.lookup_variant(prefix + '.Example') is Example
        assert tag.lookup_variant(prefix + '.Example2') is Example2
        assert tag.lookup_variant(prefix + '.Example3') is Example3
        assert tag.lookup_variant(prefix + '.Example4') is None

    def test_serialize(self):
        class Example(Model):
            pass

        if six.PY2:
            prefix = 'tests.test_tags'
        else:
            prefix = 'tests.test_tags.TestTag.test_serialize.<locals>'
        assert Tag().serialize(Example) == prefix + '.Example'

    def test_deserialize(self):
        class Example(Model):
            pass

        class Example2(Example):
            pass

        class Example3(Example):
            pass

        tag = Tag(recurse=True)
        tag._bind(Example)
        if six.PY2:
            prefix = 'tests.test_tags'
        else:
            prefix = 'tests.test_tags.TestTag.test_deserialize.<locals>'
        assert tag.deserialize(prefix + '.Example') is Example
        assert tag.deserialize(prefix + '.Example2') is Example2
        assert tag.deserialize(prefix + '.Example3') is Example3

        tag_value = prefix + '.Example4'
        with raises(DeserializationError) as e:
            tag.deserialize(tag_value)

        assert (
            e.value.pretty()
            == """\
DeserializationError: no variant found for tag '{}'
    Due to => value {} for tag 'Tag' on model 'Example'""".format(
                tag_value,
                "'tests.test_tags.Example4'"
                if six.PY2
                else "'tests.test_tags.TestTag.t... ",
            )
        )


@mock.patch('serde.tags.Tag.lookup_tag', lambda _, variant: variant.__name__)
class TestExternal:
    def test__serialize_with(self):
        class Example(Model):
            pass

        tag = External()
        tag._bind(Example)
        d = {'something': 1}
        assert tag._serialize_with(Example(), d) == {'Example': d}

    def test__deserialize_with(self):
        class Example(Model):
            pass

        class Example2(Example):
            pass

        tag = External()
        tag._bind(Example)

        model = Example()
        d = {}
        result = tag._deserialize_with(model, {'Example2': d})
        assert result[0] is model
        assert result[0].__class__ is Example2
        assert result[1] is d

    def test__deserialize_with_untagged(self):
        with raises(DeserializationError) as e:
            External()._deserialize_with(object(), {})
        assert (
            e.value.pretty()
            == """\
DeserializationError: expected externally tagged data
    Due to => tag 'External'"""
        )


@mock.patch('serde.tags.Tag.lookup_tag', lambda _, variant: variant.__name__)
class TestInternal:
    def test___init___basic(self):
        tag = Internal()
        assert tag.tag == 'tag'
        assert tag.recurse is False
        assert tag.serializers == []
        assert tag.deserializers == []

    def test___init___options(self):
        tag = Internal(tag='kind', recurse=True, serializers=[None])
        assert tag.tag == 'kind'
        assert tag.recurse is True
        assert tag.deserializers == []
        assert tag.serializers == [None]

    def test__serialize_with(self):
        class Example(Model):
            pass

        tag = Internal(tag='kind')
        tag._bind(Example)
        d = {'something': 1}
        assert tag._serialize_with(Example(), d) is d
        assert d == {'something': 1, 'kind': 'Example'}

    def test__deserialize_with(self):
        class Example(Model):
            pass

        class Example2(Example):
            pass

        tag = Internal(tag='kind')
        tag._bind(Example)

        model = Example()
        d = {'kind': 'Example2', 'something': 1}
        result = tag._deserialize_with(model, d)
        assert result[0] is model
        assert result[0].__class__ is Example2
        assert result[1] is d

    def test__deserialize_with_untagged(self):
        class Example(Model):
            pass

        class Example2(Example):
            pass

        tag = Internal(tag='kind')

        with raises(DeserializationError) as e:
            tag._deserialize_with(object(), {'something': 1})
        assert (
            e.value.pretty()
            == """\
DeserializationError: expected tag 'kind'
    Due to => tag 'Internal'"""
        )


@mock.patch('serde.tags.Tag.lookup_tag', lambda _, variant: variant.__name__)
class TestAdjacent:
    def test___init___basic(self):
        tag = Adjacent()
        assert tag.tag == 'tag'
        assert tag.content == 'content'
        assert tag.recurse is False
        assert tag.serializers == []
        assert tag.deserializers == []

    def test___init___options(self):
        tag = Adjacent(tag='kind', content='data', recurse=True, serializers=[None])
        assert tag.tag == 'kind'
        assert tag.content == 'data'
        assert tag.recurse is True
        assert tag.deserializers == []
        assert tag.serializers == [None]

    def test__serialize_with(self):
        class Example(Model):
            pass

        tag = Adjacent(tag='kind', content='data')
        tag._bind(Example)
        d = {'something': 1}
        assert tag._serialize_with(Example(), d) == {'kind': 'Example', 'data': d}

    def test__deserialize_with(self):
        class Example(Model):
            pass

        class Example2(Example):
            pass

        tag = Adjacent(tag='kind', content='data')
        tag._bind(Example)

        model = Example()
        d = {'kind': 'Example2', 'data': {'something': 1}}
        result = tag._deserialize_with(model, d)
        assert result[0] is model
        assert result[0].__class__ is Example2
        assert result[1] is d['data']

    def test__deserialize_with_untagged(self):
        class Example(Model):
            pass

        class Example2(Example):
            pass

        tag = Adjacent(tag='kind', content='data')

        with raises(DeserializationError) as e:
            tag._deserialize_with(object(), {'something': 1})
        assert (
            e.value.pretty()
            == """\
DeserializationError: expected tag 'kind'
    Due to => tag 'Adjacent'"""
        )

        with raises(DeserializationError) as e:
            tag._deserialize_with(object(), {'kind': 'Example2', 'something': 1})
        assert (
            e.value.pretty()
            == """\
DeserializationError: expected content 'data'
    Due to => tag 'Adjacent'"""
        )
