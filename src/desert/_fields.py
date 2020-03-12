import typing

import attr
import marshmallow.fields


T = typing.TypeVar("T")


@attr.s(frozen=True, auto_attribs=True)
class TypeTagField:
    cls: type
    tag: str
    field: marshmallow.fields.Field


@attr.s(auto_attribs=True)
class TypeDictRegistry:
    the_dict: typing.Dict[typing.Union[type, str], marshmallow.fields.Field,] = attr.ib(
        factory=dict
    )

    def register(self, cls, tag, field):
        if any(key in self.the_dict for key in [cls, tag]):
            raise Exception()

        type_tag_field = TypeTagField(cls=cls, tag=tag, field=field)

        self.the_dict[cls] = type_tag_field
        self.the_dict[tag] = type_tag_field

    # TODO: this type hinting...  doesn't help much as it could return
    #       another cls
    def __call__(self, tag: str, field: marshmallow.fields) -> typing.Callable[[T], T]:
        return lambda cls: self.register(cls=cls, tag=tag, field=field)

    def from_object(self, value):
        return self.the_dict[type(value)]

    def from_tag(self, tag):
        return self.the_dict[tag]


class AdjacentlyTaggedUnion(marshmallow.fields.Field):
    def __init__(
        self,
        *,
        from_object: typing.Callable[[typing.Any], TypeTagField],
        from_tag: typing.Callable[[str], TypeTagField],
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.from_object = from_object
        self.from_tag = from_tag

    def _deserialize(
        self,
        value: typing.Any,
        attr: typing.Optional[str],
        data: typing.Optional[typing.Mapping[str, typing.Any]],
        **kwargs,
    ) -> typing.Any:
        tag = value["type"]
        serialized_value = value["value"]

        if len(value) > 2:
            raise Exception()

        type_tag_field = self.from_tag(tag)
        field = type_tag_field.field()

        return field.deserialize(serialized_value)

    def _serialize(
        self, value: typing.Any, attr: str, obj: typing.Any, **kwargs,
    ) -> typing.Any:
        type_tag_field = self.from_object(value)
        field = type_tag_field.field()
        tag = type_tag_field.tag
        serialized_value = field.serialize(attr, obj)

        return {"type": tag, "value": serialized_value}
