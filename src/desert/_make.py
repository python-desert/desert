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
      Schema: ClassVar[Type[Schema]] = Schema # For the type checker
"""

__all__ = ("schema_class", "schema")

import dataclasses
import datetime
import decimal
import inspect
import typing
import uuid
from enum import Enum
from enum import EnumMeta
from typing import Any
from typing import ClassVar
from typing import Dict
from typing import List
from typing import Mapping
from typing import NewType
from typing import Optional
from typing import Tuple
from typing import Type
from typing import Union
from typing import cast

import attr
import marshmallow
import typing_inspect

import desert.exceptions


__all__ = ["dataclass", "add_schema", "class_schema", "field_for_schema"]

NoneType = type(None)


def class_schema(clazz: type) -> Type[marshmallow.Schema]:
    """
    Convert a class to a marshmallow schema
    :param clazz: A python class (may be a dataclass)
    :return: A marshmallow Schema corresponding to the dataclass
    .. note::
        All the arguments supported by marshmallow field classes are can
        be passed in the `metadata` dictionary of a field.
    If you want to use a custom marshmallow field
    (one that has no equivalent python type), you can pass it as the
    ``marshmallow_field`` key in the metadata dictionary.
    >>> @dataclasses.dataclass()
    ... class Person:
    ...   name: str = dataclasses.field(default="Anonymous")
    ...   friends: List['Person'] = dataclasses.field(default_factory=lambda:[]) # Recursive field
    ...
    >>> person = class_schema(Person)().load({
    ...     "friends": [{"name": "Roger Boucher"}]
    ... })
    >>> person
    Person(name='Anonymous', friends=[Person(name='Roger Boucher', friends=[])])
    >>> @dataclasses.dataclass()
    ... class C:
    ...   important: int = dataclasses.field(init=True, default=0)
    ...   unimportant: int = dataclasses.field(init=False, default=0) # Only fields that are in the __init__ method will be added:
    ...
    >>> c = class_schema(C)().load({
    ...     "important": 9, # This field will be imported
    ...     "unimportant": 9 # This field will NOT be imported
    ... }, unknown=marshmallow.EXCLUDE)
    >>> c
    C(important=9, unimportant=0)
    >>> @dataclasses.dataclass
    ... class Website:
    ...  url:str = dataclasses.field(metadata = {'clout': {
    ...    "marshmallow_field": marshmallow.fields.Url() # Custom marshmallow field
    ...  }})
    ...
    """

    fields: Union[Tuple[dataclasses.Field], Tuple[attr.Attribute]]
    if dataclasses.is_dataclass(clazz):
        fields = dataclasses.fields(clazz)
    elif attr.has(clazz):
        fields = attr.fields(clazz)
    else:
        raise desert.exceptions.NotAnAttrsClassOrDataclass(clazz)

    # Copy all public members of the dataclass to the schema
    attributes = {k: v for k, v in inspect.getmembers(clazz) if not k.startswith("_")}
    # Update the schema members to contain marshmallow fields instead of dataclass fields

    hints = typing.get_type_hints(clazz)
    for field in fields:
        if field.init:
            attributes[field.name] = field_for_schema(
                hints.get(field.name, field.type),
                _get_field_default(field),
                field.metadata,
            )

    cls_schema = type(clazz.__name__, (_base_schema(clazz),), attributes)

    return cast(Type[marshmallow.Schema], cls_schema)


_native_to_marshmallow: Dict[type, Type[marshmallow.fields.Field]] = {
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
    Any: marshmallow.fields.Raw,
}


def field_for_schema(
    typ: type, default=marshmallow.missing, metadata: Mapping[str, Any] = None
) -> marshmallow.fields.Field:
    """
    Get a marshmallow Field corresponding to the given python type.
    The metadata of the dataclass field is used as arguments to the marshmallow Field.
    >>> int_field = field_for_schema(int, default=9, metadata=dict(required=True))
    >>> int_field.__class__
    <class 'marshmallow.fields.Integer'>

    >>> int_field.default
    9
    >>> field_for_schema(Dict[str,str]).__class__
    <class 'marshmallow.fields.Dict'>
    >>> field_for_schema(Optional[str]).__class__
    <class 'marshmallow.fields.String'>
    >>> import marshmallow_enum
    >>> field_for_schema(Enum("X", "a b c")).__class__
    <class 'marshmallow_enum.EnumField'>
    >>> import typing
    >>> field_for_schema(typing.Union[int,str]).__class__
    <class 'marshmallow_union.Union'>
    >>> field_for_schema(NewType('UserId', int)).__class__
    <class 'marshmallow.fields.Integer'>
    >>> field_for_schema(NewType('UserId', int), default=0).default
    0
    >>> class Color(Enum):
    ...   red = 1
    >>> field_for_schema(Color).__class__
    <class 'marshmallow_enum.EnumField'>
    >>> field_for_schema(Any).__class__
    <class 'marshmallow.fields.Raw'>
    """

    if metadata is None:
        metadata = {}
    else:
        metadata = dict(metadata)

    desert_metadata = dict(metadata).get(_DESERT_SENTINEL, {})
    metadata[_DESERT_SENTINEL] = desert_metadata

    if default is not marshmallow.missing:
        desert_metadata.setdefault("default", default)
        if not desert_metadata.get(
            "required"
        ):  # 'missing' must not be set for required fields.
            desert_metadata.setdefault("missing", default)

    field = None

    # If the field was already defined by the user
    predefined_field = desert_metadata.get("marshmallow_field")

    if predefined_field:
        field = predefined_field
        field.metadata.update(metadata)
        return field

    # Base types
    if not field and typ in _native_to_marshmallow:
        field = _native_to_marshmallow[typ](default=default)

    # Generic types
    origin = typing_inspect.get_origin(typ)
    if origin:
        arguments = typing_inspect.get_args(typ, True)
        if origin in (list, List):
            field = marshmallow.fields.List(field_for_schema(arguments[0]))
        if origin in (tuple, Tuple):
            field = marshmallow.fields.Tuple(
                tuple(field_for_schema(arg) for arg in arguments)
            )
        elif origin in (dict, Dict):
            field = marshmallow.fields.Dict(
                keys=field_for_schema(arguments[0]),
                values=field_for_schema(arguments[1]),
            )
        elif typing_inspect.is_optional_type(typ):
            subtyp = next(t for t in arguments if t is not NoneType)
            # Treat optional types as types with a None default
            metadata[_DESERT_SENTINEL]["default"] = metadata.get("default", None)
            metadata[_DESERT_SENTINEL]["missing"] = metadata.get("missing", None)
            metadata[_DESERT_SENTINEL]["required"] = False

            field = field_for_schema(subtyp, metadata=metadata, default=None)
            field.default = None
            field.missing = None

        elif typing_inspect.is_union_type(typ):
            subfields = [field_for_schema(subtyp) for subtyp in arguments]
            import marshmallow_union

            field = marshmallow_union.Union(subfields)

    # typing.NewType returns a function with a __supertype__ attribute
    newtype_supertype = getattr(typ, "__supertype__", None)
    if newtype_supertype and inspect.isfunction(typ):
        metadata.setdefault("description", typ.__name__)
        field = field_for_schema(newtype_supertype, default=default)

    # enumerations
    if type(typ) is EnumMeta:
        import marshmallow_enum

        field = marshmallow_enum.EnumField(typ, metadata=metadata)

    # Nested dataclasses
    forward_reference = getattr(typ, "__forward_arg__", None)

    if field is None:
        nested = forward_reference or class_schema(typ)
        try:
            nested.help = typ.__doc__
        except AttributeError:
            # TODO need to handle the case where nested is a string forward reference.
            pass
        field = marshmallow.fields.Nested(nested)

    field.metadata.update(metadata)

    for key in ["default", "missing", "required", "marshmallow_field"]:
        if key in metadata.keys():
            metadata[_DESERT_SENTINEL][key] = metadata.pop(key)

    return field


def _base_schema(clazz: type) -> Type[marshmallow.Schema]:
    class BaseSchema(marshmallow.Schema):
        @marshmallow.post_load
        def make_data_class(self, data, **_):
            return clazz(**data)

    return BaseSchema


def _get_field_default(field: Union[dataclasses.Field, attr.Attribute]):
    """
    Return a marshmallow default value given a dataclass default value
    >>> _get_field_default(dataclasses.field())
    <marshmallow.missing>
    """
    if isinstance(field, dataclasses.Field):
        if field.default_factory != dataclasses.MISSING:
            return field.default_factory
        elif field.default is dataclasses.MISSING:
            return marshmallow.missing
        return field.default
    elif isinstance(field, attr.Attribute):
        if field.default == attr.NOTHING:
            return marshmallow.missing
        if isinstance(field.default, attr.Factory):
            if field.default.takes_self:
                raise NotImplementedError("Takes self not implemented")
            return field.default.factory
        return field.default
    else:
        raise TypeError(field)


def sentinel(name):
    return attr.make_class(name, [], frozen=True)()


_DESERT_SENTINEL = sentinel("_DesertSentinel")
