#!/usr/bin/python
#
#   olc2gpx.py  olc2002 output to GPX converter
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
import optparse
import re
import sys
try:
  from xml.etree.cElementTree import ElementTree, TreeBuilder
except ImportError:
  from xml.etree import ElementTree, TreeBuilder


class tag(object):

  def __init__(self, tb, name, attrs={}):
    self.tb = tb
    self.name = name
    self.attrs = attrs

  def __enter__(self):
    self.tb.start(self.name, self.attrs)

  def __exit__(self, type, value, traceback):
    self.tb.end(self.name)


class RtePt(object):

  def __init__(self):
    self.name = None
    self.lat = None
    self.lon = None
    self.dt = None

  def toxml(self, tb):
    with tag(tb, 'rtept', {'lat': str(self.lat), 'lon': str(self.lon)}):
      with tag(tb, 'name'): tb.data(self.name)
      with tag(tb, 'time'): tb.data(self.dt.strftime('%Y-%m-%dT%H:%M:%SZ'))
      with tag(tb, 'fix'): tb.data('2d')
    return tb


class Rte(object):

  def __init__(self):
    self.league = None
    self.name = None
    self.distance = None
    self.multiplier = None
    self.score = None
    self.circuit = None
    self.rtepts = []

  def toxml(self, tb):
    with tag(tb, 'rte'):
      with tag(tb, 'name'): tb.data(self.name)
      with tag(tb, 'extensions'):
        with tag(tb, 'league'): tb.data(self.league)
        with tag(tb, 'distance'): tb.data(str(self.distance))
        with tag(tb, 'multiplier'): tb.data('%.2f' % self.multiplier);
        with tag(tb, 'score'): tb.data(str(self.score))
        if self.circuit:
          with tag(tb, 'circuit'):
            pass
      for rtept in self.rtepts:
        rtept.toxml(tb)
    return tb


DEBUG_DATE_RE = re.compile(r'DEBUG DATE (\d\d)(\d\d)(\d\d)\Z')
OUT_TYPE_RE = re.compile(r'OUT TYPE (\S+)\Z')
OUT_FLIGHT_KM_RE = re.compile(r'OUT FLIGHT_KM (\d+\.\d+)\Z')
OUT_FLIGHT_POINTS_RE = re.compile(r'OUT FLIGHT_POINTS (\d+\.\d+)\Z')
OUT_P_RE = re.compile(r'OUT p\d+ (\d\d):(\d\d):(\d\d) ([NS])\s*(\d+):(\d+\.\d+) ([EW])\s*(\d+):(\d+\.\d+)')

PRETTY_NAME = {
  'FreeFlight0TP': 'open distance',
  'MaxTakeoffDistance': 'open distance from take-off',
  'FREE_FLIGHT': 'open distance via three turnpoints',
  'FREE_TRIANGLE': 'free triangle',
  'FAI_TRIANGLE': 'FAI triangle',
}

CIRCUITS = set(['FREE_TRIANGLE', 'FAI_TRIANGLE'])


class XC(object):

  def __init__(self, file, league):
    self.rtes = []
    date = None
    for line in file:
      line = line.rstrip()
      m = DEBUG_DATE_RE.match(line)
      if m:
        day, mon, year = map(int, m.groups())
        date = datetime.date(year + 2000, mon,day)
        continue
      m = OUT_TYPE_RE.match(line)
      if m:
        rte = Rte()
        rte.league = league
        rte.name = PRETTY_NAME[m.group(1)]
        rte.circuit = m.group(1) in CIRCUITS
        self.rtes.append(rte)
        last_time = None
        continue
      m = OUT_FLIGHT_KM_RE.match(line)
      if m:
        rte.distance = float(m.group(1))
        continue
      m = OUT_FLIGHT_POINTS_RE.match(line)
      if m:
        rte.score = float(m.group(1))
        rte.multiplier = rte.score / rte.distance
        continue
      m = OUT_P_RE.match(line)
      if m:
        rtept = RtePt()
        rtept.name = 'TP%d' % len(rte.rtepts) if rte.rtepts else 'Start'
        rtept.lat = int(m.group(5)) + float(m.group(6)) / 60.0
        if m.group(4) == 'S':
          rtept.lat = -rtept.lat
        rtept.lon = int(m.group(8)) + float(m.group(9)) / 60.0
        if m.group(7) == 'W':
          rtept.lon = -rtept.lon
        time = datetime.time(*map(int, m.group(1, 2, 3)))
        if not last_time is None and time < last_time:
          date += datetime.timedelta(1)
        rtept.dt = datetime.datetime.combine(date, time)
        rte.rtepts.append(rtept)
        last_time = time
        continue
    for rte in self.rtes:
      rte.rtepts[-1].name = 'Finish'

  def toxml(self, tb):
    with tag(tb, 'gpx', {'version': '1.1', 'creator': 'http://github.com/twpayne/igc2kmz/tree/master'}):
      for rte in self.rtes:
        rte.toxml(tb)
    return tb


def main(argv):
  parser = optparse.OptionParser(description='olc2002 to GPX converter')
  parser.add_option('-l', '--league', metavar='STRING')
  parser.add_option('-o', '--output', metavar='FILENAME')
  parser.set_defaults(league='OLC')
  options, args = parser.parse_args(argv)
  xc = XC(fileinput.input(args[1:]), options.league)
  e = xc.toxml(TreeBuilder()).close()
  output = open(options.output, 'w') if options.output else sys.stdout
  output.write('<?xml version="1.0" encoding="UTF-8"?>')
  ElementTree(e).write(output)


if __name__ == '__main__':
  main(sys.argv)
