#! /bin/bash
##
## --------------------------------------------------------------------------------
## SPDX-FileCopyrightText: 2024-2025 Martin Jan Köhler and Harald Pretl
## Johannes Kepler University, Institute for Integrated Circuits.
##
## This file is part of KPEX 
## (see https://github.com/martinjankoehler/klayout-pex).
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program. If not, see <http://www.gnu.org/licenses/>.
## SPDX-License-Identifier: GPL-3.0-or-later
## --------------------------------------------------------------------------------
##

DIR=$(dirname -- $(realpath ${BASH_SOURCE}))

mkdir -p $DIR/build

RESULTS_PATH=$DIR/build/pylint-results.json
REPORT_PATH=$DIR/build/pylint-report.html
pylint --rcfile $DIR/.pylintrc \
       --output-format json2 \
       --ignore build \
	$DIR/kpex > $RESULTS_PATH

pylint-json2html -f jsonextended $RESULTS_PATH -o $REPORT_PATH

open -a Safari $REPORT_PATH
