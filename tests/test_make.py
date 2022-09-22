import dataclasses
import datetime
import decimal
import enum
import re
import sys
import types
import typing as t

# https://github.com/pytest-dev/pytest/issues/7469
import _pytest.fixtures
import attr
import marshmallow
import marshmallow.fields
import pytest
import typing_extensions

import desert


@attr.frozen(order=False)
class DataclassModule:
    """Implementation of a dataclass module like attr or dataclasses."""

    dataclass: t.Callable[[type], type]
    field: t.Callable[..., t.Any] = attr.ib()
    fields: t.Callable[[type], object] = attr.ib()


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
    ids=["attrs", "dataclasses"],
)
def dataclass_param(request: _pytest.fixtures.SubRequest) -> DataclassModule:
    """Parametrize over both implementations of the @dataclass decorator."""
    module = t.cast(DataclassModule, request.param)
    return module


class AssertLoadDumpProtocol(typing_extensions.Protocol):
    def __call__(
        self, schema: marshmallow.Schema, loaded: t.Any, dumped: t.Dict[t.Any, t.Any]
    ) -> None:
        ...


def _assert_dump(
    schema: marshmallow.Schema, loaded: t.Any, dumped: t.Dict[t.Any, t.Any]
) -> None:
    assert schema.dump(loaded) == dumped


def _assert_load(
    schema: marshmallow.Schema, loaded: t.Any, dumped: t.Dict[t.Any, t.Any]
) -> None:
    assert schema.load(dumped) == loaded


def _assert_dump_load(
    schema: marshmallow.Schema, loaded: t.Any, dumped: t.Dict[t.Any, t.Any]
) -> None:
    assert schema.loads(schema.dumps(loaded)) == loaded


def _assert_load_dump(
    schema: marshmallow.Schema, loaded: t.Any, dumped: t.Dict[t.Any, t.Any]
) -> None:
    assert schema.dump(schema.load(dumped)) == dumped


def fixture_from_dict(
    name: str,
    id_to_value: t.Mapping[
        str, t.Callable[[marshmallow.Schema, t.Dict[t.Any, t.Any], t.Any], None]
    ],
) -> _pytest.fixtures.FixtureFunction:
    """
    Create fixture parametrized to yield each value and labeled with the
    corresponding ID.

    Args:
        name: Name of the fixture itself
        id_to_value: Mapping from ID labels to values

    Returns:
        The PyTest fixture
    """

    @pytest.fixture(name=name, params=id_to_value.values(), ids=id_to_value.keys())  # type: ignore[call-overload, misc]
    def fixture(request: _pytest.fixtures.SubRequest) -> object:
        return request.param

    # This looks right to me but mypy says:
    #   error: Incompatible return value type (got "Callable[[SubRequest], object]", expected "_pytest.fixtures._FixtureFunction")  [return-value]
    return fixture  # type: ignore[no-any-return]


_assert_dump_load = fixture_from_dict(
    name="assert_dump_load",
    id_to_value={
        "load": _assert_load,
        "dump": _assert_dump,
        "dump load": _assert_dump_load,
        "load dump": _assert_load_dump,
    },
)


def test_simple(module: DataclassModule) -> None:
    """Load dict into a dataclass instance."""

    @module.dataclass
    class A:
        x: int

    data = desert.schema_class(A)().load(data={"x": 5})

    assert data == A(x=5)  # type: ignore[call-arg]


def test_validation(module: DataclassModule) -> None:
    """Passing the wrong keys will raise ValidationError."""

    @module.dataclass
    class A:
        x: int

    schema = desert.schema_class(A)()
    with pytest.raises(marshmallow.exceptions.ValidationError):
        schema.load({"y": 5})


def test_not_a_dataclass(module: DataclassModule) -> None:
    """Raises when object is not a dataclass."""

    class A:
        x: int

    with pytest.raises(desert.exceptions.NotAnAttrsClassOrDataclass):
        desert.schema_class(A)


def test_set_default(module: DataclassModule) -> None:
    """Setting a default value in the dataclass makes passing it optional."""

    @module.dataclass
    class A:
        x: int = 1

    schema = desert.schema_class(A)()
    data = schema.load({"x": 1})
    assert data == A(1)  # type: ignore[call-arg]

    data = schema.load({})
    assert data == A(1)  # type: ignore[call-arg]


