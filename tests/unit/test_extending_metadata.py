# SPDX-FileCopyrightText: 2023 Alexander Sosedkin <monk@unboiled.info>
# SPDX-License-Identifier: GPL-3.0

"""Tests for extending metadata."""

from aiosqlitemydataclass import primary_key


def test_primary_key() -> None:
    """Test for application of primary_key."""
    r = {'aiosqlitemydataclass': {'primary_key': True}}
    assert primary_key() == r
    assert primary_key({}) == r
    assert primary_key(primary_key()) == r
    assert primary_key(primary_key({})) == r

    base1 = {'something': 'else'}
    r1 = {'something': 'else', 'aiosqlitemydataclass': {'primary_key': True}}
    assert primary_key(base1) == r1
    assert primary_key(primary_key(base1)) == r1

    base2 = {'aiosqlitemydataclass': {'future_prop': 'x'}}
    r2 = {'aiosqlitemydataclass': {'primary_key': True, 'future_prop': 'x'}}
    assert primary_key(base2) == r2
    assert primary_key(primary_key(base2)) == r2
