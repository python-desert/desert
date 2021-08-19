import dataclasses
import typing as t

import attr
import marshmallow

import desert._make
import desert._version


if t.TYPE_CHECKING:
    import attr._make


T = t.TypeVar("T")


def schema(
    cls: type, many: bool = False, meta: t.Dict[str, t.Any] = {}
) -> marshmallow.Schema:
    """Build a marshmallow schema *instance* for the class.

    Args:
        cls: A type-hinted attrs class or dataclass.
        meta: The schema's Meta class will be built from this dict.
              Use values from :class:`marshmallow.Schema.Meta`.

    Returns:
        An instance of the marshmallow schema for the class.
    """
    return desert._make.class_schema(cls, meta=meta)(many=many)


def schema_class(
    cls: type, meta: t.Dict[str, t.Any] = {}
) -> t.Type[marshmallow.Schema]:
    """Build a marshmallow schema *class* for the class.

    Args:
        cls: A type-hinted attrs class or dataclass.
        meta: The schema's Meta class will be built from this dict.
              Use values from :class:`marshmallow.Schema.Meta`.

    Returns:
        The marshmallow schema class.
    """
    return desert._make.class_schema(cls, meta=meta)


def metadata(
    field: marshmallow.fields.Field,
) -> t.Dict[object, object]:
    """Specify a marshmallow field in the field metadata.

    .. code-block:: python

        x: int = attr.ib(metadata=desert.metadata(marshmallow.fields.Int()))
    """
    return {desert._make._DESERT_SENTINEL: {"marshmallow_field": field}}


# TODO: maybe deprecate and rename metadata()
create_metadata = metadata


# These overloads lie about their return type just as both attrs and dataclasses
# do so as to support the normal usage of `attribute: int = field()`
@t.overload
def field(
    marshmallow_field: marshmallow.fields.Field,
    *,
    default: T,
    metadata: t.Mapping[object, object] = {},
    **kw: object,
) -> T:
    ...


@t.overload
def field(
    marshmallow_field: marshmallow.fields.Field,
    *,
    default_factory: t.Callable[[], T],
    metadata: t.Mapping[object, object] = {},
    **kw: object,
) -> T:
    ...


@t.overload
def field(
    marshmallow_field: marshmallow.fields.Field,
    *,
    metadata: t.Mapping[object, object] = {},
    **kw: object,
) -> t.Any:
    ...


# The return type hint of Any is certainly a lie but fits a lot better with
# the normal use of `x: int = desert.field()`.  Both dataclasses and attrs
# prioritize hinting for this usage as well.  Perhaps someday we'll have a
# plugin that indicates the actual type.
def field(
    marshmallow_field: marshmallow.fields.Field,
    metadata: t.Mapping[object, object] = {},
    **kw: object,
) -> t.Any:
    """Specify a marshmallow field in the metadata for a ``dataclasses.dataclass``.

    .. code-block:: python

        @dataclasses.dataclass
        class A:
            x: int = desert.field(marshmallow.fields.Int())
    """
    meta: t.Dict[object, object] = create_metadata(marshmallow_field)
    meta.update(metadata)

    # call-overload and new_field intermediary:
    #   https://github.com/python/typeshed/pull/5823
    new_field: dataclasses.Field[object] = dataclasses.field(**kw, metadata=meta)  # type: ignore[call-overload]
    return new_field


# These overloads lie about their return type just as both attrs and dataclasses
# do so as to support the normal usage of `attribute: int = field()`
@t.overload
def ib(
    marshmallow_field: marshmallow.fields.Field,
    *,
    default: t.Union[T, t.Callable[[], T]],
    metadata: t.Mapping[object, object] = {},
    **kw: object,
) -> T:
    ...


@t.overload
def ib(
    marshmallow_field: marshmallow.fields.Field,
    *,
    factory: t.Callable[[], T],
    metadata: t.Mapping[object, object] = {},
    **kw: object,
) -> T:
    ...


@t.overload
def ib(
    marshmallow_field: marshmallow.fields.Field,
    *,
    metadata: t.Mapping[object, object] = {},
    **kw: object,
) -> t.Any:
    ...


# The return type hint of Any is certainly a lie but fits a lot better with
# the normal use of `x: int = desert.ib()`.  Both dataclasses and attrs
# prioritize hinting for this usage as well.  Perhaps someday we'll have a
# plugin that indicates the actual type.
def ib(
    marshmallow_field: marshmallow.fields.Field,
    metadata: t.Mapping[object, object] = {},
    **kw: object,
) -> t.Any:
    """Specify a marshmallow field in the metadata for an ``attr.dataclass``.

    .. code-block:: python

        @attr.dataclass
        class A:
            x: int = desert.ib(marshmallow.fields.Int())
    """
    meta: t.Dict[object, object] = create_metadata(marshmallow_field)
    meta.update(metadata)
    new_field: attr._make._CountingAttr = attr.ib(**kw, metadata=meta)  # type: ignore[call-overload]
    return new_field


__version__ = desert._version.__version__
