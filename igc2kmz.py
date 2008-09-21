#!/usr/bin/python

import optparse
import sys

from pprint import pprint as pp

import igc2kmz
import igc2kmz.igc

def add_flight(option, opt, value, parser):
  parser.values.flights.append(igc2kmz.Flight(igc2kmz.igc.IGC(open(value)).track()))

def add_flight_option(option, opt, value, parser):
  setattr(parser.values.flights[-1], option.dest, value)

def main(argv):
  parser = optparse.OptionParser(usage='Usage: %prog [options]')
  parser.add_option('-o', '--output', metavar='FILENAME')
  parser.add_option('-z', '--timezone-offset', metavar='INTEGER', type='int')
  group = optparse.OptionGroup(parser, 'Per-flight options')
  group.add_option('-i', '--igc', metavar='FILENAME', type='string', action='callback', callback=add_flight)
  group.add_option('-p', '--pilot-name', metavar='STRING', type='string', action='callback', callback=add_flight_option)
  group.add_option('-g', '--glider-type', metavar='STRING', type='string', action='callback', callback=add_flight_option)
  group.add_option('-c', '--color', metavar='COLOR', type='string', action='callback', callback=add_flight_option)
  group.add_option('-w', '--width', metavar='INTEGER', type='string', action='callback', callback=add_flight_option)
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
