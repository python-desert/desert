"""Build schemas from classes that are defined below their containing class.

This test is run at global scope because :func:`typing.get_type_hints()` does not work on
forward references defined in function scope scope.

"""

import dataclasses

import attr

import desert


for module in [dataclasses, attr]:
    # Type ignores are just here for now instead of figuring out how to
    # handle these properly.

    @module.dataclass
    class A:
        x: "B"

    @module.dataclass
    class B:
        y: int

    schema = desert.schema_class(A)()
    dumped = {"x": {"y": 1}}
    loaded = A((B(1)))  # type:ignore[call-arg]

    assert schema.load(dumped) == loaded
    assert schema.dump(loaded) == dumped
