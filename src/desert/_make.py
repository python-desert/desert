# MIT License

# Desert
# Copyright (c) 2019 Desert contributors

# With sections from marshmallow_dataclass
# Copyright (c) 2019 Ophir LOJKINE

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


"""
This library allows the conversion of python 3.7's :mod:`dataclasses`
to :mod:`marshmallow` schemas.
It takes a python class, and generates a marshmallow schema for it.
Simple example::
    from marshmallow import Schema
    from marshmallow_dataclass import dataclass
    @dataclass
    class Point:
      x:float
      y:float
    point = Point(x=0, y=0)
    point_json = Point.Schema().dumps(point)
Full example::
    from marshmallow import Schema
    from dataclasses import field
    from marshmallow_dataclass import dataclass
    import datetime
    @dataclass
    class User:
      birth: datetime.date = field(metadata= {
        "required": True # A parameter to pass to marshmallow's field
      })
      website:str = field(metadata = {
        "marshmallow_field": marshmallow.fields.Url() # Custom marshmallow field
      })
      Schema: t.ClassVar[Type[Schema]] = Schema # For the type checker
"""

import collections.abc
import dataclasses
import datetime
import decimal
import enum
import inspect
import typing as t
import uuid

import attr
import marshmallow
import typing_inspect

import desert.exceptions


__all__ = ["dataclass", "add_schema", "class_schema", "field_for_schema"]

NoneType = type(None)
T = t.TypeVar("T")


def class_schema(
    clazz: type, meta: t.Dict[str, t.Any] = {}
) -> t.Type[marshmallow.Schema]:
    """
    Convert a class to a marshmallow schema.

    Args:
        clazz: A python class (may be a dataclass)
        meta: The marshmallow schema metadata dict.

    Returns:
        A :class:`marshmallow.Schema` type corresponding to the dataclass.

    .. note::
        All the arguments supported by marshmallow field classes are can
        be passed in the `metadata` dictionary of a field.

    If you want to use a custom marshmallow field
    (one that has no equivalent python type), you can pass it as the
    ``marshmallow_field`` key in the metadata dictionary.
    """

    fields: t.Union[
        t.Tuple[dataclasses.Field[object], ...], t.Tuple[attr.Attribute[object], ...]
    ]

    if not isinstance(clazz, type):
        raise desert.exceptions.UnknownType(
            f"Desert failed to infer the field type for {clazz}.\n"
            + "Explicitly pass a Marshmallow field type."
        )
    if dataclasses.is_dataclass(clazz):
        fields = dataclasses.fields(clazz)
    elif attr.has(clazz):
        fields = attr.fields(clazz)
    elif issubclass(clazz, (list, dict)):
        raise desert.exceptions.UnknownType(
            "Use parametrized generics like t.List[int] or t.Dict[str, int] "
            f"instead of list and dict. Got {clazz}."
        )
    else:
        raise desert.exceptions.NotAnAttrsClassOrDataclass(clazz)

    # Update the schema members to contain marshmallow fields instead of dataclass fields.
    attributes: t.Dict[str, marshmallow.fields.Field] = {}
    hints = t.get_type_hints(clazz)
    for field in fields:
        if field.init:
            attributes[field.name] = field_for_schema(
                hints.get(field.name, field.type),
                _get_field_default(field),
                field.metadata,
            )

    class_attributes: t.Dict[str, t.Any] = {
        **attributes,
        "Meta": type("Meta", (), meta),
    }

    cls_schema = type(
        clazz.__name__,
        (_base_schema(clazz),),
        class_attributes,
    )

    return t.cast(t.Type[marshmallow.Schema], cls_schema)


