from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Literal, overload

from motor.motor_asyncio import AsyncIOMotorClient

from .misc import create_nested_dict, find_in_nested_dict, maybe_int

if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase

__all__ = ("MongoManager",)


class MongoManager:
    def __init__(self, connect_url: str, port: int | None = None, /, *, database: str) -> None:
        """Initialize the MongoManager class.

        Args:
            connect_url (str): The MongoDB URI to use to connect to the database.
            port (int | None, optional): The port of the MongoDB instance, used when the db is hosted locally. Defaults to None.
            database (str): The database to use.
        """
        self._client = AsyncIOMotorClient(connect_url, port)
        self._db: AsyncIOMotorDatabase = self._client[database]

    def _parse_path(self, path: str, /) -> tuple[AsyncIOMotorCollection, str | int, str]:  # type: ignore
        """Parses a path string and returns the excess, a mongo collection and a str or int.

        Args:
            path (str): The path to parse.

        Raises:
            ValueError: If the path is too short. Minimum 2.

        Returns:
            tuple[AsyncIOMotorCollection, str | int, str]: The excess path as a list, the MongoDB collection, the _id of the document which can be a str or an int.
        """
        path: list[str] = path.split(".", 2)

        if len(path) < 2:
            raise ValueError("Path must be at least 2 elements long: Collection and _id.")

        collection = self._db[path.pop(0)]
        _id = maybe_int(path.pop(0))

        return collection, _id, next(iter(path), "")

    @overload
    async def ping(self, *, return_is_alive: Literal[False] = False) -> float:
        ...

    @overload
    async def ping(self, *, return_is_alive: Literal[True] = ...) -> tuple[float, bool]:
        ...

    async def ping(self, *, return_is_alive: bool = False) -> float | tuple[float, bool]:
        """Pings the database and returns the time it took to respond. If return_is_alive is True, it returns a tuple of the time and whether the database is alive.

        Args:
            return_is_alive (bool, optional): If True, it returns a tuple of the time and whether the database is alive. Defaults to False.

        Returns:
            int | float | tuple[int | float, bool]: The time it took to respond. If return_is_alive is True, it returns a tuple of the time and whether the database is alive.
        """
        ts = time.time()
        response = await self._db.command("ping")
        ts = time.time() - ts
        if return_is_alive:
            return ts, bool(response.get("ok", False))
        return ts

    async def get(self, path: str, /, *, default: Any = None) -> Any:
        """Fetches the variable from the database. If the path is 2 keys long, the whole document is returned (or default).

        Args:
            path (str): The path to the variable. Must be at least 2 elements long: Collection and _id.
            default (Any, optional): The default value to return if the variable is not found.

        Returns:
            Any: The value of the variable.
        """
        collection, _id, path = self._parse_path(path)

        return find_in_nested_dict(
            await collection.find_one({"_id": _id}, {"_id": 0, path: 1} if path else None),
            path,
            default=default,
        )

    async def set(self, path: str, value: Any, /) -> None:
        """Sets the variable in the database.

        Args:
            path (str): The path to the variable. Must be at least 2 elements long: Collection and _id.
            value (Any): The value to set the key to.
        """
        collection, _id, path = self._parse_path(path)

        if not path and not isinstance(value, dict):
            raise ValueError(
                "Value must be a dictionary if whole document is wanted to be updated."
            )

        if await collection.find_one({"_id": _id}, {"_id": 1}):
            val = {"$set": {path: value} if path else value}
            await collection.update_one({"_id": _id}, val)
        else:
            val = create_nested_dict(path, value) if path else value
            await collection.insert_one({"_id": _id, **val})

    async def push(self, path: str, value: Any, /, *, allow_duplicates: bool = True) -> bool:
        """Appends the variable to a list in the database.

        Args:
            path (str): The path to the list. Must be at least 3 elements long: Collection and _id.
            value (Any): The value to append to the list.
            allow_duplicates (bool, optional): If true, the value will be appended to the list. If false, the value will be appended if it is not in the list.

        Raises:
            ValueError: If the path is too short.

        Returns:
            bool: If the value was pushed.
        """
        collection, _id, path = self._parse_path(path)
        if not path:
            raise ValueError(
                "Path must be at least 3 elements long: Collection, _id and key for the push operation."
            )

        if (doc := await collection.find_one({"_id": _id})) is None:
            await collection.insert_one({"_id": _id, **create_nested_dict(path, [value])})  # type: ignore
            return True
        if allow_duplicates or value not in find_in_nested_dict(doc, path, default=set()):
            await collection.update_one({"_id": _id}, {"$push": {path: value}})
            return True

        return False

    async def pull(self, path: str, value: Any, /) -> bool:
        """Removes the variable from a list in the database.

        Args:
            path (str): The path to the list. Must be at least 3 elements long: Collection and _id.
            value (Any): The value to remove from the list.

        Raises:
            ValueError: If the path is too short.

        Returns:
            bool: If the value was removed.
        """
        collection, _id, path = self._parse_path(path)

        if not path:
            raise ValueError(
                "Path must be at least 3 elements long: Collection, _id and key for the pull operation."
            )

        if value in find_in_nested_dict(
            await collection.find_one({"_id": _id}, {path: 1}), path, default=set()
        ):
            await collection.update_one({"_id": _id}, {"$pull": {path: value}})
            return True

        return False

    async def rem(self, path: str, /) -> None:  # type: ignore
        """Removes the col/doc/var from the database.

        Args:
            path (str): The path to the col/doc/var. Must be at least 1 element long.

        Raises:
            ValueError: If the path is too short.
        """
        path: list[str] = path.split(".", 2)

        if not path:
            raise ValueError("Path not given. Cannot delete entire database.")

        collection = self._db[path.pop(0)]

        if not path:
            await collection.drop()
            return

        _id = maybe_int(path.pop(0))

        if not path:
            await collection.delete_one({"_id": _id})
        else:
            await collection.update_one({"_id": _id}, {"$unset": {path[0]: ""}})
