from __future__ import with_statement

import datetime
import re

import coord
import track
from TimeSeries import TimeSeries
from OpenStruct import OpenStruct


A_RECORD_RE = re.compile(r'A(.*)\r\n\Z')
B_RECORD_RE = re.compile(r'B(\d{2})(\d{2})(\d{2})(\d{2})(\d{5})([NS])(\d{3})(\d{5})([EW])([AV])(\d{5})(\d{5}).*\r\n\Z')
C_RECORD_RE = re.compile(r'C(\d{2})(\d{5})([NS])(\d{3})(\d{5})([EW])(.*)\r\n\Z')
G_RECORD_RE = re.compile(r'G(.*)\r\n\Z')
HFDTE_RECORD_RE = re.compile(r'H(F)(DTE)(\d\d)(\d\d)(\d\d)\r\n\Z')
HFFXA_RECORD_RE = re.compile(r'H(F)(FXA)(\d+)\r\n\Z')
H_RECORD_RE = re.compile(r'H([FOP])([A-Z]{3})[A-Z]*:(.*)\r\n\Z')
I_RECORD_RE = re.compile(r'(\d{2})(\d{2})(\w{3})\Z')
NOT_SET_RE = re.compile(r'\s*(not\s+set)?\s*\Z')


class Error(RuntimeError):
  pass


class SyntaxError(Error):
  pass


class ARecord(object):
  "Represents an A record."

  def __init__(self, line, igc):
    m = A_RECORD_RE.match(line)
    if not m:
      raise SyntaxError, line
    self.value = m.group(1)
    igc.a = self.value


class CRecord(object):
  "Represents a C record."

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


class BRecord(object):
  "Represents a B record."

  __slots__ = ('dt', 'lat', 'lon', 'validity', 'alt', 'ele', '__dict__')

  def __init__(self, line, igc):
    m = B_RECORD_RE.match(line)
    if not m:
      raise SyntaxError, line
    time = datetime.time(*map(int, m.group(1, 2, 3)))
    self.dt = datetime.datetime.combine(igc.hfdterecord.date, time)
    self.lat = int(m.group(4)) + int(m.group(5)) / 60000.0
    if m.group(6) == 'S':
      self.lat *= -1
    self.lon = int(m.group(7)) + int(m.group(8)) / 60000.0
    if m.group(9) == 'W':
      self.lat *= -1
    self.validity = m.group(10)
    self.alt = int(m.group(11))
    self.ele = int(m.group(12))
    if igc.i:
      for key, value in igc.i.fields.items():
        setattr(self, key, int(line[value[0]:value[1]]))


class GRecord(object):
  "Represents a G record."

  def __init__(self, line, igc):
    m = G_RECORD_RE.match(line)
    if not m:
      raise SyntaxError, m
    self.value = m.group(1)
    igc.g.append(self.value)


class HRecord(object):
  "Represents an H record."

  def __init__(self, line, igc):
    for re, f in (
        (HFDTE_RECORD_RE, 'hfdte'),
        (HFFXA_RECORD_RE, 'hffxa'),
        (H_RECORD_RE, 'h'),
        ):
      m = re.match(line)
      if m:
        getattr(self, f)(m, igc)
        break

  def h(self, m, igc):
    self.source, self.key, self.value = m.groups()
    igc.h[self.key.lower()] = self.value

  def hfdte(self, m, igc):
    self.source, self.type = m.group(1, 2)
    day, month, year = map(int, m.group(3, 4, 5))
    self.date = datetime.date(2000 + year, month, day)
    igc.hfdterecord = self

  def hffxa(self, m, igc):
    self.source, self.type = m.group(1, 2)
    self.value = int(m.group(3))
    igc.h['fxa'] = self.value


class IRecord(object):
  "Represents an I record."

  def __init__(self, line, igc):
    self.fields = {}
    for i in range(0, int(line[1:3])):
      m = I_RECORD_RE.match(line, 3 + 7 * i, 10 + 7 * i)
      if not m:
        raise SyntaxError, line
      self.fields[m.group(3).lower()] = (int(m.group(1)), int(m.group(2)) + 1)
    igc.i = self


PARSERS = {
    'A': ARecord,
    'C': CRecord,
    'B': BRecord,
    'G': GRecord,
    'H': HRecord,
    'I': IRecord,
    }


class IGC(object):

  def __init__(self, filename):
    global PARSERS
    self.filename = filename
    self.c = []
    self.g = []
    self.h = {}
    self.i = None
    ignore = lambda l, s: None
    with open(filename) as file:
      self.records = [PARSERS.get(line[0], ignore)(line, self) for line in file]

  def track(self):
    coords = TimeSeries()
    times = []
    t = []
    t0 = datetime.datetime(2000, 1, 1)
    for record in self.records:
      if not isinstance(record, BRecord):
        continue
      coords.append(coord.Coord(record.lat, record.lon, record.ele))
      times.append(record.dt)
      t.append((record.dt - t0).seconds)
    coords.t = t
    meta = OpenStruct(name=self.filename, pilot_name=None, glider_type=None, glider_id=None)
    if 'plt' in self.h and not NOT_SET_RE.match(self.h['plt']):
      meta.pilot_name = self.h['plt'].strip()
    if 'gty' in self.h and not NOT_SET_RE.match(self.h['gty']):
      meta.glider_type = self.h['gty'].strip()
    if 'gid' in self.h and not NOT_SET_RE.match(self.h['gid']):
      meta.glider_id = self.h['gid'].strip()
    return track.Track(meta, times, coords)
