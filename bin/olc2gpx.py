#!/usr/bin/env python
#
#   olc2002 output to GPX converter
#   Copyright (C) 2008  Tom Payne
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.


from __future__ import with_statement

import datetime
import fileinput
import logging
from optparse import OptionParser
import os
import re
import sys
try:
    from xml.etree.cElementTree import ElementTree, TreeBuilder
except ImportError:
    from xml.etree.ElementTree import ElementTree, TreeBuilder

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from igc2kmz.coord import Coord
from igc2kmz.etree import tag
from igc2kmz.gpx import gpx_tag
from igc2kmz.xc import Route, Turnpoint, XC


DEBUG_DATE_RE = re.compile(r'DEBUG DATE (\d\d)(\d\d)(\d\d)\Z')
OUT_TYPE_RE = re.compile(r'OUT TYPE (\S+)\Z')
OUT_FLIGHT_KM_RE = re.compile(r'OUT FLIGHT_KM (\d+\.\d+)\Z')
OUT_FLIGHT_POINTS_RE = re.compile(r'OUT FLIGHT_POINTS (\d+\.\d+)\Z')
OUT_P_RE = re.compile(r'OUT p\d+ (\d\d):(\d\d):(\d\d)'
                      r' ([NS])\s*(\d+):(\d+\.\d+) ([EW])\s*(\d+):(\d+\.\d+)')

PRETTY_NAME = {
    'FreeFlight0TP': 'open distance',
    'MaxTakeoffDistance': 'open distance from take-off',
    'FREE_FLIGHT': 'open distance via three turnpoints',
    'FREE_TRIANGLE': 'free triangle',
    'FAI_TRIANGLE': 'FAI triangle',
}

CIRCUITS = set(['FREE_TRIANGLE', 'FAI_TRIANGLE'])


def main(argv):
    parser = OptionParser(description='olc2002 to GPX converter')
    parser.add_option('-l', '--league', metavar='STRING')
    parser.add_option('-o', '--output', metavar='FILENAME')
    parser.add_option('--debug', action='store_true')
    parser.set_defaults(debug=False)
    parser.set_defaults(league='OLC')
    options, args = parser.parse_args(argv)
    #
    routes = []
    date = None
    for line in fileinput.input(args[1:]):
        line = line.rstrip()
        m = DEBUG_DATE_RE.match(line)
        if m:
            day, mon, year = map(int, m.groups())
            date = datetime.date(year + 2000, mon,day)
            continue
        m = OUT_TYPE_RE.match(line)
        if m:
            name = PRETTY_NAME[m.group(1)]
            circuit = m.group(1) in CIRCUITS
            route = Route(name, options.league, None, None, None, circuit, [])
            routes.append(route)
            last_time = None
            continue
        m = OUT_FLIGHT_KM_RE.match(line)
        if m:
            route.distance = float(m.group(1))
            continue
        m = OUT_FLIGHT_POINTS_RE.match(line)
        if m:
            route.score = float(m.group(1))
            route.multiplier = route.score / route.distance
            continue
        m = OUT_P_RE.match(line)
        if m:
            name = 'TP%d' % len(route.tps) if route.tps else 'Start'
            lat = int(m.group(5)) + float(m.group(6)) / 60.0
            if m.group(4) == 'S':
                lat = -lat
            lon = int(m.group(8)) + float(m.group(9)) / 60.0
            if m.group(7) == 'W':
                lon = -lon
            time = datetime.time(*map(int, m.group(1, 2, 3)))
            if not last_time is None and time < last_time:
                date += datetime.timedelta(1)
            dt = datetime.datetime.combine(date, time)
            coord = Coord(lat, lon, 0, dt)
            tp = Turnpoint(name, coord)
            route.tps.append(tp)
            last_time = time
            continue
        if options.debug:
            logging.warning(line)
    for route in routes:
        route.tps[-1].name = 'Finish'
    xc = XC(routes)
    with gpx_tag(TreeBuilder()) as tb:
        element = xc.build_tree(tb).close()
    output = open(options.output, 'w') if options.output else sys.stdout
    output.write('<?xml version="1.0" encoding="UTF-8"?>')
    ElementTree(element).write(output)


if __name__ == '__main__':
    main(sys.argv)
