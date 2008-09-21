from math import acos, asin, atan2, cos, pi, sin, sqrt

R = 6371000.0

def _deg_to_rad(deg):
  return pi * deg / 180.0

def _rad_to_deg(rad):
  return 180.0 * rad / pi

class Coord(object):

  __slots__ = ('lat', 'lon', 'ele', 'dt')

  def __init__(self, lat, lon, ele, dt=None):
    self.lat = lat
    self.lon = lon
    self.ele = ele
    self.dt = dt

  def __repr__(self):
    return 'Coord(%f, %f, %f, %s)' % (self.lat, self.lon, self.ele, self.dt)

  def distance_to(self, other):
    """Return the distance from self to other."""
    lat1 = _deg_to_rad(self.lat)
    lon1 = _deg_to_rad(self.lon)
    lat2 = _deg_to_rad(other.lat)
    lon2 = _deg_to_rad(other.lon)
    d = sin(lat1) * sin(lat2) + cos(lat1) * cos(lat2) * cos(lon1 - lon2)
    if d < 1.0:
      return R * acos(d)
    else:
      return 0.0

  def halfway_to(self, other):
    """Return the point halfway between self and other."""
    lat1 = _deg_to_rad(self.lat)
    lon1 = _deg_to_rad(self.lon)
    lat2 = _deg_to_rad(other.lat)
    lon2 = _deg_to_rad(other.lon)
    bx = cos(lat2) * cos(lon2 - lon1)
    by = cos(lat2) * sin(lon2 - lon1)
    cos_lat1_plus_bx = cos(lat1) + bx
    lat = _rad_to_deg(atan2(sin(lat1) + sin(lat2), sqrt(cos_lat1_plus_bx * cos_lat1_plus_bx + by * by)))
    lon = _rad_to_deg(lon1 + atan2(by, cos_lat1_plus_bx))
    ele = (self.ele + other.ele) / 2.0
    return Coord(lat, lon, ele)

  def interpolate(self, other, delta):
    """Return the point delta between self and other."""
    lat1 = _deg_to_rad(self.lat)
    lon1 = _deg_to_rad(self.lon)
    lat2 = _deg_to_rad(other.lat)
    lon2 = _deg_to_rad(other.lon)
    cos_lat1 = cos(lat1)
    sin_lat1 = sin(lat1)
    cos_lat2 = cos(lat2)
    sin_lat2 = sin(lat2)
    lon = lon2 - lon1
    cos_lon = cos(lon)
    d = sin_lat1 * sin_lat2 + cos_lat1 * cos_lat2 * cos_lon
    if d < 1.0:
      d = delta * acos(d)
    else:
      d = 0.0
    theta = atan2(sin(lon) * cos_lat2, cos_lat1 * sin_lat2 - sin_lat1 * cos_lat2 * cos_lon)
    cos_d = cos(d)
    sin_d = sin(d)
    lat3 = _rad_to_deg(asin(sin_lat1 * cos_d + cos_lat1 * sin_d * cos(theta)))
    lon3 = _rad_to_deg(lon1 + atan2(sin(theta) * sin_d * cos_lat1, cos_d - sin_lat1 * sin(lat3)))
    ele3 = (1.0 - delta) * self.ele + delta * other.ele
    return Coord(lat3, lon3, ele3)
