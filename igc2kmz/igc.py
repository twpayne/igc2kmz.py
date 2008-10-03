#   igc2kmz/igc.py  igc2kmz IGC functions
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


import datetime
import logging
import os.path
import re

import coord
import track


A_RECORD_RE = re.compile(r'A(.*)\Z')
B_RECORD_RE = re.compile(r'B(\d{2})(\d{2})(\d{2})(\d{2})(\d{5})([NS])(\d{3})(\d{5})([EW])([AV])(\d{5})(\d{5})\d*\Z')
C_RECORD_RE = re.compile(r'C(\d{2})(\d{5})([NS])(\d{3})(\d{5})([EW])(.*)\Z')
G_RECORD_RE = re.compile(r'G(.*)\Z')
HFDTE_RECORD_RE = re.compile(r'H(F)(DTE)(\d\d)(\d\d)(\d\d)\Z')
HFFXA_RECORD_RE = re.compile(r'H(F)(FXA)(\d+)\Z')
H_RECORD_RE = re.compile(r'H([FOP])([A-Z]{3}).*?:(.*)\Z')
I_RECORD_RE = re.compile(r'(\d{2})(\d{2})(\w{3})\Z')
L_RECORD_RE = re.compile(r'L(.*)\Z')

NOT_SET_RE = re.compile(r'\s*(not\s+set|n/?a)?\s*\Z', re.I)


class_by_letter = {}


class Error(RuntimeError):
  pass


class SyntaxError(Error):
  pass


class Metaclass(type):

  def __new__(cls, name, bases, dct):
    result = type.__new__(cls, name, bases, dct)
    if name != 'Record':
      class_by_letter[name[0]] = result
    return result


class Record(object):

  __metaclass__ = Metaclass


class ARecord(Record):

  def __init__(self, line, igc):
    m = A_RECORD_RE.match(line)
    if not m:
      raise SyntaxError, line
    self.value = m.group(1)
    igc.a = self.value


class BRecord(Record):

  __slots__ = ('dt', 'lat', 'lon', 'validity', 'alt', 'ele')

  def __init__(self, line, igc):
    m = B_RECORD_RE.match(line)
    if not m:
      raise SyntaxError, line
    for key, value in igc.i.items():
      setattr(self, key, int(line[value]))
    time = datetime.time(*map(int, m.group(1, 2, 3)))
    self.dt = datetime.datetime.combine(igc.hfdterecord.date, time)
    self.lat = int(m.group(4)) + int(m.group(5)) / 60000.0
    if 'lad' in igc.i:
      self.lat += int(line[igc.i['lad']]) / 6000000.0
    if m.group(6) == 'S':
      self.lat *= -1
    self.lon = int(m.group(7)) + int(m.group(8)) / 60000.0
    if 'lod' in igc.i:
      self.lon += int(line[igc.i['lod']]) / 6000000.0
    if m.group(9) == 'W':
      self.lat *= -1
    self.validity = m.group(10)
    self.alt = int(m.group(11))
    self.ele = int(m.group(12))
    if igc.b and igc.b[-1].dt > self.dt:
      raise Error, '%s: decreasing time stamps %s to %s' % (igc.filename, igc.b[-1].dt, self.dt)
    igc.b.append(self)


class CRecord(Record):

  def __init__(self, line, igc):
    m = C_RECORD_RE.match(line)
    if not m:
      raise SyntaxError, line
    self.lat = int(m.group(1)) + int(m.group(2)) / 60000.0
    if m.group(3) == 'S':
      self.lat *= -1
    self.lon = int(m.group(4)) + int(m.group(5)) / 60000.0
    if m.group(6) == 'W':
      self.lon *= -1
    self.name = m.group(7)
    igc.c.append(self)


class GRecord(Record):

  def __init__(self, line, igc):
    m = G_RECORD_RE.match(line)
    if not m:
      raise SyntaxError, line
    self.value = m.group(1)
    igc.g.append(self.value)


class HRecord(Record):

  def __init__(self, line, igc):
    def hfdte():
      self.source, self.type = m.group(1, 2)
      day, month, year = map(int, m.group(3, 4, 5))
      try:
        self.date = datetime.date(2000 + year, month, day)
      except ValueError:
        raise SyntaxError, line
      igc.hfdterecord = self
    def hffxa():
      self.source, self.type = m.group(1, 2)
      self.value = int(m.group(3))
      igc.h['fxa'] = self.value
    def h():
      self.source, self.key, self.value = m.groups()
      igc.h[self.key.lower()] = self.value
    for re, f in ((HFDTE_RECORD_RE, hfdte), (HFFXA_RECORD_RE, hffxa), (H_RECORD_RE, h)):
      m = re.match(line)
      if m:
        f()
        break
    else:
      raise SyntaxError, line


class IRecord(Record):

  def __init__(self, line, igc):
    for i in xrange(0, int(line[1:3])):
      m = I_RECORD_RE.match(line, 3 + 7 * i, 10 + 7 * i)
      if not m:
        raise SyntaxError, line
      igc.i[m.group(3).lower()] = slice(int(m.group(1)), int(m.group(2)) + 1)


class LRecord(Record):

  def __init__(self, line, igc):
    m = L_RECORD_RE.match(line)
    if not m:
      raise SyntaxError, line
    igc.l.append(m.group(1))


class IGC(object):

  def __init__(self, file):
    try:
      self.filename = file.name
    except AttributeError:
      self.filename = '(unknown)'
    self.b = []
    self.c = []
    self.g = []
    self.h = {}
    self.i = {}
    self.l = []
    self.records = []
    for line in file:
      try:
        line = line.rstrip()
        if line[0] in class_by_letter:
          self.records.append(class_by_letter[line[0]](line, self))
        else:
          logging.warning('%s: unknown record %s' % (self.filename, repr(line)))
      except SyntaxError:
        logging.warning('%s: invalid record %s' % (self.filename, repr(line)))

  def track(self):
    ele = 'ele' if any(b.ele for b in self.b) else 'alt'
    coords = [coord.Coord.deg(b.lat, b.lon, getattr(b, ele), b.dt) for b in self.b]
    kwargs = {}
    kwargs['filename'] = os.path.basename(self.filename)
    if 'plt' in self.h and not NOT_SET_RE.match(self.h['plt']):
      kwargs['pilot_name'] = self.h['plt'].strip()
    if 'gty' in self.h and not NOT_SET_RE.match(self.h['gty']):
      kwargs['glider_type'] = self.h['gty'].strip()
    if 'gid' in self.h and not NOT_SET_RE.match(self.h['gid']):
      kwargs['glider_id'] = self.h['gid'].strip()
    for k in self.i.keys():
      if any(getattr(b, k) for b in self.b):
        kwargs[k] = [getattr(b, k) for b in self.b]
    return track.Track(coords, **kwargs)
