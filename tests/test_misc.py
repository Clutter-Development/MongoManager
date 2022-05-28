import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize("abc", (1, 2, 3))
async def test_1(abc):
    assert abc in [1, 2], "Fail"
