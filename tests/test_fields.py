import abc
import collections.abc
import decimal
import json
import sys
import typing as t

# https://github.com/pytest-dev/pytest/issues/7469
import _pytest.fixtures
import attr
import marshmallow
import pytest

import desert._fields
import desert.exceptions


# TODO: test that field constructor doesn't tromple Field parameters

_NOTHING = object()


@attr.frozen
class ExampleData:
    to_serialize: t.Any
    serialized: t.Any
    deserialized: t.Any
    tag: str
    field: marshmallow.fields.Field
    # TODO: can we be more specific?
    hint: t.Any
    requires_origin: bool = False

    @classmethod
    def build(
        cls,
        hint: object,
        to_serialize: object,
        tag: str,
        field: marshmallow.fields.Field,
        requires_origin: bool = False,
        serialized: object = _NOTHING,
        deserialized: object = _NOTHING,
    ) -> "ExampleData":
        if serialized is _NOTHING:
            serialized = to_serialize

        if deserialized is _NOTHING:
            deserialized = to_serialize

        return cls(
            hint=hint,
            to_serialize=to_serialize,
            serialized=serialized,
            deserialized=deserialized,
            tag=tag,
            field=field,
            requires_origin=requires_origin,
        )


basic_example_data_list = [
    ExampleData.build(
        hint=float,
        to_serialize=3.7,
        tag="float_tag",
        field=marshmallow.fields.Float(),
    ),
    ExampleData.build(
        hint=str,
        to_serialize="29",
        tag="str_tag",
        field=marshmallow.fields.String(),
    ),
    ExampleData.build(
        hint=decimal.Decimal,
        to_serialize=decimal.Decimal("4.2"),
        serialized="4.2",
        tag="decimal_tag",
        field=marshmallow.fields.Decimal(as_string=True),
    ),
    ExampleData.build(
        hint=t.List[int],
        to_serialize=[1, 2, 3],
        tag="integer_list_tag",
        field=marshmallow.fields.List(marshmallow.fields.Integer()),
    ),
    ExampleData.build(
        hint=t.List[str],
        to_serialize=["abc", "2", "mno"],
        tag="string_list_tag",
        field=marshmallow.fields.List(marshmallow.fields.String()),
        requires_origin=True,
    ),
    ExampleData.build(
        hint=t.Sequence[str],
        to_serialize=("def", "13"),
        serialized=["def", "13"],
        deserialized=["def", "13"],
        tag="string_sequence_tag",
        field=marshmallow.fields.List(marshmallow.fields.String()),
    ),
]


@attr.frozen
class CustomExampleClass:
    a: int
    b: str


custom_example_data_list = [
    ExampleData.build(
        hint=CustomExampleClass,
        to_serialize=CustomExampleClass(a=1, b="b"),
        serialized={"a": 1, "b": "b"},
        tag="custom_example_class",
        field=marshmallow.fields.Nested(desert.schema(CustomExampleClass)),
    ),
]


all_example_data_list = basic_example_data_list + custom_example_data_list


@pytest.fixture(
    name="example_data",
    params=all_example_data_list,
    ids=[str(example) for example in all_example_data_list],
)
def _example_data(request: _pytest.fixtures.SubRequest) -> ExampleData:
    return request.param  # type: ignore[no-any-return]


@pytest.fixture(
    name="custom_example_data",
    params=custom_example_data_list,
    ids=[str(example) for example in custom_example_data_list],
)
def _custom_example_data(request: _pytest.fixtures.SubRequest) -> ExampleData:
    return request.param  # type: ignore[no-any-return]


# def build_type_dict_registry(examples):
#     registry = desert._fields.TypeDictFieldRegistry()
#
#     for example in examples:
#         registry.register(
#             hint=example.hint,
#             tag=example.tag,
#             field=example.field,
#         )
#
#     return registry


# class NonStringSequence(abc.ABC):
#     @classmethod
#     def __subclasshook__(cls, maybe_subclass):
#         return isinstance(maybe_subclass, collections.abc.Sequence) and not isinstance(
#             maybe_subclass, str
#         )


