import typing as t

import attr
import marshmallow
import pytest

import desert


def test_init():
    pass


def test_simple():
    @desert.dataclass
    class A:
        x: int = attr.ib()

    data, errors = desert.class_schema(A)(strict=True).load(data={"x": 5})
    assert not errors
    assert data == A(x=5)


def test_validation():
    @desert.dataclass
    class A:
        x: int = attr.ib()

    schema = desert.class_schema(A)(strict=True)
    with pytest.raises(marshmallow.exceptions.ValidationError):
        schema.load({"y": 5})


def test_not_a_dataclass():
    """Raises when object is not a dataclass."""

    class A:
        x: int

    with pytest.raises(attr.exceptions.NotAnAttrsClassError):
        desert.class_schema(A)


def test_set_default():
    @desert.dataclass
    class A:
        x: int = attr.ib(default=1)

    schema = desert.class_schema(A)(strict=True)
    data, _ = schema.load({"x": 1})
    assert data == A(1)


def test_list():
    @desert.dataclass
    class A:
        y: t.List[int] = attr.ib(factory=list)

    schema = desert.class_schema(A)(strict=True)
    data, _ = schema.load({"y": [1]})
    assert data == A([1])


def test_dict():
    @desert.dataclass
    class A:
        y: t.Dict[int, int] = attr.ib(factory=dict)

    schema = desert.class_schema(A)(strict=True)
    data, errors = schema.load({"y": {1: 2, 3: 4}})
    assert not errors
    assert data == A({1: 2, 3: 4})


def test_nested():
    @desert.dataclass
    class A:
        x: int

    @desert.dataclass
    class B:
        y: A

    data, errors = desert.class_schema(B)().load({"y": {"x": 5}})
    assert not errors
    assert data == B(A(5))


def test_optional():
    @desert.dataclass
    class A:
        x: t.Optional[int]

    data, _ = desert.class_schema(A)(strict=True).load({"x": None})
    assert data == A(None)
