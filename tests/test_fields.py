import abc
import collections.abc
import decimal
import typing

import attr
import marshmallow
import pytest

import desert.exceptions
import desert._fields

# TODO: test that field constructor doesn't tromple Field parameters

_NOTHING = object()


@attr.frozen
class ExampleData:
    to_serialize: typing.Any
    serialized: typing.Any
    deserialized: typing.Any
    tag: str
    field: marshmallow.fields.Field
    # TODO: can we be more specific?
    hint: typing.Any

    @classmethod
    def build(
        cls,
        hint,
        to_serialize,
        tag,
        field,
        serialized=_NOTHING,
        deserialized=_NOTHING,
    ):
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
        hint=typing.List[int],
        to_serialize=[1, 2, 3],
        tag="integer_list_tag",
        field=marshmallow.fields.List(marshmallow.fields.Integer()),
    ),
    ExampleData.build(
        hint=typing.List[str],
        to_serialize=["abc", "2", "mno"],
        tag="string_list_tag",
        field=marshmallow.fields.List(marshmallow.fields.String()),
    ),
    ExampleData.build(
        hint=typing.Sequence[str],
        to_serialize=("def", "13"),
        serialized=["def", "13"],
        deserialized=["def", "13"],
        tag="string_list_tag",
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
def _example_data(request):
    return request.param


@pytest.fixture(
    name="custom_example_data",
    params=custom_example_data_list,
    ids=[str(example) for example in custom_example_data_list],
)
def _custom_example_data(request):
    return request.param


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


def build_order_isinstance_registry(examples):
    registry = desert._fields.OrderedIsinstanceFieldRegistry()

    # registry.register(
    #     hint=typing.List[],
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
def _registry(request):
    return request.param


def test_registry_raises_for_no_match(registry):
    class C:
        pass

    c = C()

    with pytest.raises(desert.exceptions.NoMatchingHintFound):
        registry.from_object(value=c)


def test_registry_raises_for_multiple_matches():
    registry = desert._fields.OrderedIsinstanceFieldRegistry()

    registry.register(
        hint=typing.Sequence,
        tag="sequence",
        field=marshmallow.fields.List(marshmallow.fields.Field()),
    )

    registry.register(
        hint=typing.Collection,
        tag="collection",
        field=marshmallow.fields.List(marshmallow.fields.Field()),
    )

    with pytest.raises(desert.exceptions.MultipleMatchingHintsFound):
        registry.from_object(value=[])


@pytest.fixture(name="externally_tagged_field")
def _externally_tagged_field(registry):
    return desert._fields.externally_tagged_union(
        from_object=registry.from_object,
        from_tag=registry.from_tag,
    )


def test_externally_tagged_deserialize(example_data, externally_tagged_field):
    serialized = {example_data.tag: example_data.serialized}

    deserialized = externally_tagged_field.deserialize(serialized)

    expected = example_data.deserialized

    assert (type(deserialized) == type(expected)) and (deserialized == expected)


def test_externally_tagged_deserialize_extra_key_raises(
    example_data,
    externally_tagged_field,
):
    serialized = {
        example_data.tag: {
            "#value": example_data.serialized,
            "extra": 29,
        },
    }

    with pytest.raises(expected_exception=Exception):
        externally_tagged_field.deserialize(serialized)


def test_externally_tagged_serialize(example_data, externally_tagged_field):
    obj = {"key": example_data.to_serialize}

    serialized = externally_tagged_field.serialize("key", obj)

    assert serialized == {example_data.tag: example_data.serialized}


@pytest.fixture(name="internally_tagged_field")
def _internally_tagged_field(registry):
    return desert._fields.internally_tagged_union(
        from_object=registry.from_object,
        from_tag=registry.from_tag,
    )


def test_to_internally_tagged_raises_for_tag_collision():
    with pytest.raises(desert.exceptions.TypeKeyCollision):
        desert._fields.to_internally_tagged(
            tag="C", value={"collide": True}, type_key="collide"
        )


def test_internally_tagged_deserialize(custom_example_data, internally_tagged_field):
    serialized = {"#type": custom_example_data.tag, **custom_example_data.serialized}

    deserialized = internally_tagged_field.deserialize(serialized)

    expected = custom_example_data.deserialized

    assert (type(deserialized) == type(expected)) and (deserialized == expected)


def test_internally_tagged_serialize(custom_example_data, internally_tagged_field):
    obj = {"key": custom_example_data.to_serialize}

    serialized = internally_tagged_field.serialize("key", obj)

    assert serialized == {
        "#type": custom_example_data.tag,
        **custom_example_data.serialized,
    }


@pytest.fixture(name="adjacently_tagged_field")
def _adjacently_tagged_field(registry):
    return desert._fields.adjacently_tagged_union(
        from_object=registry.from_object,
        from_tag=registry.from_tag,
    )


def test_adjacently_tagged_deserialize(example_data, adjacently_tagged_field):
    serialized = {"#type": example_data.tag, "#value": example_data.serialized}

    deserialized = adjacently_tagged_field.deserialize(serialized)

    expected = example_data.deserialized

    assert (type(deserialized) == type(expected)) and (deserialized == expected)


def test_adjacently_tagged_deserialize_extra_key_raises(
    example_data,
    adjacently_tagged_field,
):
    serialized = {
        "#type": example_data.tag,
        "#value": example_data.serialized,
        "extra": 29,
    }

    with pytest.raises(expected_exception=Exception):
        adjacently_tagged_field.deserialize(serialized)


def test_adjacently_tagged_serialize(example_data, adjacently_tagged_field):
    obj = {"key": example_data.to_serialize}

    serialized = adjacently_tagged_field.serialize("key", obj)

    assert serialized == {"#type": example_data.tag, "#value": example_data.serialized}
