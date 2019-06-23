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
