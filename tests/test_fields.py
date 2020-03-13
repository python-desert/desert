import decimal
import typing

import attr
import marshmallow
import pytest

import desert._fields


# TODO: test that field constructor doesn't tromple Field parameters

_NOTHING = object()


@attr.s(auto_attribs=True)
class ExampleData:
    to_serialize: typing.Any
    serialized: typing.Any
    deserialized: typing.Any
    tag: str
    field: marshmallow.fields.Field

    @classmethod
    def build(
        cls, to_serialize, tag, field, serialized=_NOTHING, deserialized=_NOTHING,
    ):
        if serialized is _NOTHING:
            serialized = to_serialize

        if deserialized is _NOTHING:
            deserialized = to_serialize

        return cls(
            to_serialize=to_serialize,
            serialized=serialized,
            deserialized=deserialized,
            tag=tag,
            field=field,
        )


example_data_list = [
    ExampleData.build(
        to_serialize=3.7, tag="float_tag", field=marshmallow.fields.Float()
    ),
    ExampleData.build(
        to_serialize="29", tag="str_tag", field=marshmallow.fields.String()
    ),
    ExampleData.build(
        to_serialize=decimal.Decimal("4.2"),
        serialized="4.2",
        tag="decimal_tag",
        field=marshmallow.fields.Decimal(as_string=True),
    ),
    ExampleData.build(
        to_serialize=[1, 2, 3],
        tag="integer_list_tag",
        field=marshmallow.fields.List(marshmallow.fields.Integer()),
    ),
    ExampleData.build(
        to_serialize=["abc", "2", "mno"],
        tag="string_list_tag",
        field=marshmallow.fields.List(marshmallow.fields.String()),
    ),
    ExampleData(
        to_serialize=("def", "13"),
        serialized=["def", "13"],
        deserialized=["def", "13"],
        tag="string_list_tag",
        field=marshmallow.fields.List(marshmallow.fields.String()),
    ),
]


@pytest.fixture(
    name="example_data",
    params=example_data_list,
    ids=[str(example) for example in example_data_list],
)
def _example_data(request):
    return request.param


def build_type_dict_registry(examples):
    registry = desert._fields.TypeDictFieldRegistry()

    for example in examples:
        registry.register(
            cls=type(example.deserialized), tag=example.tag, field=example.field,
        )

    return registry


registry_builders = [
    build_type_dict_registry,
]
registries = [
    registry_builder(example_data_list)
    for registry_builder in registry_builders
]
registry_ids = [
    type(registry).__name__
    for registry in registries
]


@pytest.fixture(
    name="registry",
    params=registries,
    ids=registry_ids,
)
def _registry(request):
    return request.param


@pytest.fixture(name="adjacently_tagged_field")
def _adjacently_tagged_field(registry):
    return desert._fields.AdjacentlyTaggedUnion(
        from_object=registry.from_object, from_tag=registry.from_tag,
    )


def test_adjacently_tagged_deserialize(example_data, adjacently_tagged_field):
    serialized = {"type": example_data.tag, "value": example_data.serialized}

    deserialized = adjacently_tagged_field.deserialize(serialized)

    expected = example_data.deserialized

    assert (type(deserialized) == type(expected)) and (deserialized == expected)


def test_adjacently_tagged_deserialize_extra_key_raises(
    example_data, adjacently_tagged_field,
):
    serialized = {
        "type": example_data.tag,
        "value": example_data.serialized,
        "extra": 29,
    }

    with pytest.raises(expected_exception=Exception):
        adjacently_tagged_field.deserialize(serialized)


def test_adjacently_tagged_serialize(example_data, adjacently_tagged_field):
    obj = {"key": example_data.to_serialize}

    serialized = adjacently_tagged_field.serialize("key", obj)

    assert serialized == {"type": example_data.tag, "value": example_data.serialized}
