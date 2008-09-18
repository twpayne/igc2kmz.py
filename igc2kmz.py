#!/usr/bin/python

import optparse
import sys

import igc2kmz
import igc2kmz.igc
import igc2kmz.kmz

def add_track(option, opt_str, value, parser, make_track, **kwargs):
  track = make_track(value)
  hints = igc2kmz.Hints()
  for attr in 'color glider_type pilot_name'.split(' '):
    if not getattr(parser.values, attr) is None:
      setattr(hints, attr, getattr(parser.values, attr))
      setattr(parser.values, attr, None)
  if parser.values.tracks_and_hints is None:
    parser.values.tracks_and_hints = []
  parser.values.tracks_and_hints.append((track, hints))


def main(argv):
  parser = optparse.OptionParser(usage='Usage: %prog [options]')
  parser.add_option('-o', '--output', metavar='FILENAME')
  parser.add_option('-z', '--timezone-offset', metavar='INTEGER', type='int')
  group = optparse.OptionGroup(parser, 'Per-track options')
  group.add_option('-c', '--color', dest='color', metavar='COLOR')
  group.add_option('-i', '--igc', action='callback', callback=add_track, dest='tracks_and_hints', metavar='FILENAME', nargs=1, type='string', callback_args=(lambda value: igc2kmz.igc.IGC(value).track(),))
  group.add_option('-g', '--glider-type', dest='glider_type', metavar='STRING')
  group.add_option('-p', '--pilot-name', dest='pilot_name', metavar='STRING')
  group.add_option('-w', '--width', dest='width', metavar='INTEGER', type='int')
  parser.add_option_group(group)
  parser.set_defaults(output='igc2kmz.kmz')
  parser.set_defaults(timezone_offset=0)
  options, args = parser.parse_args(argv)
  if options.tracks_and_hints is None:
    raise RuntimeError # FIXME
  if len(args) != 1:
    raise RuntimeError # FIXME
  globals = igc2kmz.Globals(options, [track for track, hints in options.tracks_and_hints])
  result = igc2kmz.kmz.kmz()
  result.add_siblings(globals.stock.kmz)
  for track, hints in options.tracks_and_hints:
    hints.globals = globals
    result.add_siblings(igc2kmz.track2kmz(track, hints))
  result.write(options.output)

if __name__ == '__main__':
  main(sys.argv)
