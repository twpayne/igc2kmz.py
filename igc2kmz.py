#!/usr/bin/python
#
#   igc2kmz.py  IGC to Google Earth converter
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
import sys

import igc2kmz
import igc2kmz.igc
import igc2kmz.photo


def add_flight(option, opt, value, parser):
  parser.values.flights.append(igc2kmz.Flight(igc2kmz.igc.IGC(open(value)).track()))


def add_flight_option(option, opt, value, parser):
  setattr(parser.values.flights[-1], option.dest, value)


def add_flight_photo(option, opt, value, parser):
  parser.values.flights[-1].photos.append(igc2kmz.photo.Photo(value))


def main(argv):
  parser = optparse.OptionParser(usage='Usage: %prog [options]', description="IGC to Google Earth converter")
  parser.add_option('-o', '--output', metavar='FILENAME')
  parser.add_option('-z', '--timezone-offset', metavar='HOURS', type='int')
  group = optparse.OptionGroup(parser, 'Per-flight options')
  group.add_option('-i', '--igc', metavar='FILENAME', type='string', action='callback', callback=add_flight)
  group.add_option('-n', '--pilot-name', metavar='STRING', type='string', action='callback', callback=add_flight_option)
  group.add_option('-g', '--glider-type', metavar='STRING', type='string', action='callback', callback=add_flight_option)
  group.add_option('-c', '--color', metavar='COLOR', type='string', action='callback', callback=add_flight_option)
  group.add_option('-w', '--width', metavar='INTEGER', type='string', action='callback', callback=add_flight_option)
  group.add_option('-p', '--photo', metavar='FILENAME', type='string', action='callback', callback=add_flight_photo)
  parser.add_option_group(group)
  parser.set_defaults(output='igc2kmz.kmz')
  parser.set_defaults(timezone_offset=0)
  parser.set_defaults(flights=[])
  options, args = parser.parse_args(argv)
  if len(options.flights) == 0:
    raise RuntimeError # FIXME
  if len(args) != 1:
    raise RuntimeError # FIXME
  igc2kmz.flights2kmz(options.flights, timezone_offset=options.timezone_offset).write(options.output)

if __name__ == '__main__':
  main(sys.argv)
