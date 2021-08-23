import functools
import typing as t

import attr
import marshmallow.fields
import typeguard
import typing_extensions
import typing_inspect

import desert._util
import desert.exceptions


T = t.TypeVar("T")


# TODO: there must be a better name
@attr.s(frozen=True, auto_attribs=True)
class HintTagField:
    """Serializing and deserializing a given piece of data requires a group of
    information.  A type hint that matches the data to be serialized, a Marshmallow
    field that knows how to serialize and deserialize the data, and a string tag to
    label the serialized data for deserialization.  This is that group...  There
    must be a better name.
    """

    hint: t.Any
    tag: str
    field: marshmallow.fields.Field


class FieldRegistryProtocol(typing_extensions.Protocol):
    """This protocol encourages registries to provide a common interface.  The actual
    implementation of the mapping from objects to be serialized to their Marshmallow
    fields, and likewise from the serialized data, can take any form.
    """

    def register(
        self,
        hint: t.Any,
        tag: str,
        field: marshmallow.fields.Field,
    ) -> None:
        """Inform the registry of the relationship between the passed hint, tag, and
        field.
        """
        ...

    @property
    def from_object(self) -> "FromObjectProtocol":
        """This is a funny way of writing that the registry's `.from_object()` method
        should satisfy :class:`FromObjectProtocol`.
        """
        ...

    @property
    def from_tag(self) -> "FromTagProtocol":
        """This is a funny way of writing that the registry's `.from_tag()` method
        should satisfy :class:`FromTagProtocol`.
        """
        ...


check_field_registry_protocol = desert._util.ProtocolChecker[FieldRegistryProtocol]()


# @attr.s(auto_attribs=True)
# class TypeDictFieldRegistry:
#     the_dict: t.Dict[
#         t.Union[type, str],
#         HintTagField,
#     ] = attr.ib(factory=dict)
#
#     def register(
#         self,
#         hint: t.Any,
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
#     # def __call__(self, tag: str, field: marshmallow.fields) -> t.Callable[[T], T]:
#     #     return lambda cls: self.register(cls=cls, tag=tag, field=field)
#
#     def from_object(self, value: t.Any) -> HintTagField:
#         return self.the_dict[type(value)]
#
#     def from_tag(self, tag: str) -> HintTagField:
#         return self.the_dict[tag]


@check_field_registry_protocol
@attr.s(auto_attribs=True)
class TypeAndHintFieldRegistry:
    """This registry uses type and type hint checks to decide what field to use for
    serialization.  The deserialization field is chosen directly from the tag.
    """

    by_tag: t.Dict[str, HintTagField] = attr.ib(factory=dict)

    # TODO: but type bans from-scratch metatypes...  and protocols
    def register(
        self,
        hint: t.Any,
        tag: str,
        field: marshmallow.fields.Field,
    ) -> None:
        if tag in self.by_tag:
            raise desert.exceptions.TagAlreadyRegistered(tag=tag)

        type_tag_field = HintTagField(hint=hint, tag=tag, field=field)

        self.by_tag[tag] = type_tag_field

    def from_object(self, value: object) -> HintTagField:
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
                # as ["a", "b"] matching both t.List[str] and t.Sequence[str].
                # This only works properly on 3.7+.
                if type(value) == typing_inspect.get_origin(type_tag_field.hint):
                    score += 1

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
    value: object


class FromObjectProtocol(typing_extensions.Protocol):
    def __call__(self, value: object) -> HintTagField:
        ...


class FromTagProtocol(typing_extensions.Protocol):
    def __call__(self, tag: str) -> HintTagField:
        ...


class FromTaggedProtocol(typing_extensions.Protocol):
    def __call__(self, item: t.Any) -> TaggedValue:
        ...


class ToTaggedProtocol(typing_extensions.Protocol):
    def __call__(self, tag: str, value: t.Any) -> object:
        ...


class TaggedUnionField(marshmallow.fields.Field):
    """A Marshmallow field to handle unions where the data may not always be of a
    single type.  Usually this field would not be created directly but rather by
    using helper functions to fill out the needed functions in a consistent manner.

    Helpers are provided both to directly create various forms of this field as well
    as to create the same from a :class:`FieldRegistry`.

    - From a registry

      - :func:`externally_tagged_union_from_registry`
      - :func:`internally_tagged_union_from_registry`
      - :func:`adjacently_tagged_union_from_registry`

    - Direct

      - :func:`externally_tagged_union`
      - :func:`internally_tagged_union`
      - :func:`adjacently_tagged_union`
    """

    def __init__(
        self,
        *,
        from_object: FromObjectProtocol,
        from_tag: FromTagProtocol,
        from_tagged: FromTaggedProtocol,
        to_tagged: ToTaggedProtocol,
        # object results in the super() call complaining about types
        # https://github.com/python/mypy/issues/5382
        **kwargs: t.Any,
    ) -> None:
        super().__init__(**kwargs)

        self.from_object = from_object
        self.from_tag = from_tag
        self.from_tagged = from_tagged
        self.to_tagged = to_tagged

    def _deserialize(
        self,
        value: object,
        attr: t.Optional[str],
        data: t.Optional[t.Mapping[str, object]],
        # object results in the super() call complaining about types
        # https://github.com/python/mypy/issues/5382
        **kwargs: t.Any,
    ) -> object:
        tagged_value = self.from_tagged(item=value)

        type_tag_field = self.from_tag(tagged_value.tag)
        field = type_tag_field.field

        return field.deserialize(tagged_value.value)

    def _serialize(
        self,
        value: object,
        attr: str,
        obj: object,
        # object results in the super() call complaining about types
        # https://github.com/python/mypy/issues/5382
        **kwargs: t.Any,
    ) -> object:
        type_tag_field = self.from_object(value)
        field = type_tag_field.field
        tag = type_tag_field.tag
        serialized_value = field.serialize(attr, obj)

        return self.to_tagged(tag=tag, value=serialized_value)


