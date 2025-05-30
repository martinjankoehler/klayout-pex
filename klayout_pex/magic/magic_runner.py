#
# --------------------------------------------------------------------------------
# SPDX-FileCopyrightText: 2024-2025 Martin Jan Köhler and Harald Pretl
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
import time
from typing import *

import os
import subprocess

from ..log import (
    info,
    # warning,
    rule,
    subproc,
)
from ..version import __version__


class MagicPEXMode(StrEnum):
    CC = "CC"
    RC = "RC"
    R = "R"
    DEFAULT = CC


class MagicShortMode(StrEnum):
    NONE = "none"
    RESISTOR = "resistor"
    VOLTAGE = "voltage"
    DEFAULT = NONE


class MagicMergeMode(StrEnum):
    NONE = "none"                  # don't merge parallel devices
    CONSERVATIVE = "conservative"  # merge devices with same L, W
    AGGRESSIVE = "aggressive"      # merge devices with same L
    DEFAULT = NONE


def prepare_magic_script(gds_path: str,
                         cell_name: str,
                         run_dir_path: str,
                         script_path: str,
                         output_netlist_path: str,
                         pex_mode: MagicPEXMode,
                         c_threshold: float,
                         r_threshold: float,
                         tolerance: float,
                         halo: Optional[float],
                         short_mode: MagicShortMode,
                         merge_mode: MagicMergeMode):
    gds_path = os.path.abspath(gds_path)
    run_dir_path = os.path.abspath(run_dir_path)
    output_netlist_path = os.path.abspath(output_netlist_path)

    halo_scale = 200.0
    halo_decl = '' if halo is None else f"\nextract halo {round(halo * halo_scale)}"

    script: str = ""
    match pex_mode:
        case MagicPEXMode.CC:
            script = f"""# Generated by kpex {__version__}
crashbackups stop
drc off
gds read {gds_path}
load {cell_name}
select top cell
flatten {cell_name}_flat
load {cell_name}_flat
cellname delete {cell_name} -noprompt
cellname rename {cell_name}_flat {cell_name}
select top cell
extract path {run_dir_path}{halo_decl}
extract all
ext2spice short {short_mode}
ext2spice merge {merge_mode}
ext2spice cthresh {c_threshold}
ext2spice subcircuits top on
ext2spice format ngspice
ext2spice -p {run_dir_path} -o {output_netlist_path}
quit -noprompt"""
        case MagicPEXMode.RC:
            script = f"""# Generated by kpex {__version__}
crashbackups stop
drc off
gds read {gds_path}
load {cell_name}
select top cell
flatten {cell_name}_flat
load {cell_name}_flat
cellname delete {cell_name} -noprompt
cellname rename {cell_name}_flat {cell_name}
select top cell
extract path {run_dir_path}{halo_decl}
extract do resistance
extract all
ext2sim labels on
ext2sim
extresist tolerance {tolerance}
extresist all
ext2spice short {short_mode}
ext2spice merge {merge_mode}
ext2spice cthresh {c_threshold}
ext2spice rthresh {r_threshold}
ext2spice extresist on
ext2spice subcircuits top on
ext2spice format ngspice
ext2spice -p {run_dir_path} -o {output_netlist_path}
quit -noprompt
"""
        case MagicPEXMode.R:
            script = f"""# Generated by kpex {__version__}
crashbackups stop
drc off
gds read {gds_path}
load {cell_name}
select top cell
flatten {cell_name}_flat
load {cell_name}_flat
cellname delete {cell_name} -noprompt
cellname rename {cell_name}_flat {cell_name}
select top cell
extract path {run_dir_path}{halo_decl}
extract do resistance
extract no capacitance
extract no coupling
extract all
ext2sim labels on
ext2sim
extresist tolerance {tolerance}
extresist all
ext2spice short {short_mode}
ext2spice merge {merge_mode}
ext2spice rthresh {r_threshold}
ext2spice extresist on
ext2spice subcircuits top on
ext2spice format ngspice
ext2spice -p {run_dir_path} -o {output_netlist_path}
quit -noprompt
"""

    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script)

def run_magic(exe_path: str,
              magicrc_path: str,
              script_path: str,
              log_path: str):
    args = [
        exe_path,
        '-dnull',                      #
        '-noconsole',                  #
        '-rcfile',                     #
        magicrc_path,                  #
        script_path,                   # TCL script
    ]

    info('Calling MAGIC')
    subproc(f"{' '.join(args)}, output file: {log_path}")

    rule('MAGIC Output')

    start = time.time()

    proc = subprocess.Popen(args,
                            stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            universal_newlines=True,
                            text=True)
    with open(log_path, 'w', encoding='utf-8') as f:
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            subproc(line[:-1])  # remove newline
            f.writelines([line])
    proc.wait()

    duration = time.time() - start

    rule()

    if proc.returncode == 0:
        info(f"MAGIC succeeded after {'%.4g' % duration}s")
    else:
        raise Exception(f"MAGIC failed with status code {proc.returncode} after {'%.4g' % duration}s, "
                        f"see log file: {log_path}")

