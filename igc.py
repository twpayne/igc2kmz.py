import datetime
import os.path
import time
import re
import sys

import coord
import track
from TimeSeries import TimeSeries
from OpenStruct import OpenStruct


A_RECORD_RE = re.compile(r'A(.*)\Z')
B_RECORD_RE = re.compile(r'B(\d{2})(\d{2})(\d{2})(\d{2})(\d{5})([NS])(\d{3})(\d{5})([EW])([AV])(\d{5})(\d{5})\d*\Z')
C_RECORD_RE = re.compile(r'C(\d{2})(\d{5})([NS])(\d{3})(\d{5})([EW])(.*)\Z')
G_RECORD_RE = re.compile(r'G(.*)\Z')
HFDTE_RECORD_RE = re.compile(r'H(F)(DTE)(\d\d)(\d\d)(\d\d)\Z')
HFFXA_RECORD_RE = re.compile(r'H(F)(FXA)(\d+)\Z')
H_RECORD_RE = re.compile(r'H([FOP])([A-Z]{3})[A-Z]*:(.*)\Z')
I_RECORD_RE = re.compile(r'(\d{2})(\d{2})(\w{3})\Z')
L_RECORD_RE = re.compile(r'L(.*)\Z')

NOT_SET_RE = re.compile(r'\s*(not\s+set)?\s*\Z')


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


class IRecord(Record):

  def __init__(self, line, igc):
    self.fields = {}
    for i in xrange(0, int(line[1:3])):
      m = I_RECORD_RE.match(line, 3 + 7 * i, 10 + 7 * i)
      if not m:
        raise SyntaxError, line
      self.fields[m.group(3).lower()] = (int(m.group(1)), int(m.group(2)) + 1)
    igc.i = self


class LRecord(Record):

  def __init__(self, line, igc):
    m = L_RECORD_RE.match(line)
    if not m:
      raise SyntaxError, line
    igc.l.append(m.group(1))


class IGC(object):

  def __init__(self, filename):
    self.filename = filename
    self.c = []
    self.g = []
    self.h = {}
    self.i = None
    self.l = []
    ignore = lambda l, s: l
    self.records = []
    for line in open(filename):
      try:
        self.records.append(class_by_letter.get(line[0], ignore)(line.rstrip(), self))
      except SyntaxError:
        pass

  def track(self):
    times = []
    t = []
    for record in self.records:
      if isinstance(record, BRecord) and record.ele:
        ele = 'ele'
        break
    else:
      ele = 'alt'
    coords = TimeSeries()
    for record in self.records:
      if isinstance(record, BRecord):
        coords.append(coord.Coord(record.lat, record.lon, getattr(record, ele)))
        times.append(record.dt)
        t.append(int(time.mktime(record.dt.timetuple())))
    coords.t = t
    meta = OpenStruct(name=os.path.basename(self.filename), pilot_name=None, glider_type=None, glider_id=None)
    if 'plt' in self.h and not NOT_SET_RE.match(self.h['plt']):
      meta.pilot_name = self.h['plt'].strip()
    if 'gty' in self.h and not NOT_SET_RE.match(self.h['gty']):
      meta.glider_type = self.h['gty'].strip()
    if 'gid' in self.h and not NOT_SET_RE.match(self.h['gid']):
      meta.glider_id = self.h['gid'].strip()
    return track.Track(meta, times, coords)
