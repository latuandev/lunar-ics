"""Shared type aliases."""

from __future__ import annotations

JSONScalar = str | int | float | bool | None
JSONValue = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]
JSONDict = dict[str, JSONValue]