_native_to_marshmallow: t.Dict[
    t.Union[type, t.Any], t.Type[marshmallow.fields.Field]
] = {
    int: marshmallow.fields.Integer,
    float: marshmallow.fields.Float,
    str: marshmallow.fields.String,
    bool: marshmallow.fields.Boolean,
    datetime.datetime: marshmallow.fields.DateTime,
    datetime.time: marshmallow.fields.Time,
    datetime.timedelta: marshmallow.fields.TimeDelta,
    datetime.date: marshmallow.fields.Date,
    decimal.Decimal: marshmallow.fields.Decimal,
    uuid.UUID: marshmallow.fields.UUID,
    t.Any: marshmallow.fields.Raw,
}


class VariadicTuple(marshmallow.fields.List):
    """Homogenous tuple with variable number of entries."""

    def _deserialize(self, *args: object, **kwargs: object) -> t.Tuple[object, ...]:  # type: ignore[override]
        return tuple(super()._deserialize(*args, **kwargs))


def only(items: t.Iterable[T]) -> T:
    """Return the only item in an iterable or raise ValueError."""
    [x] = items
    return x


def field_for_schema(
    typ: type,
    default: object = marshmallow.missing,
    metadata: t.Optional[t.Mapping[t.Any, t.Any]] = None,
) -> marshmallow.fields.Field:
    """
    Get a marshmallow Field corresponding to the given python type.
    The metadata of the dataclass field is used as arguments to the marshmallow Field.
    >>> int_field = field_for_schema(int, default=9, metadata=dict(required=True))
    >>> int_field.__class__
    <class 'marshmallow.fields.Integer'>

    >>> int_field.dump_default
    9
    >>> field_for_schema(t.Dict[str,str]).__class__
    <class 'marshmallow.fields.Dict'>
    >>> field_for_schema(t.Optional[str]).__class__
    <class 'marshmallow.fields.String'>
    >>> import marshmallow_enum
    >>> field_for_schema(enum.Enum("X", "a b c")).__class__
    <class 'marshmallow_enum.EnumField'>
    >>> import typing
    >>> field_for_schema(t.Union[int,str]).__class__
    <class 'marshmallow_union.Union'>
    >>> field_for_schema(t.NewType('UserId', int)).__class__
    <class 'marshmallow.fields.Integer'>
    >>> field_for_schema(t.NewType('UserId', int), default=0).dump_default
    0
    >>> class Color(enum.Enum):
    ...   red = 1
    >>> field_for_schema(Color).__class__
    <class 'marshmallow_enum.EnumField'>
    >>> field_for_schema(t.Any).__class__
    <class 'marshmallow.fields.Raw'>
    """

    if metadata is None:
        metadata = {}
    else:
        metadata = dict(metadata)

    desert_metadata = dict(metadata).get(_DESERT_SENTINEL, {})
    metadata[_DESERT_SENTINEL] = desert_metadata

    if default is not marshmallow.missing:
        desert_metadata.setdefault("dump_default", default)
        desert_metadata.setdefault("allow_none", True)
        desert_metadata.setdefault("load_default", default)

    field = None

    # If the field was already defined by the user
    predefined_field = t.cast(
        marshmallow.fields.Field, desert_metadata.get("marshmallow_field")
    )

    if predefined_field:
        field = predefined_field
        field.metadata.update(metadata)
        return field

    # Base types
    if not field and typ in _native_to_marshmallow:
        field = _native_to_marshmallow[typ](dump_default=default)

    # Generic types
    origin = typing_inspect.get_origin(typ)

    if origin:
        arguments = typing_inspect.get_args(typ, True)

        if origin in (
            list,
            t.List,
            t.Sequence,
            t.MutableSequence,
            collections.abc.Sequence,
            collections.abc.MutableSequence,
        ):
            field = marshmallow.fields.List(field_for_schema(arguments[0]))

        if origin in (tuple, t.Tuple) and Ellipsis not in arguments:
            field = marshmallow.fields.Tuple(  # type: ignore[no-untyped-call]
                tuple(field_for_schema(arg) for arg in arguments)
            )
        elif origin in (tuple, t.Tuple) and Ellipsis in arguments:

            field = VariadicTuple(
                field_for_schema(only(arg for arg in arguments if arg != Ellipsis))
            )
        elif origin in (
            dict,
            t.Dict,
            t.Mapping,
            t.MutableMapping,
            collections.abc.Mapping,
            collections.abc.MutableMapping,
        ):
            field = marshmallow.fields.Dict(
                keys=field_for_schema(arguments[0]),
                values=field_for_schema(arguments[1]),
            )
        elif typing_inspect.is_optional_type(typ):
            [subtyp] = (t for t in arguments if t is not NoneType)
            # Treat optional types as types with a None default
            metadata[_DESERT_SENTINEL]["dump_default"] = metadata.get(
                "dump_default", None
            )
            metadata[_DESERT_SENTINEL]["load_default"] = metadata.get(
                "load_default", None
            )
            metadata[_DESERT_SENTINEL]["required"] = False

            field = field_for_schema(subtyp, metadata=metadata, default=None)
            field.dump_default = None
            field.load_default = None
            field.allow_none = True

        elif typing_inspect.is_union_type(typ):
            subfields = [field_for_schema(subtyp) for subtyp in arguments]
            import marshmallow_union

            field = marshmallow_union.Union(subfields)

    # t.NewType returns a function with a __supertype__ attribute
    newtype_supertype = getattr(typ, "__supertype__", None)
    if newtype_supertype and inspect.isfunction(typ):
        metadata.setdefault("description", typ.__name__)
        field = field_for_schema(newtype_supertype, default=default)

    # enumerations
    if type(typ) is enum.EnumMeta:
        import marshmallow_enum

        field = marshmallow_enum.EnumField(typ, metadata=metadata)

    # Nested dataclasses
    forward_reference = getattr(typ, "__forward_arg__", None)

    if field is None:
        nested = forward_reference or class_schema(typ)
        field = marshmallow.fields.Nested(nested)

    field.metadata.update(metadata)

    for key in ["dump_default", "load_default", "required", "marshmallow_field"]:
        if key in metadata.keys():
            metadata[_DESERT_SENTINEL][key] = metadata.pop(key)

    if field.dump_default == field.load_default == default == marshmallow.missing:
        field.required = True

    return field


