import typing

import attr
import marshmallow.fields

# import pytypes
import typeguard


T = typing.TypeVar("T")


@attr.s(frozen=True, auto_attribs=True)
class HintTagField:
    hint: typing.Any
    tag: str
    field: marshmallow.fields.Field


class FieldRegistry(typing.Protocol):
    def from_object(self, value: typing.Any) -> marshmallow.fields.Field:
        ...

    def from_tag(self, tag: str) -> marshmallow.fields.Field:
        ...


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
            if isinstance(value, type_tag_field.cls):
                return type_tag_field

        raise Exception()

    def from_tag(self, tag: str) -> HintTagField:
        return self.by_tag[tag]


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


class AdjacentlyTaggedUnion(marshmallow.fields.Field):
    def __init__(
        self,
        *,
        from_object: typing.Callable[[typing.Any], HintTagField],
        from_tag: typing.Callable[[str], HintTagField],
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
        field = type_tag_field.field

        return field.deserialize(serialized_value)

    def _serialize(
        self, value: typing.Any, attr: str, obj: typing.Any, **kwargs,
    ) -> typing.Any:
        type_tag_field = self.from_object(value)
        field = type_tag_field.field
        tag = type_tag_field.tag
        serialized_value = field.serialize(attr, obj)

        return {"type": tag, "value": serialized_value}
