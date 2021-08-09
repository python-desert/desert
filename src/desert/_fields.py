import functools
import typing

import attr
import marshmallow.fields
import typeguard
import typing_extensions

import desert._util
import desert.exceptions


T = typing.TypeVar("T")


@attr.s(frozen=True, auto_attribs=True)
class HintTagField:
    """Serializing and deserializing a given piece of data requires a group of
    information.  A type hint that matches the data to be serialized, a Marshmallow
    field that knows how to serialize and deserialize the data, and a string tag to
    label the serialized data for deserialization.  This is that group...  There
    must be a better name.
    """

    hint: typing.Any
    tag: str
    field: marshmallow.fields.Field


class FieldRegistry(typing_extensions.Protocol):
    def register(
        self,
        hint: typing.Any,
        tag: str,
        field: marshmallow.fields.Field,
    ) -> None:
        ...

    @property
    def from_object(self) -> "FromObjectProtocol":
        ...

    @property
    def from_tag(self) -> "FromTagProtocol":
        ...


check_field_registry_protocol = desert._util.ProtocolChecker[FieldRegistry]()


# @attr.s(auto_attribs=True)
# class TypeDictFieldRegistry:
#     the_dict: typing.Dict[
#         typing.Union[type, str],
#         HintTagField,
#     ] = attr.ib(factory=dict)
#
#     def register(
#         self,
#         hint: typing.Any,
#         tag: str,
#         field: marshmallow.fields.Field,
#     ) -> None:
#         # TODO: just disabling for now to show more interesting test results
#         # if any(key in self.the_dict for key in [cls, tag]):
#         #     raise Exception()
#
#         type_tag_field = HintTagField(hint=hint, tag=tag, field=field)
#
#         self.the_dict[hint] = type_tag_field
#         self.the_dict[tag] = type_tag_field
#
#     # # TODO: this type hinting...  doesn't help much as it could return
#     # #       another cls
#     # def __call__(self, tag: str, field: marshmallow.fields) -> typing.Callable[[T], T]:
#     #     return lambda cls: self.register(cls=cls, tag=tag, field=field)
#
#     def from_object(self, value: typing.Any) -> HintTagField:
#         return self.the_dict[type(value)]
#
#     def from_tag(self, tag: str) -> HintTagField:
#         return self.the_dict[tag]


@check_field_registry_protocol
@attr.s(auto_attribs=True)
class TypeAndHintFieldRegistry:
    """This registry uses type hint and type checks to decide what field to use for
    serialization.  The deserialization field is chosen directly from the tag."""

    by_tag: typing.Dict[str, HintTagField] = attr.ib(factory=dict)

    # TODO: but type bans from-scratch metatypes...  and protocols
    def register(
        self,
        hint: typing.Any,
        tag: str,
        field: marshmallow.fields.Field,
    ) -> None:
        if tag in self.by_tag:
            raise desert.exceptions.TagAlreadyRegistered(tag=tag)

        type_tag_field = HintTagField(hint=hint, tag=tag, field=field)

        self.by_tag[tag] = type_tag_field

    def from_object(self, value: typing.Any) -> HintTagField:
        scores = {}

        # for type_tag_field in self.the_list:
        for type_tag_field in self.by_tag.values():
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
            raise desert.exceptions.NoMatchingHintFound(
                hints=[ttf.hint for ttf in self.by_tag.values()], value=value
            )

        potential = [ttf for ttf, score in scores.items() if score == high_score]

        if len(potential) != 1:
            raise desert.exceptions.MultipleMatchingHintsFound(
                hints=[ttf.hint for ttf in potential], value=value
            )

        [type_tag_field] = potential

        return type_tag_field

    def from_tag(self, tag: str) -> HintTagField:
        return self.by_tag[tag]


@attr.s(auto_attribs=True)
class TaggedValue:
    tag: str
    value: typing.Any


class FromObjectProtocol(typing_extensions.Protocol):
    def __call__(self, value: typing.Any) -> HintTagField:
        ...


class FromTagProtocol(typing_extensions.Protocol):
    def __call__(self, tag: str) -> HintTagField:
        ...


