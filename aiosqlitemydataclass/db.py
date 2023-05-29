# SPDX-FileCopyrightText: 2023 Alexander Sosedkin <monk@unboiled.info>
# SPDX-License-Identifier: GPL-3.0

"""Database."""

from __future__ import annotations

import dataclasses
import sqlite3
import typing

if typing.TYPE_CHECKING:
    import types

    from aiosqlitemydataclass._extra_types import Dataclass, DataclassInstance
    D = typing.TypeVar('D', bound=DataclassInstance)
    T = typing.TypeVar('T')
    PrimaryKeyValues = typing.Any  # don't know how to spec it any better
    FieldMetadata = types.MappingProxyType[typing.Any, typing.Any]
    AnyDict = dict[typing.Any, typing.Any]

import aiosqlite


def primary_key(old_metadata: AnyDict | None = None) -> AnyDict:
    """Modify field metadata to mark it as primary key."""
    return _augment_metadata(old_metadata, {'primary_key': True})


def _augment_metadata(old_metadata: AnyDict | None,
                      extra_metadata: AnyDict,
                      key: str = 'aiosqlitemydataclass') -> AnyDict:
    if old_metadata is None:
        old_metadata = {}
    if 'aiosqlitemydataclass' not in old_metadata:
        return old_metadata | {key: extra_metadata}
    return old_metadata | {key: old_metadata[key] | extra_metadata}


def is_primary_key(metadata: FieldMetadata) -> bool:
    try:
        return metadata['aiosqlitemydataclass']['primary_key'] is True
    except KeyError:
        return False


def query_template(query: str) -> str:
    """Prettify an SQL query template."""
    return ' '.join(line.strip() for line in query.split('\n')).strip()


class DataclassMetadata:
    tablename: str
    all_field_names: tuple[str, ...]
    primary_key_names: tuple[str, ...]
    query_create: str

    def __init__(self, dataclass: Dataclass) -> None:
        self.tablename = str(dataclass.__qualname__).replace('.', '_')  # ugly
        all_fields = tuple(dataclasses.fields(dataclass))
        self.all_field_names = tuple(f.name for f in all_fields)
        primary_key_fields = tuple(f for f in all_fields
                                   if is_primary_key(f.metadata))
        self.primary_key_names = tuple(f.name for f in primary_key_fields)
        self.query_create = query_template(f'''
            CREATE TABLE {self.tablename} (
              {', '.join(fn for fn in self.all_field_names)},
              PRIMARY KEY ({', '.join(fn for fn in self.primary_key_names)})
            )
        ''')
        self.query_upsert = query_template(f'''
            INSERT INTO {self.tablename}
              VALUES ({', '.join('?' * len(self.all_field_names))})
              ON CONFLICT ({', '.join(self.primary_key_names)})
              DO UPDATE SET {', '.join(f'{f}=?' for f in self.all_field_names)}
        ''')  # noqa: S608
        self.query_select = query_template(f'''
            SELECT * FROM {self.tablename}
              WHERE {' AND '.join(f'{f}=?' for f in self.primary_key_names)}
        ''')  # noqa: S608


class Database:
    """Database to persist dataclasses to."""

    _db_path: str
    _db: aiosqlite.Connection
    _dataclass_metadata: dict[Dataclass, DataclassMetadata]

    def __init__(self, path: str | None = None) -> None:
        """Initialize a database. `async with` to open it.

        `path=None` will use an in-memory database.
        """
        self._db_path = path or ':memory:'

    async def __aenter__(self) -> typing.Self:
        self._db = await aiosqlite.connect(self._db_path)
        self._dataclass_metadata = {}
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        await self._db.close()

    def _metadata(self, dataclass: Dataclass) -> DataclassMetadata:
        try:
            return self._dataclass_metadata[dataclass]
        except KeyError:
            metadata = DataclassMetadata(dataclass)
            self._dataclass_metadata[dataclass] = metadata
            return metadata

    async def _create_table(self, dataclass: Dataclass) -> None:
        metadata = self._metadata(dataclass)
        async with self._db.cursor() as cur:
            await cur.execute(metadata.query_create)

    async def _upsert(self, dataclass_obj: DataclassInstance) -> None:
        metadata = self._metadata(dataclass_obj.__class__)
        values = tuple(dataclasses.asdict(dataclass_obj).values())
        async with self._db.cursor() as cur:
            await cur.execute(metadata.query_upsert, values * 2)

    async def put(self, dataclass_obj: DataclassInstance) -> None:
        """Put a dataclass instance into database."""
        assert dataclasses.is_dataclass(dataclass_obj)
        try:
            await self._upsert(dataclass_obj)
        except sqlite3.OperationalError as ex:
            metadata = self._metadata(dataclass_obj.__class__)
            if ex.args[0] == f'no such table: {metadata.tablename}':
                # retry (TODO: more efficiently)
                await self._create_table(dataclass_obj.__class__)
                await self._upsert(dataclass_obj)
            else:
                raise  # pragma: no cover (just in case)

    async def get(self, dataclass: type[D],
                  *primary_key_values: PrimaryKeyValues) -> D:
        """Get a dataclass instance from database by primary key values."""
        metadata = self._metadata(dataclass)
        async with self._db.cursor() as cur:
            await cur.execute(metadata.query_select, primary_key_values)
            res = await cur.fetchone()
            return dataclass(*res)


__all__ = ['Database', 'primary_key']
