from typing import Any, TypeVar

import pytest

from mongo_manager import create_nested_dict, find_in_nested_dict, maybe_int

T = TypeVar("T")


@pytest.mark.parametrize(
    ("find_in", "path", "default", "expected_result"),
    (
        ({"": {"aa": {"b": {"b": 123}}}}, ".aa.b.b", "this shouldnt be accessed", 123),
        ({"": {"": {"cc": {"qqq": "str"}}}}, ["", "", "cc", "qqq"], "this too", "str"),
        ({"sad": {"d": 123123}}, "sad.d.d.s..s..a.", "default val", "default val"),
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
        ("", 444, 444),
        (["asd", "asd", "ddf"], "str h", {"asd": {"asd": {"ddf": "str h"}}}),
    ),
)
def test_create_nested_dict(*, path: str | list[str], value: T, expected_result: dict | T) -> None:
    assert create_nested_dict(path, value) == expected_result


@pytest.mark.parametrize(
    ("value", "expected_result"),
    (
        ("a string", "a string"),
        ("123", 123),
        ("0", 0),
        ("123456789123456789123456789123456789", 123456789123456789123456789123456789),
    ),
)
def test_maybe_int(*, value: T, expected_result: int | T) -> None:
    assert maybe_int(value) == expected_result
