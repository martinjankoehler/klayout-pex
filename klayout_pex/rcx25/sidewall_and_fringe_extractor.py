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

import math

import klayout.db as kdb

from ..log import (
    info,
    warning
)
from ..tech_info import TechInfo

from .geometry_restorer import GeometryRestorer
from .extraction_results import *
from .extraction_reporter import ExtractionReporter
from .polygon_utils import find_polygon_with_nearest_edge
from .types import EdgeInterval, EdgeNeighborhood, EdgeNeighborhoodChild, EdgeNeighborhoodChildKind


class SidewallAndFringeExtractor:
    def __init__(self,
                 all_layer_names: List[LayerName],
                 layer_regions_by_name: Dict[LayerName, kdb.Region],
                 dbu: float,
                 tech_info: TechInfo,
                 results: CellExtractionResults,
                 report: ExtractionReporter):
        self.all_layer_names = all_layer_names
        self.layer_regions_by_name = layer_regions_by_name
        self.dbu = dbu
        self.tech_info = tech_info
        self.results = results
        self.report = report

    def extract(self):
        for idx, (layer_name, layer_region) in enumerate(self.layer_regions_by_name.items()):
            other_layer_names = [oln for oln in self.all_layer_names if oln != layer_name]
            other_layer_regions = [
                r for ln, r in self.layer_regions_by_name.items()
                if ln != layer_name
            ]

            en_visitor = self.PEXEdgeNeighborhoodVisitor(
                children_description=[EdgeNeighborhoodChild(EdgeNeighborhoodChildKind.SIDEWALL, layer_name)] +
                                     [EdgeNeighborhoodChild(EdgeNeighborhoodChildKind.OTHER_LAYER, name)
                                      for name in other_layer_names],
                inside_layer_name=layer_name,
                dbu=self.dbu,
                tech_info=self.tech_info,
                results=self.results,
                report=self.report
            )

            en_children = [
                # kdb.CompoundRegionOperationNode.new_primary(),
                kdb.CompoundRegionOperationNode.new_foreign()
            ]
            en_children += [kdb.CompoundRegionOperationNode.new_secondary(other_layer_region)
                            for other_layer_region in other_layer_regions]

            side_halo_um = self.tech_info.tech.process_parasitics.side_halo
            side_halo_dbu = int(side_halo_um / self.dbu) + 1  # add 1 nm to halo

            en_node = kdb.CompoundRegionOperationNode.new_edge_neighborhood(
                children=en_children,
                visitor=en_visitor,
                bext=-1, # NOTE: subtract 1 dbu to suppress quasi-empty contributions (will also suppress 90° edges)
                eext=-1, # NOTE: subtract 1 dbu to suppress quasi-empty contributions (will also suppress 90° edges)
                din=0,
                dout=side_halo_dbu # dout
            )

            layer_region.complex_op(en_node)

    # ------------------------------------------------------------------------

    class PEXEdgeNeighborhoodVisitor(kdb.EdgeNeighborhoodVisitor):
        def __init__(self,
                     children_description: List[EdgeNeighborhoodChild],
                     inside_layer_name: LayerName,
                     dbu: float,
                     tech_info: TechInfo,
                     results: CellExtractionResults,
                     report: ExtractionReporter):
            super().__init__()

            self.children_description = children_description
            self.inside_layer_name = inside_layer_name
            self.dbu = dbu
            self.tech_info = tech_info
            self.results = results
            self.report = report

        def begin_polygon(self,
                          layout: kdb.Layout,
                          cell: kdb.Cell,
                          polygon: kdb.Polygon):
            pass

        def end_polygon(self):
            pass

        def on_edge(self,
                    layout: kdb.Layout,
                    cell: kdb.Cell,
                    edge: kdb.EdgeWithProperties,
                    neighborhood: EdgeNeighborhood):
            #
            # NOTE: this complex operation will automatically rotate every edge to be on the x-axis
            #       going from 0 to edge.length
            #       so we only have to consider the y-axis to get the near and far distances
            #
            geometry_restorer = GeometryRestorer(self.to_original_trans(edge))

            for edge_interval, polygons_by_child in neighborhood:
                if not polygons_by_child:
                    continue

                for child_index, polygons in polygons_by_child.items():
                    cd = self.children_description[child_index]

                    match cd.kind:
                        case EdgeNeighborhoodChildKind.SIDEWALL:
                            # NOTE: use only the nearest polygon,
                            #       as the others are laterally shielded by the nearer ones

                            distance, nearest_polygon = find_polygon_with_nearest_edge(
                                polygons_on_same_layer=polygons
                            )

                            self.emit_sidewall(
                                layer_name=self.inside_layer_name,
                                edge=edge,
                                edge_interval=edge_interval,
                                polygon=nearest_polygon,
                                geometry_restorer=geometry_restorer
                            )

                        case EdgeNeighborhoodChildKind.OTHER_LAYER:
                            for polygon in polygons:
                                self.emit_fringe(
                                    inside_layer_name=self.inside_layer_name,
                                    outside_layer_name=cd.layer_name,
                                    edge=edge,
                                    edge_interval=edge_interval,
                                    polygon=polygon,
                                    geometry_restorer=geometry_restorer
                                )

        def emit_sidewall(self,
                          layer_name: LayerName,
                          edge: kdb.EdgeWithProperties,
                          edge_interval: EdgeInterval,
                          polygon: kdb.PolygonWithProperties,
                          geometry_restorer: GeometryRestorer):
            net1 = edge.property('net')
            net2 = polygon.property('net')
            sidewall_cap_spec = self.tech_info.sidewall_cap_by_layer_name[layer_name]

            # TODO!

            # NOTE: this method is always called for a single nearest edge (line), so the
            #       polygons have 4 points.
            #       Polygons points are sorted clockwise, so the edge
            #       that goes from right-to-left is the nearest edge
            # nearby_opposing_edge = [e for e in nearest_lateral_shape[1].each_edge() if e.d().x < 0][-1]
            # nearby_opposing_edge_trans = geometry_restorer.restore_edge(edge) * nearby_opposing_edge

            # C = Csidewall * l * t / s
            # C = Csidewall * l / s

            avg_length = edge_interval[1] - edge_interval[0]
            avg_distance = min(polygon.bbox().p1.y, polygon.bbox().p2.y)

            outside_edge = [e for e in polygon.each_edge() if e.d().x < 0][-1]

            length_um = avg_length * self.dbu
            distance_um = avg_distance * self.dbu

            # NOTE: dividing by 2 (like MAGIC this not bidirectional),
            #       but we count 2 sidewall contributions (one for each side of the cap)
            cap_femto = ((length_um * sidewall_cap_spec.capacitance)
                         / (distance_um + sidewall_cap_spec.offset)
                         / 2.0  # non-bidirectional (half)
                         / 1000.0)  # aF -> fF

            info(f"(Sidewall) layer {layer_name}: Nets {net1} <-> {net2}: {round(cap_femto, 5)} fF")

            swk = SidewallKey(layer=layer_name, net1=net1, net2=net2)
            sw_cap = SidewallCap(key=swk,
                                 cap_value=cap_femto,
                                 distance=distance_um,
                                 length=length_um,
                                 tech_spec=sidewall_cap_spec)
            self.results.add_sidewall_cap(sw_cap)

            self.report.output_sidewall(
                sidewall_cap=sw_cap,
                inside_edge=geometry_restorer.restore_edge_interval(edge_interval),
                outside_edge=geometry_restorer.restore_edge(outside_edge)
            )

        def emit_fringe(self,
                        inside_layer_name: LayerName,
                        outside_layer_name: LayerName,
                        edge: kdb.EdgeWithProperties,
                        edge_interval: EdgeInterval,
                        polygon: kdb.PolygonWithProperties,
                        geometry_restorer: GeometryRestorer):
            inside_net_name = self.tech_info.internal_substrate_layer_name \
                if inside_layer_name == self.tech_info.internal_substrate_layer_name \
                else edge.property('net')

            outside_net_name = self.tech_info.internal_substrate_layer_name \
                if outside_layer_name == self.tech_info.internal_substrate_layer_name \
                else polygon.property('net')

            # NOTE: overlap_cap_by_layer_names is top/bot (dict is not symmetric)
            overlap_cap_spec = self.tech_info.overlap_cap_by_layer_names[inside_layer_name].get(outside_layer_name,
                                                                                                None)
            if not overlap_cap_spec:
                overlap_cap_spec = self.tech_info.overlap_cap_by_layer_names[outside_layer_name][inside_layer_name]

            substrate_cap_spec = self.tech_info.substrate_cap_by_layer_name[inside_layer_name]
            sideoverlap_cap_spec = self.tech_info.side_overlap_cap_by_layer_names[inside_layer_name][
                outside_layer_name]

            bbox = polygon.bbox()

            if not polygon.is_box():
                warning(f"Side overlap, outside polygon {polygon} is not a box. "
                        f"Currently, only boxes are supported, will be using bounding box {bbox}")

            distance_near = bbox.p1.y  # + 1
            if distance_near < 0:
                distance_near = 0
            distance_far = bbox.p2.y  # - 2
            if distance_far < 0:
                distance_far = 0
            try:
                assert distance_near >= 0
                assert distance_far >= distance_near
            except AssertionError:
                print()
                raise

            if distance_far == distance_near:
                return

            distance_near_um = distance_near * self.dbu
            distance_far_um = distance_far * self.dbu

            # NOTE: overlap scaling is 1/50  (see MAGIC ExtTech)
            alpha_scale_factor = 0.02 * 0.01 * 0.5 * 200.0
            alpha_c = overlap_cap_spec.capacitance * alpha_scale_factor

            # see Magic ExtCouple.c L1164
            cnear = (2.0 / math.pi) * math.atan(alpha_c * distance_near_um)
            cfar = (2.0 / math.pi) * math.atan(alpha_c * distance_far_um)

            # "cfrac" is the fractional portion of the fringe cap seen
            # by tile tp along its length.  This is independent of the
            # portion of the boundary length that tile tp occupies.
            cfrac = cfar - cnear

            # The fringe portion extracted from the substrate will be
            # different than the portion added to the coupling layer.
            sfrac: float

            # see Magic ExtCouple.c L1198
            alpha_s = substrate_cap_spec.area_capacitance / alpha_scale_factor
            if alpha_s != alpha_c:
                snear = (2.0 / math.pi) * math.atan(alpha_s * distance_near_um)
                sfar = (2.0 / math.pi) * math.atan(alpha_s * distance_far_um)
                sfrac = sfar - snear
            else:
                sfrac = cfrac

            if outside_layer_name == self.tech_info.internal_substrate_layer_name:
                cfrac = sfrac

            edge_interval_length = edge_interval[1] - edge_interval[0]
            edge_interval_length_um = edge_interval_length * self.dbu

            cap_femto = (cfrac * edge_interval_length_um *
                         sideoverlap_cap_spec.capacitance / 1000.0)
            if cap_femto > 0.0:
                info(f"(Side Overlap) "
                     f"{inside_layer_name}({inside_net_name})-{outside_layer_name}({outside_net_name}): "
                     f"{round(cap_femto, 5)} fF, "
                     f"edge interval length = {round(edge_interval_length_um, 2)} µm")

                sok = SideOverlapKey(layer_inside=inside_layer_name,
                                     net_inside=inside_net_name,
                                     layer_outside=outside_layer_name,
                                     net_outside=outside_net_name)
                soc = SideOverlapCap(key=sok, cap_value=cap_femto)
                self.results.add_sideoverlap_cap(soc)

                self.report.output_sideoverlap(#
                    sideoverlap_cap=soc,
                    inside_edge=geometry_restorer.restore_edge_interval(edge_interval),
                    outside_polygon=geometry_restorer.restore_polygon(polygon)
                )