@pytest.mark.parametrize("annotation_class", (t.List, t.Sequence, t.MutableSequence))
def test_list(module: DataclassModule, annotation_class: type) -> None:
    """Build a generic list *without* setting a factory on the dataclass."""
    cls = type("A", (object,), {"__annotations__": {"y": annotation_class[int]}})  # type: ignore[index]
    A = module.dataclass(cls)

    schema = desert.schema_class(A)()
    data = schema.load({"y": [1]})
    assert data == A([1])


@pytest.mark.parametrize("annotation_class", (t.Dict, t.Mapping, t.MutableMapping))
def test_dict(module: DataclassModule, annotation_class: type) -> None:
    """Build a dict without setting a factory on the dataclass."""
    cls = type("A", (object,), {"__annotations__": {"y": annotation_class[int, int]}})  # type: ignore[index]
    A = module.dataclass(cls)

    schema = desert.schema_class(A)()
    data = schema.load({"y": {1: 2, 3: 4}})

    assert data == A({1: 2, 3: 4})


def test_nested(module: DataclassModule) -> None:
    """One object can hold instances of another."""

    @module.dataclass
    class A:
        x: int

    @module.dataclass
    class B:
        y: A

    data = desert.schema_class(B)().load({"y": {"x": 5}})

    assert data == B(A(5))  # type: ignore[call-arg]


def test_optional(module: DataclassModule) -> None:
    """Setting an optional type makes the default None."""

    @module.dataclass
    class A:
        x: t.Optional[int]

    data = desert.schema_class(A)().load({})
    assert data == A(None)  # type: ignore[call-arg]


def test_optional_present(module: DataclassModule) -> None:
    """Setting an optional type allows passing None."""

    @module.dataclass
    class A:
        x: t.Optional[int]

    data = desert.schema_class(A)().load({"x": None})
    assert data == A(None)  # type: ignore[call-arg]


def test_custom_field(module: DataclassModule) -> None:
    @module.dataclass
    class A:
        x: str = module.field(
            metadata=desert.metadata(marshmallow.fields.NaiveDateTime())
        )

    timestring = "2019-10-21T10:25:00"
    dt = datetime.datetime(year=2019, month=10, day=21, hour=10, minute=25, second=00)
    schema = desert.schema(A)

    assert schema.load({"x": timestring}) == A(x=dt)  # type: ignore[call-arg]


def test_concise_dataclasses_field() -> None:
    """Concisely create a dataclasses.Field."""

    @dataclasses.dataclass
    class A:
        x: datetime.datetime = desert.field(marshmallow.fields.NaiveDateTime())

    timestring = "2019-10-21T10:25:00"
    dt = datetime.datetime(year=2019, month=10, day=21, hour=10, minute=25, second=00)
    schema = desert.schema(A)

    assert schema.load({"x": timestring}) == A(x=dt)


def test_concise_attrib() -> None:
    """Concisely create an attr.ib()"""

    @attr.dataclass
    class A:
        x: datetime.datetime = desert.ib(marshmallow.fields.NaiveDateTime())

    timestring = "2019-10-21T10:25:00"
    dt = datetime.datetime(year=2019, month=10, day=21, hour=10, minute=25, second=00)
    schema = desert.schema(A)

    assert schema.load({"x": timestring}) == A(x=dt)


def test_concise_field_metadata() -> None:
    """Concisely create a dataclasses.Field with metadata."""

    @dataclasses.dataclass
    class A:
        x: datetime.datetime = desert.field(
            marshmallow.fields.NaiveDateTime(),
            metadata={"foo": 1},
        )

    timestring = "2019-10-21T10:25:00"
    dt = datetime.datetime(year=2019, month=10, day=21, hour=10, minute=25, second=00)
    schema = desert.schema(A)

    assert schema.load({"x": timestring}) == A(x=dt)
    assert dataclasses.fields(A)[0].metadata["foo"] == 1


def test_concise_attrib_metadata() -> None:
    """Concisely create an attr.ib() with metadata."""

    @attr.dataclass
    class A:
        x: datetime.datetime = desert.ib(
            marshmallow.fields.NaiveDateTime(), metadata={"foo": 1}
        )

    timestring = "2019-10-21T10:25:00"
    dt = datetime.datetime(year=2019, month=10, day=21, hour=10, minute=25, second=00)
    schema = desert.schema(A)

    assert schema.load({"x": timestring}) == A(x=dt)
    assert attr.fields(A).x.metadata["foo"] == 1


