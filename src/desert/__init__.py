import dataclasses
import typing as t

import attr
import marshmallow

import desert._make
import desert._version


if t.TYPE_CHECKING:
    import attr._make


def schema(
    cls: t.Type, many: bool = False, meta: t.Dict[str, t.Any] = {}
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
    cls: t.Type, meta: t.Dict[str, t.Any] = {}
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
) -> t.Dict["desert._make._DesertSentinel", t.Dict[t.Any, marshmallow.fields.Field]]:
    """Specify a marshmallow field in the field metadata.

    .. code-block:: python

        x: int = attr.ib(metadata=desert.metadata(marshmallow.fields.Int()))
    """
    return {desert._make._DESERT_SENTINEL: {"marshmallow_field": field}}


def field(marshmallow_field: marshmallow.fields.Field, **kw) -> dataclasses.Field:
    """Specify a marshmallow field in the metadata for a ``dataclasses.dataclass``.

    .. code-block:: python

        @dataclasses.dataclass
        class A:
            x: int = desert.field(marshmallow.fields.Int())
    """
    meta = metadata(marshmallow_field)
    meta.update(kw.pop("metadata", {}))
    # typeshed hints it as Mapping[str, Any] without any obvious reason
    # https://github.com/python/typeshed/blob/95a45eb4abd0c25849268983cb614e3bf6b9b264/stdlib/dataclasses.pyi#L81
    # https://github.com/python/typeshed/pull/5823
    return dataclasses.field(**kw, metadata=meta)  # type: ignore[arg-type]


def ib(marshmallow_field: marshmallow.fields.Field, **kw) -> attr._make._CountingAttr:
    """Specify a marshmallow field in the metadata for an ``attr.dataclass``.

    .. code-block:: python

        @attr.dataclass
        class A:
            x: int = desert.ib(marshmallow.fields.Int())
    """
    meta = metadata(marshmallow_field)
    meta.update(kw.pop("metadata", {}))
    return attr.ib(**kw, metadata=meta)


__version__ = desert._version.__version__
