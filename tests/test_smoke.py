# SPDX-FileCopyrightText: 2023 Alexander Sosedkin <monk@unboiled.info>
# SPDX-License-Identifier: GPL-3.0

"""Smoke-test for aiosqlitemydataclass."""

import dataclasses

import pytest

from aiosqlitemydataclass import Database, primary_key


@dataclasses.dataclass(frozen=True)
class Post:
    """Example parent class."""

    id: int = dataclasses.field(metadata=primary_key())  # noqa: A003
    text: str


@dataclasses.dataclass(frozen=True)
class Comment:
    """Example child class."""

    id: int = dataclasses.field(metadata=primary_key({}))  # noqa: A003
    post_id: int
    text: str


@pytest.mark.asyncio()
async def test_smoke() -> None:
    """Test storing and retrieving objects."""
    async with Database() as db:
        p0 = Post(0, 'post0')
        await db.put(p0)
        p0_retrieved = await db.get(Post, 0)
        assert (p0_retrieved.id, p0_retrieved.text) == (0, 'post0')
        assert p0 == p0_retrieved

        c0 = Comment(0, 0, 'comment0')
        c1 = Comment(1, 0, 'comment1')
        await db.put(c0)
        await db.put(c1)
        c0_retrieved = await db.get(Comment, 0)
        c1_retrieved = await db.get(Comment, 1)
        assert (c0_retrieved.id, c1_retrieved.id) == (0, 1)
        assert (c0_retrieved.post_id, c1_retrieved.post_id) == (0, 0)
        assert c0_retrieved.text == 'comment0'
        assert c1_retrieved.text == 'comment1'
        assert c0 == c0_retrieved
        assert c1 == c1_retrieved
