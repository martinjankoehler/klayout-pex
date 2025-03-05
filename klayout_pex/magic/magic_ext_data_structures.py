#! /usr/bin/env python3
#
# --------------------------------------------------------------------------------
# SPDX-FileCopyrightText: 2024 Martin Jan Köhler and Harald Pretl
# Johannes Kepler University, Institute for Integrated Circuits.
#
# This file is part of KPEX
# (see https://github.com/martinjankoehler/klayout-pex).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
# SPDX-License-Identifier: GPL-3.0-or-later
# --------------------------------------------------------------------------------
#

from enum import StrEnum
from dataclasses import dataclass
from typing import *


@dataclass
class Port:
    net: str
    x_bot: int
    y_bot: int
    x_top: int
    y_top: int
    layer: str


@dataclass
class Node:
    net: str
    int_r: int
    fin_c: int
    x_bot: int
    y_bot: int
    layer: str


class DeviceType(StrEnum):
    FET = "fet"
    MOSFET = "mosfet"
    ASSYMETRIC = "asymmetric"
    BJT = "bjt"
    DEVRES = "devres"
    DEVCAP = "devcap"
    DEVCAPREV = "devcaprev"
    VSOURCE = "vsource"
    DIODE = "diode"
    PDIODE = "pdiode"
    NDIODE = "ndiode"
    SUBCKT = "subckt"
    RSUBCKT = "rsubckt"
    MSUBCKT = "msubckt"
    CSUBCKT = "csubckt"


@dataclass
class Device:
    device_type: DeviceType
    model: str
    x_bot: int
    y_bot: int
    x_top: int
    y_top: int


@dataclass
class ExtData:
    ports: List[Port]
    nodes: List[Node]
    devices: List[Device]


@dataclass
class ResNode:
    name: str
    int_r: int
    fin_c: int
    x_bot: int
    y_bot: int


@dataclass
class Resistor:
    node1: str
    node2: str
    value_ohm: float


@dataclass
class ResExtData:
    rnodes: List[ResNode]
    resistors: List[Resistor]

    def rnodes_by_name(self, name: str) -> List[ResNode]:
        return [n for n in self.rnodes if n.name == name]
