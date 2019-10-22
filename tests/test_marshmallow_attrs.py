import typing as t

import attr
import marshmallow
import pytest

import desert


def test_init():
    pass


def test_simple():
    @attr.dataclass
    class A:
        x: int = attr.ib()

    data = desert.schema_class(A)().load(data={"x": 5})

    assert data == A(x=5)


def test_validation():
    @attr.dataclass
    class A:
        x: int = attr.ib()

    schema = desert.schema_class(A)()
    with pytest.raises(marshmallow.exceptions.ValidationError):
        schema.load({"y": 5})


def test_not_a_dataclass():
    """Raises when object is not a dataclass."""

    class A:
        x: int

    with pytest.raises(desert.exceptions.NotAnAttrsClassOrDataclass):
        desert.schema_class(A)


def test_set_default():
    @attr.dataclass
    class A:
        x: int = attr.ib(default=1)

    schema = desert.schema_class(A)()
    data = schema.load({"x": 1})
    assert data == A(1)


def test_list():
    @attr.dataclass
    class A:
        y: t.List[int] = attr.ib(factory=list)

    schema = desert.schema_class(A)()
    data = schema.load({"y": [1]})
    assert data == A([1])


def test_dict():
    @attr.dataclass
    class A:
        y: t.Dict[int, int] = attr.ib(factory=dict)

    schema = desert.schema_class(A)()
    data = schema.load({"y": {1: 2, 3: 4}})

    assert data == A({1: 2, 3: 4})


def test_nested():
    @attr.dataclass
    class A:
        x: int

    @attr.dataclass
    class B:
        y: A

    data = desert.schema_class(B)().load({"y": {"x": 5}})

    assert data == B(A(5))


def test_optional():
    @attr.dataclass
    class A:
        x: t.Optional[int]

    data = desert.schema_class(A)().load({"x": None})
    assert data == A(None)
