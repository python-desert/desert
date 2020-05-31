import functools
import typing

import attr
import marshmallow.fields
import typeguard


T = typing.TypeVar("T")


@attr.s(frozen=True, auto_attribs=True)
class HintTagField:
    hint: typing.Any
    tag: str
    field: marshmallow.fields.Field


# class FieldRegistry(typing.Protocol):
#     def from_object(self, value: typing.Any) -> marshmallow.fields.Field:
#         ...
#
#     def from_tag(self, tag: str) -> marshmallow.fields.Field:
#         ...


@attr.s(auto_attribs=True)
class TypeDictFieldRegistry:
    the_dict: typing.Dict[typing.Union[type, str], marshmallow.fields.Field,] = attr.ib(
        factory=dict
    )

    def register(
        self, hint: typing.Any, tag: str, field: marshmallow.fields.Field,
    ) -> None:
        # TODO: just disabling for now to show more interesting test results
        # if any(key in self.the_dict for key in [cls, tag]):
        #     raise Exception()

        type_tag_field = HintTagField(hint=hint, tag=tag, field=field)

        self.the_dict[hint] = type_tag_field
        self.the_dict[tag] = type_tag_field

    # # TODO: this type hinting...  doesn't help much as it could return
    # #       another cls
    # def __call__(self, tag: str, field: marshmallow.fields) -> typing.Callable[[T], T]:
    #     return lambda cls: self.register(cls=cls, tag=tag, field=field)

    def from_object(self, value: typing.Any) -> marshmallow.fields.Field:
        return self.the_dict[type(value)]

    def from_tag(self, tag: str) -> marshmallow.fields.Field:
        return self.the_dict[tag]


@attr.s(auto_attribs=True)
class OrderedIsinstanceFieldRegistry:
    the_list: typing.List[HintTagField] = attr.ib(factory=list)
    by_tag: typing.Dict[str, HintTagField] = attr.ib(factory=dict)

    # TODO: but type bans from-scratch metatypes...  and protocols
    def register(
        self, hint: typing.Any, tag: str, field: marshmallow.fields.Field,
    ) -> None:
        # TODO: just disabling for now to show more interesting test results
        # if any(key in self.the_dict for key in [cls, tag]):
        #     raise Exception()

        type_tag_field = HintTagField(hint=hint, tag=tag, field=field)

        self.the_list.append(type_tag_field)
        self.by_tag[tag] = type_tag_field

    # # TODO: this type hinting...  doesn't help much as it could return
    # #       another cls
    # def __call__(self, tag: str, field: marshmallow.fields) -> typing.Callable[[T], T]:
    #     return lambda cls: self.register(cls=cls, tag=tag, field=field)

    def from_object(self, value: typing.Any) -> HintTagField:
        for type_tag_field in self.the_list:
            # if pytypes.is_of_type(value, type_tag_field.hint):
            try:
                typeguard.check_type(
                    argname="", value=value, expected_type=type_tag_field.hint,
                )
            except TypeError:
                continue

            return type_tag_field

        raise Exception()

    def from_tag(self, tag: str) -> HintTagField:
        return self.by_tag[tag]


@attr.s(auto_attribs=True)
class TaggedValue:
    tag: str
    value: typing.Any


def from_adjacently_tagged(item: typing.Any):
    tag = item.pop("type")
    serialized_value = item.pop("value")

    if len(item) > 0:
        raise Exception()

    return TaggedValue(tag=tag, value=serialized_value)


def to_adjacently_tagged(tag: str, value: typing.Any):
    return {"type": tag, "value": value}


class TaggedUnion(marshmallow.fields.Field):
    def __init__(
        self,
        *,
        from_object: typing.Callable[[typing.Any], HintTagField],
        from_tag: typing.Callable[[str], HintTagField],
        from_tagged: typing.Callable[[typing.Any], typing.Any],
        to_tagged: typing.Callable[[str, typing.Any], TaggedValue],
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.from_object = from_object
        self.from_tag = from_tag
        self.from_tagged = from_tagged
        self.to_tagged = to_tagged

    def _deserialize(
        self,
        value: typing.Any,
        attr: typing.Optional[str],
        data: typing.Optional[typing.Mapping[str, typing.Any]],
        **kwargs,
    ) -> typing.Any:
        tagged_value = self.from_tagged(item=value)

        type_tag_field = self.from_tag(tagged_value.tag)
        field = type_tag_field.field

        return field.deserialize(tagged_value.value)

    def _serialize(
        self, value: typing.Any, attr: str, obj: typing.Any, **kwargs,
    ) -> typing.Any:
        type_tag_field = self.from_object(value)
        field = type_tag_field.field
        tag = type_tag_field.tag
        serialized_value = field.serialize(attr, obj)

        return self.to_tagged(tag=tag, value=serialized_value)


@functools.wraps(TaggedUnion)
def adjacently_tagged_union(*args, **kwargs):
    return TaggedUnion(
        *args,
        from_tagged=from_adjacently_tagged,
        to_tagged=to_adjacently_tagged,
        **kwargs,
    )
