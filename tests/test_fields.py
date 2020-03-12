import decimal
import typing

import attr
import marshmallow
import pytest

import desert._fields


# TODO: test that field constructor doesn't tromple Field parameters


@attr.s(auto_attribs=True)
class ExampleData:
    object: typing.Any
    tag: str
    field: typing.Callable[[], marshmallow.fields.Field]


example_data_list = [
    ExampleData(object=3.7, tag="float_tag", field=marshmallow.fields.Float),
    ExampleData(object="29", tag="str_tag", field=marshmallow.fields.String),
    ExampleData(
        object=decimal.Decimal("4.2"),
        tag="decimal_tag",
        field=marshmallow.fields.Decimal,
    ),
]


@pytest.fixture(
    name="example_data",
    params=example_data_list,
    ids=[str(example) for example in example_data_list],
)
def _example_data(request):
    return request.param


@pytest.fixture(name="registry", scope="session")
def _registry():
    registry = desert._fields.TypeDictRegistry()

    for example in example_data_list:
        registry.register(
            cls=type(example.object), tag=example.tag, field=example.field,
        )

    return registry


@pytest.fixture(name="adjacently_tagged_field", scope="session")
def _adjacently_tagged_field(registry):
    return desert._fields.AdjacentlyTaggedUnion(
        from_object=registry.from_object, from_tag=registry.from_tag,
    )


def test_adjacently_tagged_deserialize(example_data, adjacently_tagged_field):
    serialized_value = {"type": example_data.tag, "value": example_data.object}

    deserialized_value = adjacently_tagged_field.deserialize(serialized_value)

    assert (type(deserialized_value) == type(example_data.object)) and (
        deserialized_value == example_data.object
    )


def test_adjacently_tagged_deserialize_extra_key_raises(
    example_data, adjacently_tagged_field,
):
    serialized_value = {
        "type": example_data.tag,
        "value": example_data.object,
        "extra": 29,
    }

    with pytest.raises(expected_exception=Exception):
        adjacently_tagged_field.deserialize(serialized_value)


def test_adjacently_tagged_serialize(example_data, adjacently_tagged_field):
    obj = {"key": example_data.object}

    serialized_value = adjacently_tagged_field.serialize("key", obj)

    assert serialized_value == {"type": example_data.tag, "value": example_data.object}
