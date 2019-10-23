import dataclasses
import datetime
import types
import typing as t

import attr
import marshmallow
import pytest

import desert


@attr.s
class DataclassModule:
    dataclass = attr.ib()
    field = attr.ib()
    fields = attr.ib()


@pytest.fixture(
    name="module",
    params=[
        DataclassModule(dataclass=attr.dataclass, fields=attr.fields, field=attr.ib),
        DataclassModule(
            dataclass=dataclasses.dataclass,
            fields=dataclasses.fields,
            field=dataclasses.field,
        ),
    ],
)
def dataclass_param(request):
    """Parametrize over both implementations of the @dataclass decorator."""
    return request.param


def test_simple(module):
    @module.dataclass
    class A:
        x: int

    data = desert.schema_class(A)().load(data={"x": 5})

    assert data == A(x=5)


def test_validation(module):
    """Passing the wrong keys will raise ValidationError."""

    @module.dataclass
    class A:
        x: int

    schema = desert.schema_class(A)()
    with pytest.raises(marshmallow.exceptions.ValidationError):
        schema.load({"y": 5})


def test_not_a_dataclass(module):
    """Raises when object is not a dataclass."""

    class A:
        x: int

    with pytest.raises(desert.exceptions.NotAnAttrsClassOrDataclass):
        desert.schema_class(A)


def test_set_default(module):
    """Setting a default value in the dataclass makes passing it optional."""

    @module.dataclass
    class A:
        x: int = 1

    schema = desert.schema_class(A)()
    data = schema.load({"x": 1})
    assert data == A(1)


def test_list(module):
    """Build a generic list *without* setting a factory on the dataclass."""

    @module.dataclass
    class A:
        y: t.List[int]

    schema = desert.schema_class(A)()
    data = schema.load({"y": [1]})
    assert data == A([1])


def test_dict(module):
    """Build a dict without setting a factory on the dataclass."""

    @module.dataclass
    class A:
        y: t.Dict[int, int]

    schema = desert.schema_class(A)()
    data = schema.load({"y": {1: 2, 3: 4}})

    assert data == A({1: 2, 3: 4})


def test_nested(module):
    """One object can hold instances of another."""

    @module.dataclass
    class A:
        x: int

    @module.dataclass
    class B:
        y: A

    data = desert.schema_class(B)().load({"y": {"x": 5}})

    assert data == B(A(5))


def test_optional(module):
    """Setting an optional type makes the default None."""

    @module.dataclass
    class A:
        x: t.Optional[int]

    data = desert.schema_class(A)().load({})
    assert data == A(None)


def test_custom_field(module):
    @module.dataclass
    class A:
        x: str = module.field(
            metadata={
                "desert": {"marshmallow_field": marshmallow.fields.NaiveDateTime()}
            }
        )

    timestring = "2019-10-21T10:25:00"
    dt = datetime.datetime(year=2019, month=10, day=21, hour=10, minute=25, second=00)
    schema = desert.schema(A)

    assert schema.load({"x": timestring}) == A(x=dt)
