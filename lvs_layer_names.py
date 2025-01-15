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

import argparse
import io
import re
import shlex
import sys
from typing import *

from kpex.log import (
    LogLevel,
    set_log_level,
    # debug,
    info,
    # warning,
    error, warning
)

from kpex.version import __version__
from kpex.util.argparse_helpers import render_enum_help

# ------------------------------------------------------------------------------------

PROGRAM_NAME = "lvs_layer_names"


def parse_args(arg_list: List[str] = None) -> argparse.Namespace:
    main_parser = argparse.ArgumentParser(description=f"{PROGRAM_NAME}: "
                                                      f"Create name declarations from KLayout-based LVS log",
                                          add_help=False)
    group_special = main_parser.add_argument_group("Special options")
    group_special.add_argument('--help', '-h', action='help', help='show this help message and exit')
    group_special.add_argument("--version", "-v", action='version', version=f'{PROGRAM_NAME} {__version__}')
    group_special.add_argument("--log_level", dest='log_level', default='INFO',
                               help=render_enum_help(topic='log_level', enum_cls=LogLevel))

    main_parser.add_argument('--out', '-o', dest='output_script',
                             type=argparse.FileType('w'), default=sys.stdout,
                             help='Output LVS Ruby Script')

    main_parser.add_argument(dest='lvs_log_file_path',
                             type=argparse.FileType('r'),
                             help='LVS log file to parse')

    if arg_list is None:
        arg_list = sys.argv[1:]
    args = main_parser.parse_args(arg_list)
    return args


def validate_args(args: argparse.Namespace):
    found_errors = False

    # ...

    if found_errors:
        raise Exception("Argument validation failed")


def setup_logging(args: argparse.Namespace):
    try:
        validate_args(args)
    except Exception:
        sys.exit(1)

    set_log_level(args.log_level)


def main():
    info("Called with arguments:")
    info(' '.join(map(shlex.quote, sys.argv)))

    args = parse_args()

    setup_logging(args)

    layer_names: Set[str] = set()

    # info(f"Reading layout from {args.lvs_log_file_path}")
    lvs_log_file_path: io.TextIOWrapper = args.lvs_log_file_path
    for line in lvs_log_file_path.readlines():
        m = re.match(r'^.+ : ([a-zA-Z0-9_]+) has \d+ polygons$', line)
        if m:
            n = m.group(1)
            layer_names.add(n)

    out: io.TextIOWrapper = args.output_script
    out.write(f"# Script generated by {PROGRAM_NAME} version {__version__}\n")
    out.write('\n')
    out.write('# ================================================================\n')
    out.write('# ---------------------- SAVE LAYER NAMES ------------------------\n')
    out.write('# ================================================================\n')
    out.write('if self.respond_to?(:name)\n')
    out.write('  %w(\n')

    cnt = 0
    for ln in sorted(layer_names):
        cnt += 1
        if cnt == 1:
            out.write("    ")  # indent
        out.write(f"{ln} ")
        if cnt == 10:
            cnt = 0
            out.write('\n')
    if cnt != 0:
        out.write('\n')
    out.write('  ).each do |l|\n')
    out.write('    name(eval(l), l)\n')
    out.write('  end\n')
    out.write('end\n')


if __name__ == "__main__":
    main()