import uuid
from typing import Dict, FrozenSet, List, Optional, Set, Union

from pytest import raises

from serde import Model, fields


def test_typing_annotations_optional_combinations():
    class Example(Model):
        a: str
        b: str = 'testing...'
        c: Optional[str]
        d: Optional[str] = 'testing...'

    assert not hasattr(Example, 'a')
    assert not hasattr(Example, 'b')
    assert not hasattr(Example, 'c')
    assert not hasattr(Example, 'd')

    assert Example.__fields__.a == fields.Str()
    assert Example.__fields__.b == fields.Str(default='testing...')
    assert Example.__fields__.c == fields.Optional(fields.Str)
    assert Example.__fields__.d == fields.Optional(fields.Str, default='testing...')

    with raises(TypeError) as e:
        Example()
    assert str(e.value) == "__init__() missing required argument 'a'"

    expected = Example(a='required...', b='testing...', c=None, d='testing...')
    assert Example(a='required...') == expected


def test_typing_annotations_each_type():
    class Example(Model):
        a: Optional[str]
        b: Union[str, None]
        c: Dict[uuid.UUID, Optional[bool]]
        d: List[Optional[Set[int]]] = [42, None]
        e: FrozenSet[int]

    assert Example.__fields__.a == fields.Optional(fields.Str)
    assert Example.__fields__.b == fields.Optional(fields.Str)
    assert Example.__fields__.c == fields.Dict(
        fields.Uuid, fields.Optional(fields.Bool)
    )
    assert Example.__fields__.d == fields.List(
        fields.Optional(fields.Set(fields.Int)), default=[42, None]
    )
    assert Example.__fields__.e == fields.FrozenSet(fields.Int)
