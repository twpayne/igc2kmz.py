#   igc2kmz/track.py  igc2kmz track functions
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


class Track(object):

  def __init__(self, coords, **kwargs):
    self.coords = coords
    self.t = [int(time.mktime(c.dt.timetuple())) for c in self.coords]
    self.pilot_name = None
    self.glider_type = None
    self.glider_id = None
    self.__dict__.update(kwargs)
    self.analyse(20)

  def merge_adjacent_sequences(self, seq, delta):
    start, stop = seq[0].start, seq[0].stop
    result = []
    for i in xrange(1, len(seq)):
      if self.t[seq[i].start] - self.t[stop] < delta:
        stop = seq[i].stop
      else:
        if delta < self.t[stop] - self.t[start]:
          result.append(slice(start, stop))
        start, stop = seq[i].start, seq[i].stop
    result.append(slice(start, stop))
    return result

  def analyse(self, dt):
    def do_set(seq, slices, value):
      for sl in slices:
        seq[sl] = [value] * (sl.stop - sl.start)
    n = len(self.coords)
    self.bounds = util.BoundsSet()
    self.bounds.ele = util.Bounds([coord.ele for coord in self.coords])
    self.bounds.time = util.Bounds((self.coords[0].dt, self.coords[-1].dt))
    if hasattr(self, 'tas'):
      self.bounds.tas = util.Bounds(self.tas)
    self.elevation_data = self.bounds.ele.min != 0 or self.bounds.ele.max != 0
    self.s = [0.0]
    for i in xrange(1, n):
      self.s.append(self.s[i - 1] + self.coords[i - 1].distance_to(self.coords[i]))
    self.ele = [(self.coords[i - 1].ele + self.coords[i].ele) / 2.0 for i in xrange(1, n)]
    self.total_dz_positive = 0
    self.max_dz_positive = 0
    min_ele = self.coords[0].ele
    for i in xrange(1, n):
      dz = self.coords[i].ele - self.coords[i - 1].ele
      if dz > 0:
        self.total_dz_positive += dz
      if self.coords[i].ele < min_ele:
        min_ele = self.coords[i].ele
      elif self.coords[i].ele - min_ele > self.max_dz_positive:
        self.max_dz_positive = self.coords[i].ele - min_ele
    self.speed = []
    self.climb = []
    self.progress = []
    i0 = i1 = 0
    for i in xrange(1, n):
      t0 = (self.t[i - 1] + self.t[i]) / 2 - dt / 2
      while self.t[i0] <= t0:
        i0 += 1
      if i0 == 0:
        coord0 = self.coords[0]
        s0 = self.s[0]
      else:
        delta0 = float(t0 - self.t[i0 - 1]) / (self.t[i0] - self.t[i0 - 1])
        coord0 = self.coords[i0 - 1].interpolate(self.coords[i0], delta0)
        s0 = (1.0 - delta0) * self.s[i0 - 1] + delta0 * self.s[i0]
      t1 = t0 + dt
      while i1 < n and self.t[i1] < t1:
        i1 += 1
      if i1 == n:
        coord1 = self.coords[n - 1]
        s1 = self.s[n - 1]
      else:
        delta1 = float(t1 - self.t[i1 - 1]) / (self.t[i1] - self.t[i1 - 1])
        coord1 = self.coords[i1 - 1].interpolate(self.coords[i1], delta1)
        s1 = (1.0 - delta1) * self.s[i1 - 1] + delta1 * self.s[i1]
      ds = s1 - s0
      dz = coord1.ele - coord0.ele
      dp = coord0.distance_to(coord1)
      climb = dz / dt
      if ds == 0.0:
        progress = 0.0
      elif dp > ds:
        progress = 1.0
      else:
        progress = dp / ds
      self.speed.append(3.6 * ds / dt)
      self.climb.append(dz / dt)
      self.progress.append(progress)
    self.bounds.speed = util.Bounds(self.speed)
    self.bounds.climb = util.Bounds(self.climb)
    state = [0] * (n - 1)
    glide = [self.progress[i] >= 0.8 for i in xrange(0, n - 1)]
    glide_pairs = [sl for sl in util.runs(glide) if glide[sl.start]]
    glide_pairs = self.merge_adjacent_sequences(glide_pairs, 60)
    do_set(state, glide_pairs, 3)
    dive = [self.progress[i] < 0.9 and self.climb[i] < 0.0 for i in xrange(0, n - 1)]
    dive_pairs = [sl for sl in util.runs(dive) if dive[sl.start]]
    dive_pairs = self.merge_adjacent_sequences(dive_pairs, 30)
    do_set(state, dive_pairs, 2)
    thermal = [self.progress[i] < 0.9 and self.climb[i] >= 0.0 for i in xrange(0, n - 1)]
    thermal_pairs = [sl for sl in util.runs(thermal) if thermal[sl.start]]
    thermal_pairs = self.merge_adjacent_sequences(thermal_pairs, 60)
    do_set(state, thermal_pairs, 1)
    self.thermals = []
    self.glides = []
    self.dives = []
    for sl in util.runs(state):
      if state[sl.start] == 1 and self.t[sl.stop] - self.t[sl.start] >= 60:
        self.thermals.append(sl)
      elif state[sl.start] == 2 and (self.coords[sl.stop].ele - self.coords[sl.start].ele) / (self.t[sl.stop] - self.t[sl.start]) < -3:
        self.dives.append(sl)
      elif state[sl.start] == 3 and self.t[sl.stop] - self.t[sl.start] >= 60:
        self.glides.append(sl)
      else:
        pass