default_tagged_type_key = "#type"
default_tagged_value_key = "#value"


def from_externally_tagged(item: t.Mapping[str, object]) -> TaggedValue:
    """Process externally tagged data into a :class:`TaggedValue`."""

    [[tag, serialized_value]] = item.items()

    return TaggedValue(tag=tag, value=serialized_value)


def to_externally_tagged(tag: str, value: object) -> t.Dict[str, object]:
    """Process untagged data to the externally tagged form."""

    return {tag: value}


def externally_tagged_union(
    from_object: FromObjectProtocol,
    from_tag: FromTagProtocol,
) -> TaggedUnionField:
    """Create a :class:`TaggedUnionField` that supports the externally tagged form."""

    # TODO: allow the pass through kwargs to the field

    return TaggedUnionField(
        from_object=from_object,
        from_tag=from_tag,
        from_tagged=from_externally_tagged,
        to_tagged=to_externally_tagged,
    )


def externally_tagged_union_from_registry(
    registry: FieldRegistryProtocol,
) -> TaggedUnionField:
    """Use a :class:`FieldRegistry` to create a :class:`TaggedUnionField` that supports
    the externally tagged form.  Externally tagged data has the following form.

    ..  include:: ../snippets/tag_forms/external.rst
    """

    return externally_tagged_union(
        from_object=registry.from_object,
        from_tag=registry.from_tag,
    )


def from_internally_tagged(item: t.Mapping[str, object], type_key: str) -> TaggedValue:
    """Process internally tagged data into a :class:`TaggedValue`."""

    # it just kind of has to be a string...
    type_string: str = item[type_key]  # type: ignore[assignment]

    return TaggedValue(
        tag=type_string,
        value={k: v for k, v in item.items() if k != type_key},
    )


def to_internally_tagged(
    tag: str,
    value: t.Mapping[str, object],
    type_key: str,
) -> t.Mapping[str, object]:
    """Process untagged data to the internally tagged form."""

    if type_key in value:
        raise desert.exceptions.TypeKeyCollision(type_key=type_key, value=value)

    return {type_key: tag, **value}


def internally_tagged_union(
    from_object: FromObjectProtocol,
    from_tag: FromTagProtocol,
    type_key: str = default_tagged_type_key,
) -> TaggedUnionField:
    """Create a :class:`TaggedUnionField` that supports the internally tagged form."""

    return TaggedUnionField(
        from_object=from_object,
        from_tag=from_tag,
        from_tagged=functools.partial(from_internally_tagged, type_key=type_key),
        to_tagged=functools.partial(to_internally_tagged, type_key=type_key),
    )


def internally_tagged_union_from_registry(
    registry: FieldRegistryProtocol,
    type_key: str = default_tagged_type_key,
) -> TaggedUnionField:
    """Use a :class:`FieldRegistry` to create a :class:`TaggedUnionField` that supports
    the internally tagged form.  Internally tagged data has the following form.

    ..  include:: ../snippets/tag_forms/internal.rst
    """

    return internally_tagged_union(
        from_object=registry.from_object,
        from_tag=registry.from_tag,
        type_key=type_key,
    )


def from_adjacently_tagged(
    item: t.Dict[str, object], type_key: str, value_key: str
) -> TaggedValue:
    """Process adjacently tagged data into a :class:`TaggedValue`."""

    tag: str = item.pop(type_key)  # type: ignore[assignment]
    serialized_value = item.pop(value_key)

    if len(item) > 0:
        raise Exception()

    return TaggedValue(tag=tag, value=serialized_value)


def to_adjacently_tagged(
    tag: str, value: object, type_key: str, value_key: str
) -> t.Dict[str, object]:
    """Process untagged data to the adjacently tagged form."""

    return {type_key: tag, value_key: value}


def adjacently_tagged_union(
    from_object: FromObjectProtocol,
    from_tag: FromTagProtocol,
    type_key: str = default_tagged_type_key,
    value_key: str = default_tagged_value_key,
) -> TaggedUnionField:
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
    registry: FieldRegistryProtocol,
    type_key: str = default_tagged_type_key,
    value_key: str = default_tagged_value_key,
) -> TaggedUnionField:
    """Use a :class:`FieldRegistry` to create a :class:`TaggedUnionField` that supports
    the adjacently tagged form.  Adjacently tagged data has the following form.

    ..  include:: ../snippets/tag_forms/adjacent.rst
    """

    return adjacently_tagged_union(
        from_object=registry.from_object,
        from_tag=registry.from_tag,
        type_key=type_key,
        value_key=value_key,
    )
