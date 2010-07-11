#   igc2kmz IGC functions
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

from coord import Coord
import track


A_RECORD_RE = re.compile(r'A(.*)\Z')
B_RECORD_RE = re.compile(r'B(\d{2})(\d{2})(\d{2})(\d{2})(\d{5})([NS])'
                         r'(\d{3})(\d{5})([EW])([AV])(\d{5})(\d{5}).*\Z')
C_RECORD_RE = re.compile(r'C(\d{2})(\d{5})([NS])(\d{3})(\d{5})([EW])(.*)\Z')
E_RECORD_RE = re.compile(r'E(\d{2})(\d{2})(\d{2})(\w{3})(.*)\Z')
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

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__,
                           ', '.join('%s=%s' % (key, repr(value))
                                     for key, value in self.__dict__.items()))


class ARecord(Record):

    @classmethod
    def parse(cls, line, igc):
        result = cls()
        m = A_RECORD_RE.match(line)
        if not m:
            raise SyntaxError, line
        result.value = m.group(1)
        igc.a = result.value
        return result


class BRecord(Record):

    @classmethod
    def parse(cls, line, igc):
        result = cls()
        m = B_RECORD_RE.match(line)
        if not m:
            raise SyntaxError, line
        for key, value in igc.i.items():
            try:
                setattr(result, key, int(line[value]))
            except ValueError:
                setattr(result, key, None)
        time = datetime.time(*map(int, m.group(1, 2, 3)))
        if 'tds' in igc.i:
            time = time.replace(microsecond=int(line[igc.i['tds']]) * 100000)
        result.dt = datetime.datetime.combine(igc.hfdterecord.date, time)
        if igc.b and result.dt < igc.b[-1].dt:
            igc.hfdterecord.date = datetime.date.fromordinal(
                    igc.hfdterecord.date.toordinal() + 1)
            result.dt = datetime.datetime.combine(igc.hfdterecord.date, time)
        result.lat = int(m.group(4)) + int(m.group(5)) / 60000.0
        if 'lad' in igc.i:
            result.lat += int(line[igc.i['lad']]) / 6000000.0
        if m.group(6) == 'S':
            result.lat *= -1
        result.lon = int(m.group(7)) + int(m.group(8)) / 60000.0
        if 'lod' in igc.i:
            result.lon += int(line[igc.i['lod']]) / 6000000.0
        if m.group(9) == 'W':
            result.lon *= -1
        result.validity = m.group(10)
        result.alt = int(m.group(11))
        result.ele = int(m.group(12))
        igc.b.append(result)
        return result


class CRecord(Record):

    @classmethod
    def parse(cls, line, igc):
        result = cls()
        m = C_RECORD_RE.match(line)
        if not m:
            raise SyntaxError, line
        result.lat = int(m.group(1)) + int(m.group(2)) / 60000.0
        if m.group(3) == 'S':
            result.lat *= -1
        result.lon = int(m.group(4)) + int(m.group(5)) / 60000.0
        if m.group(6) == 'W':
            result.lon *= -1
        result.name = m.group(7)
        igc.c.append(result)
        return result


class ERecord(Record):

    @classmethod
    def parse(cls, line, igc):
        result = cls()
        m = E_RECORD_RE.match(line)
        if not m:
            raise SyntaxError, line
        result.value = m.group(4)
        return result


class GRecord(Record):

    @classmethod
    def parse(cls, line, igc):
        result = cls()
        m = G_RECORD_RE.match(line)
        if not m:
            raise SyntaxError, line
        result.value = m.group(1)
        igc.g.append(result.value)
        return result


class HRecord(Record):

    @classmethod
    def parse(cls, line, igc):
        result = cls()
        m = HFDTE_RECORD_RE.match(line)
        if m:
            result.source, result.type = m.group(1, 2)
            day, month, year = map(int, m.group(3, 4, 5))
            try:
                result.date = datetime.date(2000 + year, month, day)
            except ValueError:
                raise SyntaxError, line
            igc.hfdterecord = result
            return result
        m = HFFXA_RECORD_RE.match(line)
        if m:
            result.source, result.type = m.group(1, 2)
            result.value = int(m.group(3))
            igc.h['fxa'] = result.value
            return result
        m = H_RECORD_RE.match(line)
        if m:
            result.source, result.key, result.value = m.groups()
            igc.h[result.key.lower()] = result.value
            return result
        raise SyntaxError, line


class IRecord(Record):

    @classmethod
    def parse(cls, line, igc):
        result = cls()
        for i in xrange(0, int(line[1:3])):
            m = I_RECORD_RE.match(line, 3 + 7 * i, 10 + 7 * i)
            if not m:
                raise SyntaxError, line
            igc.i[m.group(3).lower()] = slice(int(m.group(1)) - 1,
                                              int(m.group(2)))
        return result


class LRecord(Record):

    @classmethod
    def parse(cls, line, igc):
        result = cls()
        m = L_RECORD_RE.match(line)
        if not m:
            raise SyntaxError, line
        igc.l.append(m.group(1))
        return result


class IGC(object):

    def __init__(self, file, date=None):
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
        if date:
            HRecord.parse(date.strftime('HFDTE%d%m%y'), self)
        for line in file:
            try:
                line = line.rstrip()
                letter = line[0]
                if letter in class_by_letter:
                    klass = class_by_letter[letter]
                    self.records.append(klass.parse(line, self))
                else:
                    logging.warning('%s: unknown record %s'
                                    % (self.filename, repr(line)))
            except SyntaxError:
                logging.warning('%s: invalid record %s'
                                % (self.filename, repr(line)))

    def track(self):
        ele = 'ele' if any(b.ele for b in self.b) else 'alt'
        coords = [Coord.deg(b.lat, b.lon, getattr(b, ele), b.dt)
                  for b in self.b]
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


if __name__ == '__main__':
    import sys
    print repr(IGC(sys.stdin).__dict__)