def _base_schema(clazz: type) -> t.Type[marshmallow.Schema]:
    class BaseSchema(marshmallow.Schema):
        @marshmallow.post_load
        def make_data_class(self, data: t.Mapping[str, object], **_: object) -> object:
            return clazz(**data)

    return BaseSchema


def _get_field_default(
    # field: t.Union[dataclasses.Field[object], "attr.Attribute[object]"],
    field: t.Union["dataclasses.Field[object]", "attr.Attribute[object]"],
) -> object:
    """
    Return a marshmallow default value given a dataclass default value
    >>> _get_field_default(dataclasses.field())
    <marshmallow.missing>
    """
    if isinstance(field, dataclasses.Field):
        # misc: https://github.com/python/mypy/issues/10750
        # comparison-overlap: https://github.com/python/typeshed/pull/5900
        if field.default_factory != dataclasses.MISSING:
            return dataclasses.MISSING
        if field.default is dataclasses.MISSING:
            return marshmallow.missing
        return field.default
    elif isinstance(field, attr.Attribute):
        if field.default == attr.NOTHING:
            return marshmallow.missing
        if isinstance(field.default, attr.Factory):  # type: ignore[arg-type]
            # attrs specifically doesn't support this so as to support the
            # primary use case.
            # https://github.com/python-attrs/attrs/blob/38580632ceac1cd6e477db71e1d190a4130beed4/src/attr/__init__.pyi#L63-L65
            if field.default.takes_self:  # type: ignore[attr-defined]
                return attr.NOTHING
            return field.default.factory  # type: ignore[attr-defined]
        return field.default
    else:
        raise TypeError(field)


@attr.frozen
class _DesertSentinel:
    pass


_DESERT_SENTINEL = _DesertSentinel()
