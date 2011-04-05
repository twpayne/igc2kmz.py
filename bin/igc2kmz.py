#!/usr/bin/env python
#
#   IGC to Google Earth converter
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


import optparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from igc2kmz import Flight, flights2kmz
from igc2kmz.gpx import GPX
from igc2kmz.igc import IGC
from igc2kmz.kml import Verbatim
from igc2kmz.photo import Photo
from igc2kmz.task import Task
from igc2kmz.xc import XC


def add_flight(option, opt, value, parser):
    """Add a flight."""
    ext = os.path.splitext(value)[1].lower()
    if ext == '.igc':
        track = IGC(open(value)).track()
    elif ext == '.gpx':
        track = GPX(open(value)).track()
    else:
        raise RuntimeError, 'unsupported file type %s' % repr(ext)
    parser.values.flights.append(Flight(track))


def set_flight_option(option, opt, value, parser):
    """Set an option on the last flight."""
    flight = parser.values.flights[-1]
    setattr(flight, option.dest, value)


def add_photo(option, opt, value, parser):
    """Add a photo to the last flight."""
    flight = parser.values.flights[-1]
    photo = Photo(value)
    flight.photos.append(photo)


def set_photo_option(option, opt, value, parser):
    """Set an option on the last photo on the last flight."""
    flight = parser.values.flights[-1]
    photo = flight.photos[-1]
    setattr(photo, option.dest, value)


def set_flight_xc(option, opt, value, parser):
    """Set the XC of the last flight."""
    flight = parser.values.flights[-1]
    xc = XC.from_file(open(value))
    flight.xc = xc


def main(argv):
    parser = optparse.OptionParser(
            usage='Usage: %prog [options]',
            description="IGC to Google Earth converter")
    parser.add_option('-o', '--output', metavar='FILENAME',
            help='set output filename')
    parser.add_option('-z', '--tz-offset', metavar='HOURS', type='int',
            help='set timezone offset')
    parser.add_option('-r', '--root', metavar='FILENAME',
            action='append', dest='roots',
            help='add root element')
    parser.add_option('-t', '--task', metavar='FILENAME',
            help='set task')
    group = optparse.OptionGroup(parser, 'Per-flight options')
    group.add_option('-i', '--igc', metavar='FILENAME', type='string',
            action='callback', callback=add_flight,
            help='set flight IGC file')
    group.add_option('-n', '--pilot-name', metavar='STRING', type='string',
            action='callback', callback=set_flight_option,
            help='set pilot name')
    group.add_option('-g', '--glider-type', metavar='STRING', type='string',
            action='callback', callback=set_flight_option,
            help='set glider type')
    group.add_option('-c', '--color', metavar='COLOR', type='string',
            action='callback', callback=set_flight_option,
            help='set track line color')
    group.add_option('-w', '--width', metavar='INTEGER', type='int',
            action='callback', callback=set_flight_option,
            help='set track line width')
    group.add_option('-u', '--url', metavar='URL', type='string',
            action='callback', callback=set_flight_option,
            help='set flight URL')
    group.add_option('-x', '--xc', metavar='FILENAME', type='string',
            action='callback', callback=set_flight_xc,
            help='set flight XC')
    parser.add_option_group(group)
    group = optparse.OptionGroup(parser, 'Per-photo options')
    group.add_option('-p', '--photo', metavar='URL', type='string',
            action='callback', callback=add_photo,
            help='add photo')
    group.add_option('-d', '--description', metavar='STRING', type='string',
            action='callback', callback=set_photo_option,
            help='set photo comment')
    parser.add_option_group(group)
    #
    parser.set_defaults(flights=[])
    parser.set_defaults(output='igc2kmz.kmz')
    parser.set_defaults(roots=[])
    parser.set_defaults(tz_offset=0)
    #
    options, args = parser.parse_args(argv)
    if len(options.flights) == 0:
        parser.error('no flights specified')
    if len(args) != 1:
        parser.error('extra arguments on command line: %s' % repr(args[1:]))
    #
    roots = [Verbatim(open(root).read()) for root in options.roots]
    task = Task.from_file(open(options.task)) if options.task else None
    kmz = flights2kmz(options.flights,
                      roots=roots,
                      tz_offset=options.tz_offset,
                      task=task)
    kmz.write(options.output, '2.2')


if __name__ == '__main__':
    main(sys.argv)