def build_order_isinstance_registry(
    examples: t.List[ExampleData],
) -> desert._fields.TypeAndHintFieldRegistry:
    registry = desert._fields.TypeAndHintFieldRegistry()

    # registry.register(
    #     hint=t.List[],
    #     tag="sequence_abc",
    #     field=marshmallow.fields.List(marshmallow.fields.String()),
    # )

    for example in examples:
        registry.register(
            hint=example.hint,
            tag=example.tag,
            field=example.field,
        )

    return registry


registries = [
    # build_type_dict_registry(example_data_list),
    build_order_isinstance_registry(all_example_data_list),
]
registry_ids = [type(registry).__name__ for registry in registries]


@pytest.fixture(
    name="registry",
    params=registries,
    ids=registry_ids,
)
def _registry(
    request: _pytest.fixtures.SubRequest,
) -> desert._fields.TypeAndHintFieldRegistry:
    return request.param  # type: ignore[no-any-return]


def test_registry_raises_for_no_match(
    registry: desert._fields.FieldRegistryProtocol,
) -> None:
    class C:
        pass

    c = C()

    with pytest.raises(desert.exceptions.NoMatchingHintFound):
        registry.from_object(value=c)


def test_registry_raises_for_multiple_matches() -> None:
    registry = desert._fields.TypeAndHintFieldRegistry()

    registry.register(
        hint=t.Sequence,
        tag="sequence",
        field=marshmallow.fields.List(marshmallow.fields.Field()),
    )

    registry.register(
        hint=t.Collection,
        tag="collection",
        field=marshmallow.fields.List(marshmallow.fields.Field()),
    )

    with pytest.raises(desert.exceptions.MultipleMatchingHintsFound):
        registry.from_object(value=[])


@pytest.fixture(name="externally_tagged_field", params=[False, True])
def _externally_tagged_field(
    request: _pytest.fixtures.SubRequest,
    registry: desert._fields.FieldRegistryProtocol,
) -> desert._fields.TaggedUnionField:
    field: desert._fields.TaggedUnionField

    if request.param:
        field = desert._fields.externally_tagged_union_from_registry(registry=registry)
    else:
        field = desert._fields.externally_tagged_union(
            from_object=registry.from_object,
            from_tag=registry.from_tag,
        )

    return field


def test_externally_tagged_deserialize(
    example_data: ExampleData, externally_tagged_field: desert._fields.TaggedUnionField
) -> None:
    serialized = {example_data.tag: example_data.serialized}

    deserialized = externally_tagged_field.deserialize(serialized)

    expected = example_data.deserialized

    assert (type(deserialized) == type(expected)) and (deserialized == expected)


def test_externally_tagged_deserialize_extra_key_raises(
    example_data: ExampleData,
    externally_tagged_field: desert._fields.TaggedUnionField,
) -> None:
    serialized = {
        example_data.tag: {
            "#value": example_data.serialized,
            "extra": 29,
        },
    }

    with pytest.raises(expected_exception=Exception):
        externally_tagged_field.deserialize(serialized)


def test_externally_tagged_serialize(
    example_data: ExampleData,
    externally_tagged_field: desert._fields.TaggedUnionField,
) -> None:
    if example_data.requires_origin and sys.version_info < (3, 7):
        pytest.xfail()

    obj = {"key": example_data.to_serialize}

    serialized = externally_tagged_field.serialize("key", obj)

    assert serialized == {example_data.tag: example_data.serialized}


@pytest.fixture(name="internally_tagged_field", params=[False, True])
def _internally_tagged_field(
    request: _pytest.fixtures.SubRequest,
    registry: desert._fields.FieldRegistryProtocol,
) -> desert._fields.TaggedUnionField:
    field: desert._fields.TaggedUnionField

    if request.param:
        field = desert._fields.internally_tagged_union_from_registry(registry=registry)
    else:
        field = desert._fields.internally_tagged_union(
            from_object=registry.from_object,
            from_tag=registry.from_tag,
        )

    return field


