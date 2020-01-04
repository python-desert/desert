import dataclasses
import datetime
import enum
import sys
import types
import typing as t

import attr
import marshmallow
import pytest

import desert


@attr.s(frozen=True, order=False)
class DataclassModule:
    """Implementation of a dataclass module like attr or dataclasses."""

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
    """Load dict into a dataclass instance."""

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

    data = schema.load({})
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


def test_optional_present(module):
    """Setting an optional type allows passing None."""

    @module.dataclass
    class A:
        x: t.Optional[int]

    data = desert.schema_class(A)().load({"x": None})
    assert data == A(None)


def test_custom_field(module):
    @module.dataclass
    class A:
        x: str = module.field(
            metadata=desert.metadata(marshmallow.fields.NaiveDateTime())
        )

    timestring = "2019-10-21T10:25:00"
    dt = datetime.datetime(year=2019, month=10, day=21, hour=10, minute=25, second=00)
    schema = desert.schema(A)

    assert schema.load({"x": timestring}) == A(x=dt)


def test_concise_dataclasses_field():
    """Concisely create a dataclasses.Field."""

    @dataclasses.dataclass
    class A:
        x: str = desert.field(marshmallow.fields.NaiveDateTime())

    timestring = "2019-10-21T10:25:00"
    dt = datetime.datetime(year=2019, month=10, day=21, hour=10, minute=25, second=00)
    schema = desert.schema(A)

    assert schema.load({"x": timestring}) == A(x=dt)


def test_concise_attrib():
    """Concisely create an attr.ib()"""

    @attr.dataclass
    class A:
        x: str = desert.ib(marshmallow.fields.NaiveDateTime())

    timestring = "2019-10-21T10:25:00"
    dt = datetime.datetime(year=2019, month=10, day=21, hour=10, minute=25, second=00)
    schema = desert.schema(A)

    assert schema.load({"x": timestring}) == A(x=dt)


def test_union(module):
    """Deserialize one of several types."""

    @module.dataclass
    class A:
        x: t.Union[int, str]

    schema = desert.schema_class(A)()

    dumped = {"x": "X"}
    loaded = A("X")
    assert schema.load(dumped) == loaded

    assert schema.dump(loaded) == dumped

    dumped = {"x": "X"}
    loaded = A("X")

    assert schema.load(dumped) == loaded
    assert schema.dump(loaded) == dumped


def test_enum(module):
    """Deserialize an enum object."""

    class Color(enum.Enum):
        RED = enum.auto()
        GREEN = enum.auto()

    @module.dataclass
    class A:
        x: Color

    schema = desert.schema_class(A)()
    dumped = {"x": "RED"}
    loaded = A(Color.RED)
    assert schema.load(dumped) == loaded
    assert schema.dump(loaded) == dumped


def test_tuple(module):
    """Round trip a tuple.

    The tuple is converted to list only for dumps(), not during dump().
    """

    @module.dataclass
    class A:
        x: t.Tuple[int, bool]

    schema = desert.schema_class(A)()
    dumped = {"x": (1, False)}
    loaded = A(x=(1, False))

    assert schema.load(dumped) == loaded
    assert schema.dump(loaded) == dumped
    assert schema.loads(schema.dumps(loaded)) == loaded


def test_attr_factory():
    """Attrs default factory instantiates the factory type if no value is passed."""

    @attr.dataclass
    class A:
        x: t.List[int] = attr.ib(factory=list)

    data = desert.schema_class(A)().load({})
    assert data == A([])


def test_dataclasses_factory():
    """Dataclasses default factory instantiates the factory type if no value is passed."""

    @dataclasses.dataclass
    class A:
        x: t.List[int] = dataclasses.field(default_factory=list)

    data = desert.schema_class(A)().load({})
    assert data == A([])


def test_newtype(module):
    """An instance of NewType delegates to its supertype."""

    MyInt = t.NewType("MyInt", int)

    @module.dataclass
    class A:
        x: MyInt

    schema = desert.schema_class(A)()
    dumped = {"x": 1}
    loaded = A(x=1)

    assert schema.load(dumped) == loaded
    assert schema.dump(loaded) == dumped


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Forward references and string annotations are broken. \n"
        + "See https://github.com/lovasoa/marshmallow_dataclass/issues/13"
    ),
)
def test_forward_reference(module):
    """Build schemas from classes that are defined below their containing class."""

    @module.dataclass
    class A:
        x: "B"

    @module.dataclass
    class B:
        y: int

    schema = desert.schema_class(A)()
    dumped = {"x": {"y": 1}}
    loaded = A((B(1)))

    assert schema.load(dumped) == loaded
    assert schema.dump(loaded) == dumped


def test_forward_reference_module_scope():
    """Run the forward reference test at global scope."""

    import tests.cases.forward_reference  # pylint disable=unused-import,import-outside-toplevel


def test_non_string_metadata_key(module):
    """A non-string key in the attrib metadata comes through in the mm field."""

    @module.dataclass
    class A:
        x: int = module.field(metadata={1: 2})

    field = desert.schema(A).fields["x"]
    assert field.metadata == {1: 2, desert._make._DESERT_SENTINEL: {}}


def test_non_optional_means_required(module):
    """Non-optional fields are required."""

    @module.dataclass
    class A:
        x: int = module.field(metadata={1: 2})

    schema = desert.schema(A)

    with pytest.raises(marshmallow.exceptions.ValidationError):
        schema.load({})


def test_ignore_unknown_fields(module):
    """Enable unknown fields with meta argument."""

    @module.dataclass
    class A:
        x: int

    schema_class = desert.schema_class(A, meta={"unknown": marshmallow.EXCLUDE})
    schema = schema_class()
    data = schema.load({"x": 1, "y": 2})
    assert data == A(x=1)


def test_raise_unknown_type(module):
    """Raise UnknownType for failed inferences."""

    @module.dataclass
    class A:
        x: list

    with pytest.raises(desert.exceptions.UnknownType):
        desert.schema_class(A)


@pytest.mark.skipif(
    sys.version_info[:2] <= (3, 6), reason="3.6 has isinstance(t.Sequence[int], type)."
)
def test_raise_unknown_generic(module):
    """Raise UnknownType for unknown generics."""

    @module.dataclass
    class A:
        x: t.Sequence[int]

    with pytest.raises(desert.exceptions.UnknownType):
        desert.schema_class(A)


def test_tuple_ellipsis(module):
    """Tuple with ellipsis allows variable length tuple.

    See :class:`typing.Tuple`.
    """

    @module.dataclass
    class A:
        x: t.Tuple[int, ...]

    schema = desert.schema_class(A)()
    dumped = {"x": (1, 2, 3)}
    loaded = A(x=(1, 2, 3))

    assert schema.load(dumped) == loaded
    assert schema.dump(loaded) == {"x": [1, 2, 3]}
    assert schema.loads(schema.dumps(loaded)) == loaded


def test_only():
    """only() extracts the only item in an iterable."""
    assert desert._make.only([1]) == 1


def test_only_raises():
    """only() raises if the iterable has an unexpected number of entries.'"""
    with pytest.raises(ValueError):
        desert._make.only([])

    with pytest.raises(ValueError):
        desert._make.only([1, 2])
