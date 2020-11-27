"""
This module contains tag classes for use with `Models <serde.Model>`.
"""

from collections import OrderedDict

from serde import fields, utils
from serde.exceptions import ValidationError


class Tag(fields._Base):
    """
    A tag field for a `Model <serde.Model>`.

    Args:
        recurse (bool): whether to recurse subclasses when calculating model
            variants.
        serializers (list): a list of serializer functions taking the value to
            serialize as an argument. The functions need to raise an `Exception`
            if they fail. These serializer functions will be applied before the
            primary serializer on this tag.
        deserializers (list): a list of deserializer functions taking the value
            to deserialize as an argument. The functions need to raise an
            `Exception` if they fail. These deserializer functions will be
            applied after the primary deserializer on this tag.
    """

    def __init__(self, recurse=False, serializers=None, deserializers=None):
        """
        Create a new `Tag`.
        """
        super(Tag, self).__init__(serializers=serializers, deserializers=deserializers)
        self.recurse = recurse

    def variants(self):
        """
        Returns a list of variants for the bound model class.
        """
        base_cls = self.__model__

        if self.recurse:
            variants = utils.subclasses(base_cls)
        else:
            variants = base_cls.__subclasses__()

        if not base_cls.__abstract__:
            variants = [base_cls] + variants

        return variants

    def lookup_tag(self, variant):
        """
        Get the tag value for the given model variant.

        Args:
            variant (Model): the model class.

        Returns:
            str: the corresponding tag value.
        """
        return f'{variant.__module__}.{variant.__qualname__}'

    def lookup_variant(self, tag):
        """
        Get the variant for the given tag value.

        Args:
            tag: the tag value.

        Returns:
            Model: the corresponding Model class.
        """
        for variant in self.variants():
            if self.serialize(variant) == tag:
                return variant

    def serialize(self, value):
        """
        Serialize a Model variant into a tag value.
        """
        return self.lookup_tag(value)

    def deserialize(self, value):
        """
        Deserialize a tag value into a Model variant.
        """
        variant = self.lookup_variant(value)
        if not variant:
            raise ValidationError('no variant found', value=value)
        return variant


class External(Tag):
    """
    A tag to externally tag `~serde.Model` data.
    """

    def _serialize_with(self, model, d):
        """
        Serialize the model variant by externally tagging the given dictionary.
        """
        variant = model.__class__
        d = OrderedDict([(self._serialize(variant), d)])
        return d

    def _deserialize_with(self, model, d):
        """
        Deserialize the model variant from an externally tagged dictionary.
        """
        try:
            tag = next(iter(d))
        except StopIteration:
            raise ValidationError('missing data, expected externally tagged data')

        model.__class__ = self._deserialize(tag)

        return model, d[tag]


class Internal(Tag):
    """
    A tag to internally tag `~serde.Model` data.

    Args:
        tag: the key to use when serializing the model variant's tag.
    """

    def __init__(self, tag='tag', **kwargs):
        """
        Create a new `Internal`.
        """
        super(Internal, self).__init__(**kwargs)
        self.tag = tag

    def _serialize_with(self, model, d):
        """
        Serialize the model variant by internally tagging the given dictionary.
        """
        variant = model.__class__
        d[self.tag] = self._serialize(variant)
        return d

    def _deserialize_with(self, model, d):
        """
        Deserialize the model variant from an internally tagged dictionary.
        """
        try:
            tag = d[self.tag]
        except KeyError:
            raise ValidationError(f'missing data, expected tag {self.tag!r}')

        model.__class__ = self._deserialize(tag)

        return model, d


class Adjacent(Tag):
    """
    A tag to adjacently tag `~serde.Model` data.

    Args:
        tag: the key to use when serializing the model variant's tag.
        content: the key to use when serializing the model variant's data.
    """

    def __init__(self, tag='tag', content='content', **kwargs):
        """
        Create a new `Adjacent`.
        """
        super(Adjacent, self).__init__(**kwargs)
        self.tag = tag
        self.content = content

    def _serialize_with(self, model, d):
        """
        Serialize the model variant by adjacently tagging the given dictionary.
        """
        variant = model.__class__
        d = OrderedDict([(self.tag, self._serialize(variant)), (self.content, d)])
        return d

    def _deserialize_with(self, model, d):
        """
        Deserialize the model variant from an adjacently tagged dictionary.
        """
        try:
            tag = d[self.tag]
        except KeyError:
            raise ValidationError(f'missing data, expected tag {self.tag!r}')

        try:
            content = d[self.content]
        except KeyError:
            raise ValidationError(f'missing data, expected content {self.content!r}')

        model.__class__ = self._deserialize(tag)

        return model, content


__all__ = [name for name, obj in globals().items() if utils.is_subclass(obj, Tag)]
