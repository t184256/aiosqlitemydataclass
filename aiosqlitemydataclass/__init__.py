# SPDX-FileCopyrightText: 2023 Alexander Sosedkin <monk@unboiled.info>
# SPDX-License-Identifier: GPL-3.0

"""aiosqlitemydataclass.

Store dataclasses in SQLite. async.
"""

from aiosqlitemydataclass.db import Database, primary_key

__all__ = ['Database', 'primary_key']
