#!/usr/bin/env python
#
#   IGC to task converter
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

from datetime import timedelta
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
from igc2kmz.etree import pretty_write, tag
from igc2kmz.gpx import gpx_tag
from igc2kmz.igc import IGC
from igc2kmz.task import Task, Turnpoint


def find_nth(function, iterable, n=0):
    for element in iterable:
        if function(element):
            if n <= 0:
                return element
            else:
                n -= 1
    return None


def main(argv):
    parser = OptionParser(
            usage='Usage: %prog [options] filename.igc',
            description='IGC to task converter')
    parser.add_option('-o', '--output', metavar='FILENAME',
                      help='set output filename')
    parser.add_option('-n', '--name', metavar='NAME',
                      help='set task name')
    parser.add_option('-z', '--tz-offset', metavar='HOURS', type='int',
                      help='set timezone offset')
    parser.add_option('--start', metavar='NAME',
                      help='set start turnpoint')
    parser.add_option('--start-count', metavar='NUMBER', type='int',
                      help='set start count')
    parser.add_option('--start-radius', metavar='RADIUS', type='int',
                      help='set start radius in meters')
    parser.add_option('--start-time', metavar='TIME',
                      help='set start time')
    parser.add_option('--ess', metavar='NAME',
                      help='set end of speed section turnpoint')
    parser.add_option('--ess-count', metavar='NUMBER', type='int',
                      help='set end of speed section count')
    parser.add_option('--ess-radius', metavar='RADIUS', type='int',
                      help='set end of speed section radius in meters')
    parser.add_option('--goal', metavar='NAME',
                      help='set goal turnpoint')
    parser.add_option('--goal-count', metavar='NUMBER', type='int',
                      help='set goal count')
    parser.add_option('--goal-radius', metavar='RADIUS', type='int',
                      help='set start radius in meters')
    parser.set_defaults(tz_offset=0)
    parser.set_defaults(start_count=0)
    parser.set_defaults(ess_count=0)
    parser.set_defaults(goal_count=0)
    #
    options, args = parser.parse_args(argv)
    if len(args) < 2:
        parser.error('no IGC file specified')
    if len(args) > 2:
        parser.error('excess arguments on command line: %s' % repr(args[2:]))
    #
    igc = IGC(open(args[1]))
    if not igc.c:
        parser.error('%s does not contain a task' % repr(argv[1]))
    tps = []
    for c in igc.c:
        if c.name == 'TAKEOFF' or c.name == 'LANDING':
            continue
        m = re.match(r'([A-Z][0-9]{2})([0-9]{3})', c.name)
        if m:
            name = m.group(1)
            ele = 10 * int(m.group(2))
        else:
            name = c.name
            ele = 0
        coord = Coord(c.lat, c.lon, ele)
        tp = Turnpoint(name, coord)
        tps.append(tp)
    task = Task(options.name, tps)
    #
    if options.start:
        start = find_nth(lambda tp: tp.name == options.start, task.tps,
                         options.start_count)
        if not start:
            parser.error('start turnpoint %s not found' % repr(options.start))
    else:
        start = task.tps[1]
    if options.start_radius:
        start.radius = int(options.start_radius)
    if options.start_time:
        m = re.match(r'(\d+):(\d\d)\Z', options.start_time)
        if not m:
            parser.error('invalid start time %s' % repr(options.start_time))
        hour, minute = map(int, m.group(1, 2))
        start.coord.dt = igc.b[0].dt.replace(hour=hour,
                                             minute=minute,
                                             second=0) \
                         - timedelta(seconds=3600 * options.tz_offset)
    #
    if options.ess:
        ess = find_nth(lambda tp: tp.name == options.ess, task.tps,
                       options.ess_count)
        if not ess:
            parser.error('end of speed section turnpoint %s not found'
                         % repr(options.ess))
    else:
        ess = task.tps[-2]
    if options.ess_radius:
        ess.radius = int(options.ess_radius)
    #
    if options.goal:
        goal = find_nth(lambda tp: tp.name == options.goal, task.tps,
                        options.goal_count)
        if not goal:
            parser.error('goal turnpoint %s not found' % repr(options.goal))
    else:
        goal = task.tps[-1]
    if options.goal_radius:
        goal.radius = int(options.goal_radius)
    #
    with gpx_tag(TreeBuilder()) as tb:
        element = task.build_tree(tb).close()
    output = open(options.output, 'w') if options.output else sys.stdout
    output.write('<?xml version="1.0" encoding="utf-8"?>\n')
    pretty_write(output, element)


if __name__ == '__main__':
    main(sys.argv)
