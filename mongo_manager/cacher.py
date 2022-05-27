from typing import Any

from lru import LRU

from .manager import MongoManager

__all__ = ("CachedMongoManager",)


class CachedMongoManager(MongoManager):
    def __init__(
        self, connect_url: str, port: int | None = None, /, *, database: str, max_items: int
    ) -> None:
        self._cache = LRU(max_items)
        super().__init__(connect_url, port, database=database)

    def uncache(self, key: str | list[str], /, *, match: bool = True) -> None:
        """Uncaches all kv pairs with the given path. If match is False, it will uncache all kv pairs that start with the path.

        Args:
            key (str | list[str]): The key(s) to uncache.
            match (bool, optional): If not to delete all keys starting with the path
        """
        if isinstance(key, list):
            for single_key in key:
                self.uncache(single_key, match=match)

        elif match:
            del self._cache[key]

        else:
            for key_ in self._cache.keys():
                if key_.startswith(key):
                    del self._cache[key_]

    async def get(self, path: str, /, *, default: Any = None) -> Any:
        """Fetches the variable from the database.

        Args:
            path (str): The path to the variable. Must be at least 2 elements long: Collection and _id.
            default (Any, optional): The default value to return if the variable is not found.

        Returns:
            Any: The value of the variable.
        """
        if path in self._cache:
            return self._cache[path]

        value = await super().get(path, default=default)
        self._cache[path] = value
        return value

    async def set(self, path: str, value: Any, /) -> None:
        await super().set(path, value)
        self.uncache(path)

    async def push(self, path: str, value: Any, /, *, allow_duplicates: bool = True) -> bool:
        val = await super().push(path, value, allow_duplicates=allow_duplicates)
        self.uncache(path)
        return val

    async def pull(self, path: str, value: Any, /) -> bool:
        val = await super().pull(path, value)
        self.uncache(path)
        return val

    async def rem(self, path: str, /) -> None:
        await super().rem(path)
        self.uncache(path)