def test_to_internally_tagged_raises_for_tag_collision() -> None:
    with pytest.raises(desert.exceptions.TypeKeyCollision):
        desert._fields.to_internally_tagged(
            tag="C", value={"collide": True}, type_key="collide"
        )


def test_internally_tagged_deserialize(
    custom_example_data: ExampleData,
    internally_tagged_field: desert._fields.TaggedUnionField,
) -> None:
    serialized = {"#type": custom_example_data.tag, **custom_example_data.serialized}

    deserialized = internally_tagged_field.deserialize(serialized)

    expected = custom_example_data.deserialized

    assert (type(deserialized) == type(expected)) and (deserialized == expected)


def test_internally_tagged_serialize(
    custom_example_data: ExampleData,
    internally_tagged_field: desert._fields.TaggedUnionField,
) -> None:
    obj = {"key": custom_example_data.to_serialize}

    serialized = internally_tagged_field.serialize("key", obj)

    assert serialized == {
        "#type": custom_example_data.tag,
        **custom_example_data.serialized,
    }


@pytest.fixture(name="adjacently_tagged_field", params=[False, True])
def _adjacently_tagged_field(
    request: _pytest.fixtures.SubRequest,
    registry: desert._fields.FieldRegistryProtocol,
) -> desert._fields.TaggedUnionField:
    field: desert._fields.TaggedUnionField

    if request.param:
        field = desert._fields.adjacently_tagged_union_from_registry(registry=registry)
    else:
        field = desert._fields.adjacently_tagged_union(
            from_object=registry.from_object,
            from_tag=registry.from_tag,
        )

    return field


def test_adjacently_tagged_deserialize(
    example_data: ExampleData,
    adjacently_tagged_field: desert._fields.TaggedUnionField,
) -> None:
    serialized = {"#type": example_data.tag, "#value": example_data.serialized}

    deserialized = adjacently_tagged_field.deserialize(serialized)

    expected = example_data.deserialized

    assert (type(deserialized) == type(expected)) and (deserialized == expected)


def test_adjacently_tagged_deserialize_extra_key_raises(
    example_data: ExampleData,
    adjacently_tagged_field: desert._fields.TaggedUnionField,
) -> None:
    serialized = {
        "#type": example_data.tag,
        "#value": example_data.serialized,
        "extra": 29,
    }

    with pytest.raises(expected_exception=Exception):
        adjacently_tagged_field.deserialize(serialized)


def test_adjacently_tagged_serialize(
    example_data: ExampleData,
    adjacently_tagged_field: desert._fields.TaggedUnionField,
) -> None:
    if example_data.requires_origin and sys.version_info < (3, 7):
        pytest.xfail()

    obj = {"key": example_data.to_serialize}

    serialized = adjacently_tagged_field.serialize("key", obj)

    assert serialized == {"#type": example_data.tag, "#value": example_data.serialized}


# start tagged_union_example
def test_actual_example() -> None:
    registry = desert._fields.TypeAndHintFieldRegistry()
    registry.register(hint=str, tag="str", field=marshmallow.fields.String())
    registry.register(hint=int, tag="int", field=marshmallow.fields.Integer())

    field = desert._fields.adjacently_tagged_union_from_registry(registry=registry)

    @attr.frozen
    class C:
        # TODO: desert.ib() shouldn't be needed for many cases
        union: t.Union[str, int] = desert.ib(marshmallow_field=field)

    schema = desert.schema(C)

    objects = C(union="3")
    marshalled = {"union": {"#type": "str", "#value": "3"}}
    serialized = json.dumps(marshalled)

    assert schema.dumps(objects) == serialized
    assert schema.loads(serialized) == objects
    # end tagged_union_example


def test_raises_for_tag_reregistration() -> None:
    registry = desert._fields.TypeAndHintFieldRegistry()
    registry.register(hint=str, tag="duplicate_tag", field=marshmallow.fields.String())

    with pytest.raises(desert.exceptions.TagAlreadyRegistered):
        registry.register(
            hint=int, tag="duplicate_tag", field=marshmallow.fields.Integer()
        )
