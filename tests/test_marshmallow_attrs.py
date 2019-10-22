import dataclasses
import typing as t

import attr
import marshmallow
import pytest

import desert


@pytest.fixture(name="dataclass", params=[attr.dataclass, dataclasses.dataclass])
def dataclass_param(request):
    """Parametrize over both implementations of the @dataclass decorator."""
    return request.param


def test_simple(dataclass):
    @dataclass
    class A:
        x: int = attr.ib()

    data = desert.schema_class(A)().load(data={"x": 5})

    assert data == A(x=5)


def test_validation(dataclass):
    @dataclass
    class A:
        x: int = attr.ib()

    schema = desert.schema_class(A)()
    with pytest.raises(marshmallow.exceptions.ValidationError):
        schema.load({"y": 5})


def test_not_a_dataclass(dataclass):
    """Raises when object is not a dataclass."""

    class A:
        x: int

    with pytest.raises(desert.exceptions.NotAnAttrsClassOrDataclass):
        desert.schema_class(A)


def test_set_default(dataclass):
    @dataclass
    class A:
        x: int = attr.ib(default=1)

    schema = desert.schema_class(A)()
    data = schema.load({"x": 1})
    assert data == A(1)


def test_list(dataclass):
    @dataclass
    class A:
        y: t.List[int] = attr.ib(factory=list)

    schema = desert.schema_class(A)()
    data = schema.load({"y": [1]})
    assert data == A([1])


def test_dict(dataclass):
    @dataclass
    class A:
        y: t.Dict[int, int] = attr.ib(factory=dict)

    schema = desert.schema_class(A)()
    data = schema.load({"y": {1: 2, 3: 4}})

    assert data == A({1: 2, 3: 4})


def test_nested(dataclass):
    @dataclass
    class A:
        x: int

    @dataclass
    class B:
        y: A

    data = desert.schema_class(B)().load({"y": {"x": 5}})

    assert data == B(A(5))


def test_optional(dataclass):
    @dataclass
    class A:
        x: t.Optional[int]

    data = desert.schema_class(A)().load({"x": None})
    assert data == A(None)
