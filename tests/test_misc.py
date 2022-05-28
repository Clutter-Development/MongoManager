from typing import Any, TypeVar

import pytest

from mongo_manager import create_nested_dict, find_in_nested_dict, maybe_int

T = TypeVar("T")


@pytest.mark.parametrize(
    ("find_in", "path", "default", "expected_result"),
    (
        ({"abc": {"def": {"ghi": 123}}}, "abc.def.ghi", "unused default", 123),
        ({"abc": {"def": {"ghi": 123}}}, ["abc", "def", "ghi"], "unused default", 123),
        ({"abc": {"def": {"ghi": 123}}}, "abc.def.ghii", "used default", "used default"),
    ),
)
def test_find_in_nested_dict(
    *, find_in: dict, path: str | list[str], default: Any, expected_result: Any
) -> None:
    assert find_in_nested_dict(find_in, path, default=default) == expected_result


@pytest.mark.parametrize(
    ("path", "value", "expected_result"),
    (
        ("abc.def.ghi", 123, {"abc": {"def": {"ghi": 123}}}),
        (["abc", "def", "ghi"], 123, {"abc": {"def": {"ghi": 123}}}),
        ("", 123, 123),
        ([], 123, 123),
    ),
)
def test_create_nested_dict(*, path: str | list[str], value: T, expected_result: dict | T) -> None:
    assert create_nested_dict(path, value) == expected_result


@pytest.mark.parametrize(
    ("value", "expected_result"),
    (("123456789", 123456789), ("string", "string")),
)
def test_maybe_int(*, value: T, expected_result: int | T) -> None:
    assert maybe_int(value) == expected_result
