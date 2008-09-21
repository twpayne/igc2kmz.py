from math import acos, asin, atan2, cos, pi, sin, sqrt

R = 6371000.0

class Coord(object):

  __slots__ = ('lat', 'lon', 'ele', 'dt')

  def __init__(self, lat, lon, ele, dt=None):
    self.lat = lat
    self.lon = lon
    self.ele = ele
    self.dt = dt

  @classmethod
  def deg(cls, lat, lon, ele, dt=None):
    return cls(pi * lat / 180.0, pi * lon / 180.0, ele, dt)

  def bearing_to(self, other):
    return atan2(sin(other.lon - self.lon) * cos(other.lat), cos(self.lat) * sin(other.lat) - sin(self.lat) * cos(other.lat) * cos(lon))

  def distance_to(self, other):
    """Return the distance from self to other."""
    d = sin(self.lat) * sin(other.lat) + cos(self.lat) * cos(other.lat) * cos(self.lon - other.lon)
    if d < 1.0:
      return R * acos(d)
    else:
      return 0.0

  def halfway_to(self, other):
    """Return the point halfway between self and other."""
    bx = cos(other.lat) * cos(other.lon - self.lon)
    by = cos(other.lat) * sin(other.lon - self.lon)
    cos_lat_plus_bx = cos(self.lat) + bx
    lat = atan2(sin(self.lat) + sin(other.lat), sqrt(cos_lat_plus_bx * cos_lat_plus_bx + by * by))
    lon = self.lon + atan2(by, cos_lat_plus_bx)
    ele = (self.ele + other.ele) / 2.0
    return Coord(lat, lon, ele)

  def interpolate(self, other, delta):
    """Return the point delta between self and other."""
    d = sin(self.lat) * sin(other.lat) + cos(self.lat) * cos(other.lat) * cos(other.lon - self.lon)
    if d < 1.0:
      d = delta * acos(d)
    else:
      d = 0.0
    theta = atan2(sin(other.lon - self.lon) * cos(other.lat), cos(self.lat) * sin(other.lat) - sin(self.lat) * cos(other.lat) * cos(other.lon - self.lon))
    lat3 = asin(sin(self.lat) * cos(d) + cos(self.lat) * sin(d) * cos(theta))
    lon3 = self.lon + atan2(sin(theta) * sin(d) * cos(self.lat), cos(d) - sin(self.lat) * sin(lat3))
    ele3 = (1.0 - delta) * self.ele + delta * other.ele
    return Coord(lat3, lon3, ele3)
