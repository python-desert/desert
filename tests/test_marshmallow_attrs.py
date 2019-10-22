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
    """Passing the wrong keys will raise ValidationError."""

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
    """Setting a default value in the dataclass makes passing it optional."""

    @dataclass
    class A:
        x: int = 1

    schema = desert.schema_class(A)()
    data = schema.load({"x": 1})
    assert data == A(1)


def test_list(dataclass):
    """Build a generic list *without* setting a factory on the dataclass."""

    @dataclass
    class A:
        y: t.List[int]

    schema = desert.schema_class(A)()
    data = schema.load({"y": [1]})
    assert data == A([1])


def test_dict(dataclass):
    """Build a dict without setting a factory on the dataclass."""

    @dataclass
    class A:
        y: t.Dict[int, int]

    schema = desert.schema_class(A)()
    data = schema.load({"y": {1: 2, 3: 4}})

    assert data == A({1: 2, 3: 4})


def test_nested(dataclass):
    """One object can hold instances of another."""

    @dataclass
    class A:
        x: int

    @dataclass
    class B:
        y: A

    data = desert.schema_class(B)().load({"y": {"x": 5}})

    assert data == B(A(5))


def test_optional(dataclass):
    """Setting an optional type makes the default None."""

    @dataclass
    class A:
        x: t.Optional[int]

    data = desert.schema_class(A)().load({})
    assert data == A(None)
