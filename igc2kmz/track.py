#   igc2kmz track functions
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


import time

import util


UNKNOWN = 0
THERMAL = 1
GLIDE = 2
DIVE = 3


class Track(object):

    def __init__(self, coords, **kwargs):
        self.coords = Track.filter(coords)
        self.t = [int(time.mktime(c.dt.timetuple())) for c in self.coords]
        self.pilot_name = None
        self.glider_type = None
        self.glider_id = None
        self.declaration = None
        self.__dict__.update(kwargs)
        self.analyse(20)

    @classmethod
    def filter(self, coords):
        """Filter out erroneous points."""
        # TODO replace with Kahlman filter?
        # TODO cope with erroneous points at start of track
        result = [coords[0]]
        last_c = coords[0]
        for c in coords:
            if c.dt <= last_c.dt:
                continue
            ds = last_c.distance_to(c)
            dt = (c.dt - last_c.dt).seconds
            if dt == 0:
                dt=0.001
            if ds / dt > 100.0:
                continue
            dz = c.ele - last_c.ele
            if dz / dt < -30.0 or 30.0 < dz / dt:
                continue
            result.append(c)
            last_c = c
        return result

    def coord_at(self, dt):
        t = int(time.mktime(dt.timetuple()))
        if t < self.t[0]:
            return self.coords[0]
        elif self.t[-1] <= t:
            return self.coords[-1]
        else:
            index = util.find_first_ge(self.t, t)
            if self.t[index] == t:
                return self.coords[index]
            else:
                delta = float(t - self.t[index - 1]) \
                        / (self.t[index] - self.t[index - 1])
                return self.coords[index - 1].interpolate(self.coords[index],
                                                          delta)

    def analyse(self, dt):
        n = len(self.coords)
        period = (self.coords[-1].dt - self.coords[0].dt).seconds / n
        if dt < 2 * period:
            dt = 2 * period
        self.bounds = util.BoundsSet()
        self.bounds.ele = util.Bounds([coord.ele for coord in self.coords])
        self.bounds.time = util.Bounds((self.coords[0].dt, self.coords[-1].dt))
        self.bounds.t = util.Bounds((self.t[0], self.t[-1]))
        if hasattr(self, 'tas'):
            self.bounds.tas = util.Bounds(self.tas)
        if self.bounds.ele.min != 0 or self.bounds.ele.max != 0:
            self.elevation_data = True
        else:
            self.elevation_data = False
        self.s = [0.0]
        for i in xrange(1, n):
            self.s.append(self.s[i - 1] +
                          self.coords[i - 1].distance_to(self.coords[i]))
        self.ele = [(self.coords[i - 1].ele + self.coords[i].ele) / 2.0
                    for i in xrange(1, n)]
        self.total_dz_positive = self.max_dz_positive = 0
        min_ele = self.coords[0].ele
        for i in xrange(1, n):
            dz = self.coords[i].ele - self.coords[i - 1].ele
            if dz > 0:
                self.total_dz_positive += dz
            if self.coords[i].ele < min_ele:
                min_ele = self.coords[i].ele
            elif self.coords[i].ele - min_ele > self.max_dz_positive:
                self.max_dz_positive = self.coords[i].ele - min_ele
        self.speed, self.climb, self.tec, self.progress = [], [], [], []
        i0 = i1 = 0
        for i in xrange(1, n):
            t0 = (self.t[i - 1] + self.t[i]) / 2 - dt / 2
            while self.t[i0] <= t0:
                i0 += 1
            if i0 == 0:
                coord0 = self.coords[0]
                s0 = self.s[0]
            else:
                delta0 = float(t0 - self.t[i0 - 1]) \
                         / (self.t[i0] - self.t[i0 - 1])
                coord0 = self.coords[i0 - 1].interpolate(self.coords[i0],
                                                         delta0)
                s0 = (1.0 - delta0) * self.s[i0 - 1] + delta0 * self.s[i0]
            t1 = t0 + dt
            while i1 < n and self.t[i1] < t1:
                i1 += 1
            if i1 == n:
                coord1 = self.coords[n - 1]
                s1 = self.s[n - 1]
            else:
                delta1 = float(t1 - self.t[i1 - 1]) \
                         / (self.t[i1] - self.t[i1 - 1])
                coord1 = self.coords[i1 - 1].interpolate(self.coords[i1],
                                                         delta1)
                s1 = (1.0 - delta1) * self.s[i1 - 1] + delta1 * self.s[i1]
            ds = s1 - s0
            ds2 = s1 * s1 - s0 * s0
            dz = coord1.ele - coord0.ele
            dp = coord0.distance_to(coord1)
            if ds == 0.0:
                progress = 0.0
            elif dp > ds:
                progress = 1.0
            else:
                progress = dp / ds
            self.speed.append(3.6 * ds / dt)
            self.climb.append(dz / dt)
            self.tec.append(dz / dt + ds2 / (2 * 9.80665))
            self.progress.append(progress)
        self.bounds.speed = util.Bounds(self.speed)
        self.bounds.climb = util.Bounds(self.climb)
        self.bounds.tec = util.Bounds(self.tec)
        state = [UNKNOWN] * (n - 1)
        glide = (self.progress[i] >= 0.9 for i in xrange(0, n - 1))
        for sl in util.condense(util.runs_where(glide), self.t, 60):
            state[sl] = [GLIDE] * (sl.stop - sl.start)
        dive = (self.progress[i] < 0.9 and self.climb[i] < 1.0
                for i in xrange(0, n - 1))
        for sl in util.condense(util.runs_where(dive), self.t, 30):
            if self.coords[sl.stop].ele - self.coords[sl.start].ele < -100:
                state[sl] = [DIVE] * (sl.stop - sl.start)
        thermal = ((self.progress[i] < 0.9 and self.climb[i] > 0.0)
                   or (self.speed[i] < 10.0 and self.climb[i] > 0.0)
                   or (self.climb[i] > 1.0)
                   for i in xrange(0, n - 1))
        for sl in util.condense(util.runs_where(thermal), self.t, 60):
            state[sl] = [THERMAL] * (sl.stop - sl.start)
        self.thermals, self.glides, self.dives = [], [], []
        for sl in util.runs(state):
            dt = self.t[sl.stop] - self.t[sl.start]
            dz = self.coords[sl.stop].ele - self.coords[sl.start].ele
            if state[sl.start] == THERMAL:
                if dt >= 60 and dz > 50:
                    self.thermals.append(sl)
            elif state[sl.start] == DIVE:
                if dt >= 30 and dz / dt < -2:
                    self.dives.append(sl)
            elif state[sl.start] == GLIDE:
                if dt >= 120:
                    self.glides.append(sl)