class FromTaggedProtocol(typing_extensions.Protocol):
    def __call__(self, item: typing.Any) -> TaggedValue:
        ...


class ToTaggedProtocol(typing_extensions.Protocol):
    def __call__(self, tag: typing.Any, value: typing.Any) -> typing.Any:
        ...


class TaggedUnionField(marshmallow.fields.Field):
    """A Marshmallow field to handle unions where the data may not always be of a
    single type.  Usually this field would not be created directly but rather by
    using helper functions to fill out the needed functions in a consistent manner.
    """

    def __init__(
        self,
        *,
        from_object: FromObjectProtocol,
        from_tag: FromTagProtocol,
        from_tagged: FromTaggedProtocol,
        to_tagged: ToTaggedProtocol,
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


def from_externally_tagged(item: typing.Any) -> TaggedValue:
    """Process externally tagged data into a :class:`TaggedValue`."""

    [[tag, serialized_value]] = item.items()

    return TaggedValue(tag=tag, value=serialized_value)


def to_externally_tagged(tag: str, value: typing.Any):
    """Process untagged data to the externally tagged form."""

    return {tag: value}


def externally_tagged_union(
    from_object: FromObjectProtocol,
    from_tag: FromTagProtocol,
):
    """Create a :class:`TaggedUnionField` that supports the externally tagged form."""

    # TODO: allow the pass through kwargs to the field

    return TaggedUnionField(
        from_object=from_object,
        from_tag=from_tag,
        from_tagged=from_externally_tagged,
        to_tagged=to_externally_tagged,
    )


def from_internally_tagged(item: typing.Any, type_key: str) -> TaggedValue:
    """Process internally tagged data into a :class:`TaggedValue`."""

    return TaggedValue(
        tag=item[type_key], value={k: v for k, v in item.items() if k != type_key}
    )


def to_internally_tagged(tag: str, value: typing.Any, type_key: str) -> typing.Any:
    """Process untagged data to the internally tagged form."""

    if type_key in value:
        raise desert.exceptions.TypeKeyCollision(type_key=type_key, value=value)

    return {type_key: tag, **value}


def internally_tagged_union(
    from_object: FromObjectProtocol,
    from_tag: FromTagProtocol,
    type_key=default_tagged_type_key,
):
    """Create a :class:`TaggedUnionField` that supports the internally tagged form."""

    return TaggedUnionField(
        from_object=from_object,
        from_tag=from_tag,
        from_tagged=functools.partial(from_internally_tagged, type_key=type_key),
        to_tagged=functools.partial(to_internally_tagged, type_key=type_key),
    )


def from_adjacently_tagged(item: typing.Any, type_key: str, value_key: str):
    """Process adjacently tagged data into a :class:`TaggedValue`."""

    tag = item.pop(type_key)
    serialized_value = item.pop(value_key)

    if len(item) > 0:
        raise Exception()

    return TaggedValue(tag=tag, value=serialized_value)


def to_adjacently_tagged(tag: str, value: typing.Any, type_key: str, value_key: str):
    """Process untagged data to the adjacently tagged form."""

    return {type_key: tag, value_key: value}


def adjacently_tagged_union(
    from_object: FromObjectProtocol,
    from_tag: FromTagProtocol,
    type_key=default_tagged_type_key,
    value_key=default_tagged_value_key,
):
    """Create a :class:`TaggedUnionField` that supports the adjacently tagged form."""

    return TaggedUnionField(
        from_object=from_object,
        from_tag=from_tag,
        from_tagged=functools.partial(
            from_adjacently_tagged, type_key=type_key, value_key=value_key
        ),
        to_tagged=functools.partial(
            to_adjacently_tagged, type_key=type_key, value_key=value_key
        ),
    )


def adjacently_tagged_union_from_registry(
    registry: FieldRegistry,
    type_key=default_tagged_type_key,
    value_key=default_tagged_value_key,
) -> TaggedUnionField:
    """Create a :class:`TaggedUnionField` that supports the adjacently tagged form
    from a :class:`FieldRegistry`.
    """

    return adjacently_tagged_union(
        from_object=registry.from_object,
        from_tag=registry.from_tag,
        type_key=type_key,
        value_key=value_key,
    )
