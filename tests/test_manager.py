import asyncio
import os
from typing import Any

import pytest

from mongo_manager import MongoManager

db = MongoManager(os.getenv("MONGO_URI"), database="MongoManagerTest")  # type: ignore


@pytest.fixture
def event_loop():
    loop = asyncio.get_event_loop()

    yield loop

    pending = asyncio.tasks.all_tasks(loop)
    loop.run_until_complete(asyncio.gather(*pending))
    loop.run_until_complete(asyncio.sleep(1))

    loop.close()


@pytest.mark.asyncio
async def test_setup():
    await db._db.test.drop()  # Nuking the collection so the old tests don't break this.


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("path", "value", "query", "expected_result"),
    (
        (
            "test._id name",
            {"some_key": 123},
            {"_id": "_id name"},
            {"_id": "_id name", "some_key": 123},
        ),
        (
            "test.123123123123123123123",
            {"asd": "def"},
            {"_id": 123123123123123123123},
            {"_id": 123123123123123123123, "asd": "def"},
        ),
        (
            "test.another _id.a var",
            "some value",
            {"_id": "another _id"},
            {"_id": "another _id", "a var": "some value"},
        ),
        (
            "test.67676767676767.object_h.k1.2",
            6.9,
            {"_id": 67676767676767},
            {"_id": 67676767676767, "object_h": {"k1": {"2": 6.9}}},
        ),
    ),
)
async def test_manager_set(*, path: str, value: Any, query: dict, expected_result: Any):
    await db.set(path, value)
    assert await db._db.test.find_one(query) == expected_result
