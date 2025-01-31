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

from functools import cached_property
from typing import *

import klayout.rdb as rdb
import klayout.db as kdb

from .extraction_results import *


VarShapes = kdb.Shapes | kdb.Region | List[kdb.Edge] | List[kdb.Polygon]


class ExtractionReporter:
    def __init__(self,
                 cell_name: str,
                 dbu: float):
        self.report = rdb.ReportDatabase(f"PEX {cell_name}")
        self.cell = self.report.create_cell(cell_name)
        self.dbu_trans = kdb.CplxTrans(mag=dbu)
        self.category_name_counter: Dict[str, int] = defaultdict(int)

    @cached_property
    def cat_common(self) -> rdb.RdbCategory:
        return self.report.create_category('Common')

    @cached_property
    def cat_overlap(self) -> rdb.RdbCategory:
        return self.report.create_category("Overlap")

    @cached_property
    def cat_sidewall(self) -> rdb.RdbCategory:
        return self.report.create_category("Sidewall")

    @cached_property
    def cat_fringe(self) -> rdb.RdbCategory:
        return self.report.create_category("Fringe / Side Overlap")

    def save(self, path: str):
        self.report.save(path)

    def output_shapes(self,
                      parent_category: rdb.RdbCategory,
                      category_name: str,
                      shapes: VarShapes):
        rdb_cat = self.report.create_category(parent_category, category_name)
        self.report.create_items(self.cell.rdb_id(),  ## TODO: if later hierarchical mode is introduced
                                 rdb_cat.rdb_id(),
                                 self.dbu_trans,
                                 shapes)

    def output_sidewall(self,
                        sidewall_cap: SidewallCap,
                        inside_edge: kdb.Edge,
                        outside_edge: kdb.Edge):
        cat_sidewall_layer = self.report.create_category(self.cat_sidewall,
                                                         f"layer={sidewall_cap.key.layer}")
        cat_sidewall_net_inside = self.report.create_category(cat_sidewall_layer,
                                                              f'inside={sidewall_cap.key.net1}')
        cat_sidewall_net_outside = self.report.create_category(cat_sidewall_net_inside,
                                                               f'outside={sidewall_cap.key.net2}')
        self.category_name_counter[cat_sidewall_net_outside.path()] += 1

        self.output_shapes(
            cat_sidewall_net_outside,
            f"#{self.category_name_counter[cat_sidewall_net_outside.path()]}: "
            f"len {sidewall_cap.length} µm, "
            f"distance {sidewall_cap.distance} µm, {sidewall_cap.cap_value} fF",
            [inside_edge, outside_edge]
        )
