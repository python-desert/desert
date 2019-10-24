import dataclasses
import typing as t

import attr
import marshmallow

import desert._make


def schema(cls: t.Type, many: bool = False) -> marshmallow.Schema:
    """Build a marshmallow schema *instance* for the class.
    """
    return desert._make.class_schema(cls)(many=many)


def schema_class(cls: t.Type) -> t.Type[marshmallow.Schema]:
    """Build a marshmallow schema *class* for the class.
    """
    return desert._make.class_schema(cls)


def metadata(
    field: marshmallow.fields.Field
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
    return dataclasses.field(**kw, metadata=metadata(marshmallow_field))


def ib(marshmallow_field: marshmallow.fields.Field, **kw) -> attr._make._CountingAttr:
    """Specify a marshmallow field in the metadata for an ``attr.dataclass``.

    .. code-block:: python

        @attr.dataclass
        class A:
            x: int = desert.ib(marshmallow.fields.Int())
    """
    return attr.ib(**kw, metadata=metadata(marshmallow_field))
