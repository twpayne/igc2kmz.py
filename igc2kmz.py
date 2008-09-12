#!/usr/bin/python

import fileinput
import optparse
import sys

from bounds import Bounds, BoundsSet
import gradient
import igc
import kmz
from OpenStruct import OpenStruct
import scale
from track import Hints, Stock

def add_track(option, opt_str, value, parser, make_track, **kwargs):
  track = make_track(value)
  hints = Hints()
  for attr in 'color glider_type pilot_name timezone_offset'.split(' '):
    if not getattr(parser.values, attr) is None:
      setattr(hints, attr, getattr(parser.values, attr))
      setattr(parser.values, attr, None)
  if parser.values.tracks_and_hints is None:
    parser.values.tracks_and_hints = []
  parser.values.tracks_and_hints.append((track, hints))

def main(argv):
  parser = optparse.OptionParser(usage='Usage: %prog [options]')
  parser.add_option('-o', '--output', dest='filename', metavar='FILENAME')
  group = optparse.OptionGroup(parser, 'Per-track options')
  group.add_option('-c', '--color', dest='color', metavar='COLOR')
  group.add_option('-i', '--igc', action='callback', callback=add_track, dest='tracks_and_hints', metavar='FILENAME', nargs=1, type='string', callback_args=(lambda value: igc.IGC(value).track(),))
  group.add_option('-g', '--glider-type', dest='glider_type', metavar='STRING')
  group.add_option('-p', '--pilot-name', dest='pilot_name', metavar='STRING')
  group.add_option('-w', '--width', dest='width', metavar='INTEGER', type='int')
  group.add_option('-z', '--timezone-offset', dest='timezone_offset', metavar='INTEGER', type='int')
  parser.add_option_group(group)
  parser.set_defaults(output='igc2kmz.kmz')
  options, args = parser.parse_args(argv)
  if options.tracks_and_hints is None:
    raise RuntimeError # FIXME
  if len(args) != 1:
    raise RuntimeError # FIXME
  bounds = BoundsSet()
  for track, hints in options.tracks_and_hints:
    bounds.merge(track.bounds)
  stock = Stock()
  stock.altitude_scale = scale.Scale(bounds.ele.tuple(), title='altitude', gradient=gradient.default)
  stock.time_scale = scale.TimeScale(bounds.time.tuple())
  result = kmz.kmz()
  result.add_siblings(stock.kmz)
  for track, hints in options.tracks_and_hints:
    hints.stock = stock
    result.add_siblings(track.kmz(hints))
  result.write(options.output)

if __name__ == '__main__':
  main(sys.argv)
