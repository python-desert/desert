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
    field: typing.Type[marshmallow.fields.Field]


example_data = [
    ExampleData(object=3.7, tag="float_tag", field=marshmallow.fields.Float,),
]


@pytest.fixture(
    name="example_data", params=example_data,
)
def _example_data(request):
    return request.param


@pytest.fixture(name="registry", scope="session")
def _registry():
    registry = desert._fields.TypeDictRegistry()

    for example in example_data:
        registry.register(
            cls=type(example.object), tag=example.tag, field=example.field,
        )

    return registry


def test_adjacently_tagged_deserialize(example_data, registry):
    field = desert._fields.AdjacentlyTaggedUnion(
        from_object=registry.from_object, from_tag=registry.from_tag,
    )

    serialized_value = {"type": example_data.tag, "value": example_data.object}

    deserialized_value = field.deserialize(serialized_value)

    assert deserialized_value == example_data.object


def test_adjacently_tagged_serialize(example_data, registry):
    field = desert._fields.AdjacentlyTaggedUnion(
        from_object=registry.from_object, from_tag=registry.from_tag,
    )

    obj = {"key": example_data.object}

    serialized_value = field.serialize("key", obj)

    assert serialized_value == {"type": example_data.tag, "value": example_data.object}
