import typing as t

import attr
import marshmallow
import pytest

import marshmallow_attrs


def test_init():
    pass


def test_simple():
    @marshmallow_attrs.dataclass
    class A:
        x: int = attr.ib()

    data, errors = marshmallow_attrs.class_schema(A)(strict=True).load(data={"x": 5})
    assert not errors
    assert data == A(x=5)


def test_validation():
    @marshmallow_attrs.dataclass
    class A:
        x: int = attr.ib()

    schema = marshmallow_attrs.class_schema(A)(strict=True)
    with pytest.raises(marshmallow.exceptions.ValidationError):
        schema.load({"y": 5})


def test_not_a_dataclass():
    """Raises when object is not a dataclass."""

    class A:
        x: int

    with pytest.raises(attr.exceptions.NotAnAttrsClassError):
        marshmallow_attrs.class_schema(A)


def test_set_default():
    @marshmallow_attrs.dataclass
    class A:
        x: int = attr.ib(default=1)

    schema = marshmallow_attrs.class_schema(A)(strict=True)
    data, _ = schema.load({"x": 1})
    assert data == A(1)


def test_list():
    @marshmallow_attrs.dataclass
    class A:
        y: t.List[int] = attr.ib(factory=list)

    schema = marshmallow_attrs.class_schema(A)(strict=True)
    data, _ = schema.load({"y": [1]})
    assert data == A([1])


def test_dict():
    @marshmallow_attrs.dataclass
    class A:
        y: t.Dict[int, int] = attr.ib(factory=dict)

    schema = marshmallow_attrs.class_schema(A)(strict=True)
    data, errors = schema.load({"y": {1: 2, 3: 4}})
    assert not errors
    assert data == A({1: 2, 3: 4})


def test_nested():
    @marshmallow_attrs.dataclass
    class A:
        x: int

    @marshmallow_attrs.dataclass
    class B:
        y: A

    data, errors = marshmallow_attrs.class_schema(B)().load({"y": {"x": 5}})
    assert not errors
    assert data == B(A(5))


def test_optional():
    @marshmallow_attrs.dataclass
    class A:
        x: t.Optional[int]

    data, _ = marshmallow_attrs.class_schema(A)(strict=True).load({"x": None})
    assert data == A(None)
