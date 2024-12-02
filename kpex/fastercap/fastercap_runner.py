import re
import time
from typing import *

import os
import subprocess
import unittest

from kpex.log import (
    debug,
    info,
    # warning,
    error
)
from .capacitance_matrix import CapacitanceMatrix


def run_fastercap(exe_path: str,
                  lst_file_path: str,
                  log_path: str,
                  tolerance: float):
    args = [
        exe_path,
        f"-b",                             # console mode, without GUI
        f"-a{tolerance}",  # stop when relative error lower than threshold
        lst_file_path
    ]
    info(f"Calling {' '.join(args)}, output file: {log_path}")

    start = time.time()
    proc = subprocess.run(args,
                          stdin=subprocess.DEVNULL,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT,
                          universal_newlines=True)
    duration = time.time() - start

    with open(log_path, 'w') as f:
        f.write(proc.stdout)

    if proc.returncode == 0:
        info(f"FasterCap succeeded after {'%.4g' % duration}s")

    if proc.returncode != 0:
        raise Exception(f"FasterCap failed with status code {proc.returncode}, "
                        f"see log file: {log_path}")


def fastercap_parse_capacitance_matrix(log_path: str) -> CapacitanceMatrix:
    with open(log_path, 'r') as f:
        rlines = f.readlines()
        rlines.reverse()

        # multiple iterations possible, find the last matrix
        for idx, line in enumerate(rlines):
            if line.strip() == "Capacitance matrix is:":
                m = re.match(r'^Dimension (\d+) x (\d+)$', rlines[idx-1])
                if not m:
                    raise Exception(f"Could not parse capacitor matrix dimensions")
                dim = int(m.group(1))
                conductor_names: List[str] = []
                rows: List[List[float]] = []
                for i in reversed(range(idx-1-dim, idx-1)):
                    line = rlines[i].strip()
                    cells = [cell.strip() for cell in line.split(' ')]
                    cells = list(filter(lambda c: len(c) >= 1, cells))
                    conductor_names.append(cells[0])
                    row = [float(cell)/1e6 for cell in cells[1:]]
                    rows.append(row)
                cm = CapacitanceMatrix(conductor_names=conductor_names, rows=rows)
                return cm

        raise Exception(f"Could not extract capacitance matrix from FasterCap log file {log_path}")


class Test(unittest.TestCase):
    @property
    def fastercap_testdata_dir(self) -> str:
        return os.path.realpath(os.path.join(__file__, '..', '..', '..', 'testdata', 'fastercap'))

    def test_fastercap_parse_capacitance_matrix(self):
        testdata_path = os.path.join(self.fastercap_testdata_dir, 'nmos_diode2_FasterCap_Output.txt')
        obtained_matrix = fastercap_parse_capacitance_matrix(log_path=testdata_path)
        self.assertEqual(10, len(obtained_matrix.rows))
        self.assertEqual(10, len(obtained_matrix.rows[0]))
        self.assertEqual(10, len(obtained_matrix.rows[1]))
        self.assertEqual(10, len(obtained_matrix.rows[2]))
        self.assertEqual(10, len(obtained_matrix.rows[3]))
        self.assertEqual(10, len(obtained_matrix.rows[4]))
        self.assertEqual(10, len(obtained_matrix.rows[5]))
        self.assertEqual(10, len(obtained_matrix.rows[6]))
        self.assertEqual(10, len(obtained_matrix.rows[7]))
        self.assertEqual(10, len(obtained_matrix.rows[8]))
        self.assertEqual(10, len(obtained_matrix.rows[9]))
        self.assertEqual(
            ['g1_7', 'g1_8', 'g1_9', 'g1_10', 'g1_11', 'g1_12', 'g1_13', 'g1_14', 'g1_15', 'g1_16'],
            obtained_matrix.conductor_names
        )

        output_path = os.path.join(self.fastercap_testdata_dir, 'nmos_diode2_FasterCap_Result_Matrix.csv')
        obtained_matrix.write_csv(output_path=output_path, separator=';')
