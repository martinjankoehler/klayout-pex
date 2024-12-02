from __future__ import annotations

import copy
from dataclasses import dataclass
import os
import tempfile
from typing import *
import unittest


@dataclass
class CapacitanceMatrix:
    conductor_names: List[str]  # NOTE FasterCap generates [g_1, g_2, ...]
    rows: List[List[float]]     # NOTE: in µm

    def __getitem__(self, key):
        return self.rows.__getitem__(key)

    def __setitem__(self, key, value):
        self.rows.__setitem__(key, value)

    @property
    def dimension(self):
        return len(self.conductor_names)

    @classmethod
    def parse_csv(cls, path: str, separator: str = ';'):
        with open(path, 'r') as f:
            lines = f.readlines()
            if len(lines) < 2:
                raise Exception(f"Capacitance Matrix CSV must at least have 2 lines: "
                                f"{path}")
            conductor_names = [cell.strip() for cell in lines[0].split(sep=separator)]
            rows = []
            for line in lines[1:]:
                row = [float(cell.strip()) for cell in line.split(sep=separator)]
                rows.append(row)
            return CapacitanceMatrix(conductor_names=conductor_names,
                                     rows=rows)

    def write_csv(self, output_path: str, separator: str = ';'):
        with open(output_path, 'w') as f:
            header_line = separator.join(self.conductor_names)
            f.write(header_line)
            f.write('\n')

            for row in self.rows:
                cells = ['%.12g' % cell for cell in row]
                row_line = separator.join(cells)
                f.write(row_line)
                f.write('\n')

    def averaged_off_diagonals(self) -> CapacitanceMatrix:
        c = copy.deepcopy(self)
        for i in range(len(self.rows)):
            for j in range(len(self.conductor_names)):
                if j <= i:
                    continue
                v1 = self[i][j]
                v2 = self[j][i]
                avg = (v1 + v2) / 2
                # print(f"i={i} j={j}, avg({v1}, {v2}) == {avg}")
                c[i][j] = avg
                c[j][i] = avg
        return c


class Test(unittest.TestCase):
    @property
    def klayout_testdata_dir(self) -> str:
        return os.path.realpath(os.path.join(__file__, '..', '..', '..',
                                             'testdata', 'fastercap'))

    def test_dump_cap_matrix_info(self):
        info = CapacitanceMatrixInfo([
            ConductorInfo(fastcap_index=7, net='0', outside_dielectric=None),
            ConductorInfo(fastcap_index=8, net='VDD', outside_dielectric=None),
            ConductorInfo(fastcap_index=9, net='VSS', outside_dielectric=None),
            ConductorInfo(fastcap_index=10, net='VDD', outside_dielectric='spnit'),
        ])
        out_path = tempfile.mktemp(prefix='fastercap_matrix_info', suffix='.yaml')
        info.write_yaml(out_path)

        info2 = CapacitanceMatrixInfo.from_yaml(out_path)
        self.assertEqual(info, info2)

    def test_parse_csv(self):
        csv_path = os.path.join(self.klayout_testdata_dir, 'nmos_diode2_FasterCap_Result_Matrix.csv')
        parsed_matrix = CapacitanceMatrix.parse_csv(path=csv_path, separator=';')
        self.assertEqual(10, len(parsed_matrix.rows))
        self.assertEqual(10, len(parsed_matrix.rows[0]))
        self.assertEqual(10, len(parsed_matrix.rows[1]))
        self.assertEqual(10, len(parsed_matrix.rows[2]))
        self.assertEqual(10, len(parsed_matrix.rows[3]))
        self.assertEqual(10, len(parsed_matrix.rows[4]))
        self.assertEqual(10, len(parsed_matrix.rows[5]))
        self.assertEqual(10, len(parsed_matrix.rows[6]))
        self.assertEqual(10, len(parsed_matrix.rows[7]))
        self.assertEqual(10, len(parsed_matrix.rows[8]))
        self.assertEqual(10, len(parsed_matrix.rows[9]))
        self.assertEqual(
            ['g1_7', 'g1_8', 'g1_9', 'g1_10', 'g1_11', 'g1_12', 'g1_13', 'g1_14', 'g1_15', 'g1_16'],
            parsed_matrix.conductor_names
        )

    def test_write_csv(self):
        csv_path = os.path.join(self.klayout_testdata_dir, 'nmos_diode2_FasterCap_Result_Matrix.csv')
        parsed_matrix = CapacitanceMatrix.parse_csv(path=csv_path, separator=';')
        out_path = tempfile.mktemp(prefix='fastercap_matrix_raw__', suffix='.csv')
        parsed_matrix.write_csv(output_path=out_path, separator=';')
        parsed_matrix2 = CapacitanceMatrix.parse_csv(path=out_path, separator=';')
        self.assertEqual(parsed_matrix, parsed_matrix2)

    def test_averaged_off_diagonals(self):
        csv_path = os.path.join(self.klayout_testdata_dir, 'nmos_diode2_FasterCap_Result_Matrix.csv')
        parsed_matrix = CapacitanceMatrix.parse_csv(path=csv_path, separator=';')
        avg_matrix = parsed_matrix.averaged_off_diagonals()
        out_path = tempfile.mktemp(prefix='fastercap_matrix_avg__', suffix='.csv')
        avg_matrix.write_csv(output_path=out_path, separator=';')
        print(f"averaged matrix stored in {out_path}")