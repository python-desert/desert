import collections
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
    the_dict: typing.Dict[
        typing.Union[type, str],
        marshmallow.fields.Field,
    ] = attr.ib(factory=dict)

    def register(
        self,
        hint: typing.Any,
        tag: str,
        field: marshmallow.fields.Field,
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
        self,
        hint: typing.Any,
        tag: str,
        field: marshmallow.fields.Field,
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
        scores = {}

        for type_tag_field in self.the_list:
            score = 0

            # if pytypes.is_of_type(value, type_tag_field.hint):
            try:
                typeguard.check_type(
                    argname="",
                    value=value,
                    expected_type=type_tag_field.hint,
                )
            except TypeError:
                pass
            else:
                score += 2

            try:
                if isinstance(value, type_tag_field.hint):
                    score += 3
            except TypeError:
                pass

            if score > 0:
                # Only use this to disambiguate between already selected options such
                # as ["a", "b"] matching both typing.List[str] and typing.Sequence[str].
                # This only works properly on 3.7+.
                try:
                    if type(value) == type_tag_field.hint.__origin__:
                        score += 1
                except (AttributeError, TypeError):
                    pass

            scores[type_tag_field] = score

        high_score = max(scores.values())

        if high_score == 0:
            raise Exception("No matching type hints found")

        potential = [ttf for ttf, score in scores.items() if score == high_score]

        if len(potential) != 1:
            raise Exception(
                "Unique matching type hint not found: {}".format(
                    ", ".join(str(p.hint) for p in potential),
                )
            )

        [type_tag_field] = potential

        return type_tag_field

    def from_tag(self, tag: str) -> HintTagField:
        return self.by_tag[tag]


@attr.s(auto_attribs=True)
class TaggedValue:
    tag: str
    value: typing.Any


class TaggedUnion(marshmallow.fields.Field):
    def __init__(
        self,
        *,
        from_object: typing.Callable[[typing.Any], HintTagField],
        from_tag: typing.Callable[[str], HintTagField],
        from_tagged: typing.Callable[[typing.Any], TaggedValue],
        to_tagged: typing.Callable[[str, typing.Any], typing.Any],
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
        self,
        value: typing.Any,
        attr: str,
        obj: typing.Any,
        **kwargs,
    ) -> typing.Any:
        type_tag_field = self.from_object(value)
        field = type_tag_field.field
        tag = type_tag_field.tag
        serialized_value = field.serialize(attr, obj)

        return self.to_tagged(tag=tag, value=serialized_value)


default_tagged_type_key = "#type"
default_tagged_value_key = "#value"


def from_externally_tagged(item: typing.Any):
    [[tag, serialized_value]] = item.items()

    return TaggedValue(tag=tag, value=serialized_value)


def to_externally_tagged(tag: str, value: typing.Any):
    return {tag: value}


@functools.wraps(TaggedUnion)
def externally_tagged_union(*args, **kwargs):
    return TaggedUnion(
        *args,
        from_tagged=from_externally_tagged,
        to_tagged=to_externally_tagged,
        **kwargs,
    )


def from_internally_tagged(item: typing.Any, type_key: str):
    return TaggedValue(
        tag=item[type_key], value={k: v for k, v in item.items() if k != type_key}
    )


def to_internally_tagged(tag: str, value: typing.Any, type_key: str):
    if type_key in value:
        raise Exception()

    return {type_key: tag, **value}


@functools.wraps(TaggedUnion)
def internally_tagged_union(*args, type_key=default_tagged_type_key, **kwargs):
    return TaggedUnion(
        *args,
        from_tagged=functools.partial(from_internally_tagged, type_key=type_key),
        to_tagged=functools.partial(to_internally_tagged, type_key=type_key),
        **kwargs,
    )


def from_adjacently_tagged(item: typing.Any, type_key: str, value_key: str):
    tag = item.pop(type_key)
    serialized_value = item.pop(value_key)

    if len(item) > 0:
        raise Exception()

    return TaggedValue(tag=tag, value=serialized_value)


def to_adjacently_tagged(tag: str, value: typing.Any, type_key: str, value_key: str):
    return {type_key: tag, value_key: value}


@functools.wraps(TaggedUnion)
def adjacently_tagged_union(
    *args,
    type_key=default_tagged_type_key,
    value_key=default_tagged_value_key,
    **kwargs,
):
    return TaggedUnion(
        *args,
        from_tagged=functools.partial(
            from_adjacently_tagged, type_key=type_key, value_key=value_key
        ),
        to_tagged=functools.partial(
            to_adjacently_tagged, type_key=type_key, value_key=value_key
        ),
        **kwargs,
    )
