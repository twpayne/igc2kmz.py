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

class Error(RuntimeError):
  pass

class SyntaxError(Error):
  pass


class ARecord:

  def __init__(self, line, igc):
    m = A_RECORD_RE.match(line)
    if not m:
      raise SyntaxError, line
    self.value = m.group(1)
    igc.a = self.value


class CRecord:

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


class BRecord:

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
    for key, value in igc.i.fields.items():
      setattr(self, key, int(line[value[0]:value[1]]))


class GRecord:

  def __init__(self, line, igc):
    m = G_RECORD_RE.match(line)
    if not m:
      raise SyntaxError, m
    self.value = m.group(1)
    igc.g.append(self.value)


class HRecord:

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


class IRecord:

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


class IGC:

  def __init__(self, input):
    global PARSERS
    self.c = []
    self.g = []
    self.h = {}
    ignore = lambda l, s: None
    self.records = [PARSERS.get(line[0], ignore)(line, self) for line in input]

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
    meta = OpenStruct()
    if self.h.has_key('plt') and self.h['plt'].strip() != 'not set':
      meta.pilot_name = self.h['plt'].strip()
    else:
      meta.pilot_name = None
    if self.h.has_key('gty') and self.h['gty'].strip() != 'not set':
      meta.glider_type = self.h['gty'].strip()
    else:
      meta.glider_type = None
    if self.h.has_key('gid') and self.h['gid'].strip() != 'not set':
      meta.glider_id = self.h['gid'].strip()
    else:
      meta.glider_id = None
    return track.Track(meta, times, coords)
