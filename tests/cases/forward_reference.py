"""Build schemas from classes that are defined below their containing class.

This test is run at global scope because :func:`typing.get_type_hints()` does not work on
forward references defined in function scope scope.

"""

import dataclasses

import attr

import desert


for module in [dataclasses, attr]:

    @module.dataclass
    class A:
        x: "B"

    @module.dataclass
    class B:
        y: int

    schema = desert.schema_class(A)()
    dumped = {"x": {"y": 1}}
    loaded = A((B(1)))

    assert schema.load(dumped) == loaded
    assert schema.dump(loaded) == dumped
