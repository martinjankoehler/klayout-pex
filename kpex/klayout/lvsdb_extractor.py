from __future__ import annotations

import tempfile
from typing import *
from dataclasses import dataclass
from rich.pretty import pprint

import klayout.db as kdb

from ..log import (
    console,
    debug,
    info,
    warning,
    error
)

from ..tech_info import TechInfo


GDSPair = Tuple[int, int]


@dataclass
class KLayoutExtractedLayerInfo:
    index: int
    lvs_layer_name: str        # NOTE: this can be computed, so gds_pair is preferred
    gds_pair: GDSPair
    region: kdb.Region


@dataclass
class KLayoutMergedExtractedLayerInfo:
    source_layers: List[KLayoutExtractedLayerInfo]
    gds_pair: GDSPair


@dataclass
class KLayoutExtractionContext:
    lvsdb: kdb.LayoutToNetlist
    dbu: float
    top_cell: kdb.Cell
    layer_map: Dict[int, kdb.LayerInfo]
    cell_mapping: kdb.CellMapping
    target_layout: kdb.Layout
    extracted_layers: Dict[GDSPair, KLayoutMergedExtractedLayerInfo]
    unnamed_layers: List[KLayoutExtractedLayerInfo]

    @classmethod
    def prepare_extraction(cls,
                           lvsdb: kdb.LayoutToNetlist,
                           top_cell: str,
                           tech: TechInfo) -> KLayoutExtractionContext:
        dbu = lvsdb.internal_layout().dbu
        target_layout = kdb.Layout()
        target_layout.dbu = dbu
        top_cell = target_layout.create_cell(top_cell)

        # CellMapping
        #   mapping of internal layout to target layout for the circuit mapping
        #   https://www.klayout.de/doc-qt5/code/class_CellMapping.html
        # ---
        # https://www.klayout.de/doc-qt5/code/class_LayoutToNetlist.html#method18
        # Creates a cell mapping for copying shapes from the internal layout to the given target layout
        cm = lvsdb.cell_mapping_into(target_layout,  # target layout
                                     top_cell,
                                     True)  # with_device_cells

        lm = cls.build_LVS_layer_map(target_layout=target_layout, lvsdb=lvsdb, tech=tech)

        net_name_prop_num = 1

        # Build a full hierarchical representation of the nets
        # https://www.klayout.de/doc-qt5/code/class_LayoutToNetlist.html#method14
        # hier_mode = None
        hier_mode = kdb.LayoutToNetlist.BuildNetHierarchyMode.BNH_Flatten
        # hier_mode = kdb.LayoutToNetlist.BuildNetHierarchyMode.BNH_SubcircuitCells

        lvsdb.build_all_nets(
            cmap=cm,               # mapping of internal layout to target layout for the circuit mapping
            target=target_layout,  # target layout
            lmap=lm,               # maps: target layer index => net regions
            hier_mode=hier_mode,   # hier mode
            netname_prop=net_name_prop_num,
            circuit_cell_name_prefix="CIRCUIT_",
            device_cell_name_prefix=None  # "DEVICE_"
        )  # property name to which to attach the net name

        extracted_layers, unnamed_layers = cls.nonempty_extracted_layers(lvsdb=lvsdb, tech=tech)

        return KLayoutExtractionContext(
            lvsdb=lvsdb,
            dbu=dbu,
            top_cell=top_cell,
            layer_map=lm,
            cell_mapping=cm,
            target_layout=target_layout,
            extracted_layers=extracted_layers,
            unnamed_layers=unnamed_layers
        )

    @staticmethod
    def build_LVS_layer_map(target_layout: kdb.Layout,
                            lvsdb: kdb.LayoutToNetlist,
                            tech: TechInfo) -> Dict[int, kdb.LayerInfo]:
        # NOTE: currently, the layer numbers are auto-assigned
        # by the sequence they occur in the LVS script, hence not well defined!
        # build a layer map for the layers that correspond to original ones.

        # https://www.klayout.de/doc-qt5/code/class_LayerInfo.html
        lm: Dict[int, kdb.LayerInfo] = {}

        if not hasattr(lvsdb, "layer_indexes"):
            raise Exception("Needs at least KLayout version 0.29.2")

        for layer_index in lvsdb.layer_indexes():
            lname = lvsdb.layer_name(layer_index)

            gds_pair = tech.gds_pair_for_computed_layer_name.get(lname, None)
            if not gds_pair:
                li = lvsdb.internal_layout().get_info(layer_index)
                if li != kdb.LayerInfo():
                    gds_pair = (li.layer, li.datatype)

            if gds_pair is not None:
                target_layer_index = target_layout.layer(*gds_pair)  # Creates a new internal layer!
                region = lvsdb.layer_by_index(layer_index)
                lm[target_layer_index] = region

        return lm

    @staticmethod
    def nonempty_extracted_layers(lvsdb: kdb.LayoutToNetlist,
                                  tech: TechInfo) -> Tuple[Dict[GDSPair, KLayoutMergedExtractedLayerInfo], List[KLayoutExtractedLayerInfo]]:
        # https://www.klayout.de/doc-qt5/code/class_LayoutToNetlist.html#method18
        nonempty_layers: Dict[GDSPair, KLayoutMergedExtractedLayerInfo] = {}

        unnamed_layers: List[KLayoutExtractedLayerInfo] = []

        for idx, ln in enumerate(lvsdb.layer_names()):
            layer = lvsdb.layer_by_name(ln)
            if layer.count() >= 1:
                gds_pair = tech.gds_pair_for_computed_layer_name.get(ln, None)
                if not gds_pair:
                    warning(f"Unable to find info about extracted LVS layer '{ln}'")
                    gds_pair = (1000 + idx, 20)
                    linfo = KLayoutExtractedLayerInfo(
                        index=idx,
                        lvs_layer_name=ln,
                        gds_pair=gds_pair,
                        region=layer
                    )
                    unnamed_layers.append(linfo)
                    continue

                linfo = KLayoutExtractedLayerInfo(
                    index=idx,
                    lvs_layer_name=ln,
                    gds_pair=gds_pair,
                    region=layer
                )

                entry = nonempty_layers.get(gds_pair, None)
                if entry:
                    entry.source_layers.append(linfo)
                else:
                    nonempty_layers[gds_pair] = KLayoutMergedExtractedLayerInfo(
                        source_layers=[linfo],
                        gds_pair=gds_pair,
                    )

        return nonempty_layers, unnamed_layers

    def shapes_of_net(self, gds_pair: GDSPair, net: kdb.Net) -> Optional[kdb.Region]:
        lyr = self.extracted_layers.get(gds_pair, None)
        if not lyr:
            return None

        shapes: kdb.Region

        match len(lyr.source_layers):
            case 0:
                raise AssertionError('Internal error: Empty list of source_layers')
            case 1:
                shapes = self.lvsdb.shapes_of_net(net, lyr.source_layers[0].region, True)
            case _:
                shapes = kdb.Region()
                for sl in lyr.source_layers:
                    shapes += self.lvsdb.shapes_of_net(net, sl.region, True)
                # shapes.merge()

        return shapes

    def shapes_of_layer(self, gds_pair: GDSPair) -> Optional[kdb.Region]:
        lyr = self.extracted_layers.get(gds_pair, None)
        if not lyr:
            return None

        shapes: kdb.Region

        match len(lyr.source_layers):
            case 0:
                raise AssertionError('Internal error: Empty list of source_layers')
            case 1:
                shapes = lyr.source_layers[0].region
            case _:
                shapes = kdb.Region()
                for sl in lyr.source_layers:
                    shapes += sl.region
                # shapes.merge()

        return shapes


