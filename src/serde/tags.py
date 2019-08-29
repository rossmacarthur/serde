"""
This module contains Tag classes `Models <serde.model.Model>`.
"""

from serde import fields, utils
from serde.exceptions import DeserializationError, SerializationError, map_errors


class Tag(fields.BaseField):
    """
    A tag Field for a `Model <serde.model.Model>`.
    """

    def __init__(self, recurse=False, **kwargs):
        """
        Create a new Tag.

        Args:
            recurse (bool): whether to recurse subclasses when calculating Model
                variants.
            **kwargs: keyword arguments for the `Base` constructor.
        """
        super(Tag, self).__init__(**kwargs)
        self.recurse = recurse

    def variants(self):
        """
        Returns a list of variants for the given Model class.
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
        Get the tag value for the given Model variant.

        Args:
            variant (Model): the Model class.

        Returns:
            tag: the corresponding tag value.
        """
        return variant.__name__

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
            raise DeserializationError(
                'no variant found for tag',
                value=value,
                field=self,
                model_cls=self.__model__
            )

        return variant


class External(Tag):
    """
    A tag to externally tag `Model <serde.model.Model>` data.
    """

    def _serialize_with(self, model, d):
        """
        Serialize the Model variant by externally tagging the given dictionary.
        """
        variant = model.__class__

        with map_errors(SerializationError, value=variant, field=self, model_cls=model.__class__):
            d = {self._serialize(variant): d}

        return d

    def _deserialize_with(self, model, d):
        """
        Deserialize the Model variant from an externally tagged dictionary.
        """
        try:
            tag = next(iter(d))
        except StopIteration:
            raise DeserializationError('expected externally tagged data', field=self)

        with map_errors(DeserializationError, value=tag, field=self, model_cls=model.__class__):
            model.__class__ = self._deserialize(tag)

        return model, d[tag]


class Internal(Tag):
    """
    A tag to internally tag `Model <serde.model.Model>` data.
    """

    def __init__(self, tag='tag', **kwargs):
        """
        Create a new Internal tag.

        Args:
            tag: the key to use when serializing the Model variant's tag.
        """
        super(Internal, self).__init__(**kwargs)
        self.tag = tag

    def _serialize_with(self, model, d):
        """
        Serialize the Model variant by internally tagging the given dictionary.
        """
        variant = model.__class__

        with map_errors(SerializationError, value=variant, field=self, model_cls=model.__class__):
            d[self.tag] = self._serialize(variant)

        return d

    def _deserialize_with(self, model, d):
        """
        Deserialize the Model variant from an internally tagged dictionary.
        """
        try:
            tag = d[self.tag]
        except KeyError:
            raise DeserializationError('expected tag {!r}'.format(self.tag), field=self)

        with map_errors(DeserializationError, value=tag, field=self, model_cls=model.__class__):
            model.__class__ = self._deserialize(tag)

        return model, d


class Adjacent(Tag):
    """
    A tag to adjacently tag `Model <serde.model.Model>` data.
    """

    def __init__(self, tag='tag', content='content', **kwargs):
        """
        Create a new Adjacent tag.

        Args:
            tag: the key to use when serializing the Model variant's tag.
            content: the key to use when serializing the Model variant's data.
        """
        super(Adjacent, self).__init__(**kwargs)
        self.tag = tag
        self.content = content

    def _serialize_with(self, model, d):
        """
        Serialize the Model variant by adjacently tagging the given dictionary.
        """
        variant = model.__class__

        with map_errors(SerializationError, field=self, model_cls=model.__class__):
            d = {
                self.tag: self._serialize(variant),
                self.content: d
            }

        return d

    def _deserialize_with(self, model, d):
        """
        Deserialize the Model variant from an adjacently tagged dictionary.
        """
        try:
            tag = d[self.tag]
        except KeyError:
            raise DeserializationError('expected tag {!r}'.format(self.tag), field=self)

        try:
            content = d[self.content]
        except KeyError:
            raise DeserializationError('expected content {!r}'.format(self.content), field=self)

        with map_errors(DeserializationError, field=self, model_cls=model.__class__):
            model.__class__ = self._deserialize(tag)

        return model, content
