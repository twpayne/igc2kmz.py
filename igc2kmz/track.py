import igc2kmz.util


class Track(object):

  def __init__(self, meta, times, coords):
    self.meta = meta
    self.times = times
    self.coords = coords
    self.analyse(20)

  def analyse(self, dt):
    n = len(self.coords)
    self.bounds = igc2kmz.util.BoundsSet()
    self.bounds.ele = igc2kmz.util.Bounds(self.coords[0].ele)
    for coord in self.coords:
      self.bounds.ele.merge(coord.ele)
    self.bounds.time = igc2kmz.util.Bounds((self.times[0], self.times[-1]))
    self.elevation_data = self.bounds.ele.min != 0 or self.bounds.ele.max != 0
    self.s = [0.0]
    for i in xrange(1, n):
      self.s.append(self.s[i - 1] + self.coords[i - 1].distance_to(self.coords[i]))
    self.ele = []
    for i in xrange(1, n):
      self.ele.append((self.coords[i - 1].ele + self.coords[i].ele) / 2.0)
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
    self.thermal = []
    i0 = i1 = 0
    for i in xrange(1, n):
      t0 = (self.coords.t[i - 1] + self.coords.t[i]) / 2 - dt / 2
      while self.coords.t[i0] <= t0:
        i0 += 1
      if i0 == 0:
        coord0 = self.coords[0]
        s0 = self.s[0]
      else:
        delta0 = float(t0 - self.coords.t[i0 - 1]) / (self.coords.t[i0] - self.coords.t[i0 - 1])
        coord0 = self.coords[i0 - 1].interpolate(self.coords[i0], delta0)
        s0 = (1.0 - delta0) * self.s[i0 - 1] + delta0 * self.s[i0]
      t1 = t0 + dt
      while i1 < n and self.coords.t[i1] < t1:
        i1 += 1
      if i1 == n:
        coord1 = self.coords[n - 1]
        s1 = self.s[n - 1]
      else:
        delta1 = float(t1 - self.coords.t[i1 - 1]) / (self.coords.t[i1] - self.coords.t[i1 - 1])
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
      if climb >= 0.0:
        if progress < 0.9:
          thermal = 1.0
        else:
          thermal = 0.75
      else:
        if progress < 0.9:
          thermal = 0.5
        else:
          thermal = 0.0
      self.speed.append(3.6 * ds / dt)
      self.climb.append(dz / dt)
      self.progress.append(progress)
      self.thermal.append(thermal)
    self.bounds.speed = igc2kmz.util.Bounds(self.speed)
    self.bounds.climb = igc2kmz.util.Bounds(self.climb)
