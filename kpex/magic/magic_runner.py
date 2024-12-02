from enum import StrEnum
import re
import time
from typing import *

import os
import subprocess
import unittest

from kpex.log import (
    info,
    # warning,
    rule,
    subproc,
)
from kpex.version import __version__


class MagicPEXMode(StrEnum):
    CC = "CC"
    RC = "RC"
    DEFAULT = "CC"


def prepare_magic_script(gds_path: str,
                         cell_name: str,
                         run_dir_path: str,
                         script_path: str,
                         output_netlist_path: str,
                         pex_mode: MagicPEXMode,
                         c_threshold: float,
                         r_threshold: float,
                         halo: Optional[float]):
    gds_path = os.path.abspath(gds_path)
    run_dir_path = os.path.abspath(run_dir_path)
    output_netlist_path = os.path.abspath(output_netlist_path)

    halo_scale = 200.0

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
extract path {run_dir_path}{'' if halo is None else f"\nextract halo {round(halo * halo_scale)}"}
extract all
ext2spice cthresh {c_threshold}
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
extract path {run_dir_path}{'' if halo is None else f"\nextract halo {round(halo * halo_scale)}"}
extract do resistance
extract all
ext2sim labels on
ext2sim
extresist tolerance {r_threshold}
extresist all
ext2spice cthresh {c_threshold}
ext2spice rthresh {r_threshold}
ext2spice extresist on
ext2spice format ngspice
ext2spice -p {run_dir_path} -o {output_netlist_path}
quit -noprompt
"""
    with open(script_path, 'w') as f:
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

    info(f"Calling {' '.join(args)}, output file: {log_path}")

    start = time.time()

    proc = subprocess.Popen(args,
                            stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            universal_newlines=True,
                            text=True)
    with open(log_path, 'w') as f:
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
        raise Exception(f"MAGIC failed with status code {proc.returncode} after {'%.4g' % duration}s",
                        f"see log file: {log_path}")

