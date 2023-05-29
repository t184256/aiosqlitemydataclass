# SPDX-FileCopyrightText: 2023 Alexander Sosedkin <monk@unboiled.info>
# SPDX-License-Identifier: GPL-3.0

import dataclasses
import typing

class DataclassInstance(typing.Protocol):
    __dataclass_fields__: \
            typing.ClassVar[dict[str, dataclasses.Field[typing.Any]]]

Dataclass = type[DataclassInstance]