def test_non_init(module: DataclassModule) -> None:
    """Non-init attributes are not included in schema"""

    @module.dataclass
    class A:
        x: int
        y: str = module.field(default="can't init this", init=False)

    schema = desert.schema_class(A)()

    assert "y" not in schema.fields


def test_metadata_marshmallow_field_loads(module: DataclassModule) -> None:
    """Marshmallow field can be specified via metadata dict"""

    @module.dataclass
    class A:
        x: decimal.Decimal = module.field(
            metadata={"marshmallow_field": marshmallow.fields.Decimal(as_string=True)}
        )

    schema = desert.schema_class(A)()

    assert schema.loads('{"x": "1.3"}') == A(decimal.Decimal("1.3"))  # type: ignore[call-arg]


def test_get_field_default_raises_for_non_field() -> None:
    """Not attrs and not dataclasses field raises"""

    with pytest.raises(TypeError, match=re.escape("None")):
        desert._make._get_field_default(field=None)  # type: ignore[arg-type]


@pytest.mark.parametrize(argnames=["value"], argvalues=[["X"], [5]])
def test_union(
    module: DataclassModule,
    value: t.List[object],
    assert_dump_load: AssertLoadDumpProtocol,
) -> None:
    """Deserialize one of several types."""

    @module.dataclass
    class A:
        x: t.Union[int, str]

    schema = desert.schema_class(A)()

    dumped = {"x": value}
    loaded = A(value)  # type: ignore[call-arg]

    assert_dump_load(schema=schema, loaded=loaded, dumped=dumped)


def test_enum(
    module: DataclassModule,
    assert_dump_load: AssertLoadDumpProtocol,
) -> None:
    """Deserialize an enum object."""

    class Color(enum.Enum):
        RED = enum.auto()
        GREEN = enum.auto()

    @module.dataclass
    class A:
        x: Color

    schema = desert.schema_class(A)()
    dumped = {"x": "RED"}
    loaded = A(Color.RED)  # type: ignore[call-arg]

    assert_dump_load(schema=schema, loaded=loaded, dumped=dumped)


def test_tuple(
    module: DataclassModule,
    assert_dump_load: AssertLoadDumpProtocol,
) -> None:
    """Round trip a tuple.

    The tuple is converted to list only for dumps(), not during dump().
    """

    @module.dataclass
    class A:
        x: t.Tuple[int, bool]

    schema = desert.schema_class(A)()
    dumped = {"x": (1, False)}
    loaded = A(x=(1, False))  # type: ignore[call-arg]

    assert_dump_load(schema=schema, loaded=loaded, dumped=dumped)


def test_attr_factory() -> None:
    """Attrs default factory instantiates the factory type if no value is passed."""

    @attr.dataclass
    class A:
        x: t.List[int] = attr.ib(factory=list)

    data = desert.schema_class(A)().load({})
    assert data == A([])


def test_dataclasses_factory() -> None:
    """Dataclasses default factory instantiates the factory type if no value is passed."""

    @dataclasses.dataclass
    class A:
        x: t.List[int] = dataclasses.field(default_factory=list)

    data = desert.schema_class(A)().load({})
    assert data == A([])


def test_newtype(
    module: DataclassModule,
    assert_dump_load: AssertLoadDumpProtocol,
) -> None:
    """An instance of NewType delegates to its supertype."""

    MyInt = t.NewType("MyInt", int)

    @module.dataclass
    class A:
        x: MyInt

    schema = desert.schema_class(A)()
    dumped = {"x": 1}
    loaded = A(x=1)  # type: ignore[call-arg]

    assert_dump_load(schema=schema, loaded=loaded, dumped=dumped)


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Forward references and string annotations are broken. \n"
        + "See https://github.com/lovasoa/marshmallow_dataclass/issues/13"
    ),
)
def test_forward_reference(
    module: DataclassModule,
    assert_dump_load: AssertLoadDumpProtocol,
) -> None:  # pragma: no cover
    """Build schemas from classes that are defined below their containing class."""

    @module.dataclass
    class A:
        x: "B"

    @module.dataclass
    class B:
        y: int

    schema = desert.schema_class(A)()
    dumped = {"x": {"y": 1}}
    loaded = A((B(1)))  # type: ignore[call-arg]

    assert_dump_load(schema=schema, loaded=loaded, dumped=dumped)


