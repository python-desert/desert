import dataclasses

import attr


class DesertException(Exception):
    """Top-level exception for desert."""


class NotAnAttrsClassOrDataclass(DesertException):
    """Raised for dataclass operations on non-dataclasses."""
