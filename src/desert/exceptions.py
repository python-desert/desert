import dataclasses
import typing as t

import attr


class DesertException(Exception):
    """Top-level exception for desert."""


class MultipleMatchingHintsFound(DesertException):
    """Raised when a union finds multiple hints that equally match the data to be
    serialized.
    """

    def __init__(self, hints: t.Any, value: object):
        hint_list = ", ".join(str(hint) for hint in hints)
        super().__init__(
            f"Multiple matching type hints found in union for {value!r}.  Candidates: {hint_list}"
        )


class NoMatchingHintFound(DesertException):
    """Raised when a union is unable to find a valid hint for the data to be
    serialized.
    """

    def __init__(self, hints: t.Any, value: object):
        hint_list = ", ".join(str(hint) for hint in hints)
        super().__init__(
            f"No matching type hints found in union for {value!r}.  Considered: {hint_list}"
        )


class NotAnAttrsClassOrDataclass(DesertException):
    """Raised for dataclass operations on non-dataclasses."""


class TypeKeyCollision(DesertException):
    """Raised when a tag key collides with a data value."""

    def __init__(self, type_key: str, value: object):
        super().__init__(f"Type key {type_key!r} collided with attribute in: {value!r}")


class UnknownType(DesertException):
    """Raised for a type with unknown serialization equivalent."""