@pytest.mark.xfail(
    # type ignored due to foss.heptapod.net/pypy/pypy/-/issues/3129
    condition=sys.implementation.name == "pypy" and sys.pypy_version_info < (7, 2),  # type: ignore[attr-defined]
    reason="Forward references and string annotations are broken in PyPy3 < 7.2",
    strict=True,
)
def test_forward_reference_module_scope() -> None:
    """Run the forward reference test at global scope."""

    import tests.cases.forward_reference  # pylint disable=unused-import,import-outside-toplevel


def test_non_string_metadata_key(module: DataclassModule) -> None:
    """A non-string key in the attrib metadata comes through in the mm field."""

    @module.dataclass
    class A:
        x: int = module.field(metadata={1: 2})

    field = desert.schema(A).fields["x"]
    assert field.metadata == {1: 2, desert._make._DESERT_SENTINEL: {}}


def test_non_optional_means_required(module: DataclassModule) -> None:
    """Non-optional fields are required."""

    @module.dataclass
    class A:
        x: int = module.field(metadata={1: 2})

    schema = desert.schema(A)

    with pytest.raises(marshmallow.exceptions.ValidationError):
        schema.load({})


def test_ignore_unknown_fields(module: DataclassModule) -> None:
    """Enable unknown fields with meta argument."""

    @module.dataclass
    class A:
        x: int

    schema_class = desert.schema_class(A, meta={"unknown": marshmallow.EXCLUDE})
    schema = schema_class()
    data = schema.load({"x": 1, "y": 2})
    assert data == A(x=1)  # type: ignore[call-arg]


def test_raise_unknown_type(module: DataclassModule) -> None:
    """Raise UnknownType for failed inferences."""

    @module.dataclass
    class A:
        x: list  # type: ignore[type-arg]

    with pytest.raises(desert.exceptions.UnknownType):
        desert.schema_class(A)


T = t.TypeVar("T")


class UnknownGeneric(t.Generic[T]):
    pass


@pytest.mark.skipif(
    sys.version_info[:2] <= (3, 6), reason="3.6 has isinstance(t.Sequence[int], type)."
)
def test_raise_unknown_generic(module: DataclassModule) -> None:
    """Raise UnknownType for unknown generics."""

    @module.dataclass
    class A:
        x: UnknownGeneric[int]

    with pytest.raises(desert.exceptions.UnknownType):
        desert.schema_class(A)


def test_tuple_ellipsis(module: DataclassModule) -> None:
    """Tuple with ellipsis allows variable length tuple.

    See :class:`typing.Tuple`.
    """

    @module.dataclass
    class A:
        x: t.Tuple[int, ...]

    schema = desert.schema_class(A)()
    dumped = {"x": (1, 2, 3)}
    loaded = A(x=(1, 2, 3))  # type: ignore[call-arg]

    actually_dumped = {"x": [1, 2, 3]}

    # TODO: how to use assert_dump_load?
    assert schema.load(dumped) == loaded
    assert schema.dump(loaded) == actually_dumped
    assert schema.loads(schema.dumps(loaded)) == loaded
    assert schema.dump(schema.load(actually_dumped)) == actually_dumped


def test_only() -> None:
    """only() extracts the only item in an iterable."""
    assert desert._make.only([1]) == 1


def test_only_raises() -> None:
    """only() raises if the iterable has an unexpected number of entries.'"""
    with pytest.raises(ValueError):
        desert._make.only([])

    with pytest.raises(ValueError):
        desert._make.only([1, 2])


def test_takes_self() -> None:
    """Attrs default factories are constructed after instance creation."""

    @attr.s
    class C:
        x: int = attr.ib()
        y: int = attr.ib()

        @y.default
        def _(self) -> int:
            return self.x + 1

    schema = desert.schema(C)
    assert schema.load({"x": 1}) == C(x=1, y=2)


def test_methods_not_on_schema(module: DataclassModule) -> None:
    """Dataclass methods are not copied to the schema."""

    @module.dataclass
    class A:
        def dataclass_method(self) -> None:
            """This method should not exist on the schema."""

    schema = desert.schema(A)
    sentinel = object()
    method = getattr(schema, "dataclass_method", sentinel)
    assert method is sentinel
