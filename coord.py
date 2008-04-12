from math import acos, atan2, cos, pi, sin, sqrt

R = 6371000.0

def _deg_to_rad(deg):
  return pi * deg / 180.0

def _rad_to_deg(rad):
  return 180.0 * rad / pi

class Coord:

  def __init__(self, lat, lon, ele):
    self.lat, self.lon, self.ele = lat, lon, ele

  def distance_to(self, other):
    "Return the distance from self to other."
    lat1 = _deg_to_rad(self.lat)
    lon1 = _deg_to_rad(self.lon)
    lat2 = _deg_to_rad(other.lat)
    lon2 = _deg_to_rad(other.lon)
    d = sin(lat1) * sin(lat2) + cos(lat1) * cos(lat2) * cos(lon1 - lon2)
    return R * acos(d) if d < 1.0 else 0.0

  def halfway_to(self, other):
    "Return the point halfway between self and other."
    lat1 = _deg_to_rad(self.lat)
    lon1 = _deg_to_rad(self.lon)
    ele1 = self.ele
    lat2 = _deg_to_rad(other.lat)
    lon2 = _deg_to_rad(other.lon)
    ele2 = other.ele
    bx = cos(lat2) * cos(lon1 - lon2)
    by = cos(lat2) * sin(lon1 - lon2)
    cos_lat1_plus_bx = cos(lat1) + bx
    lat = _rad_to_deg(atan2(sin(lat1) + sin(lat2), sqrt(cos_lat1_plus_bx * cos_lat1_plus_bx + by * by)))
    lon = _rad_to_deg(lon1 + atan2(by, cos_lat1_plus_bx))
    ele = (ele1 + ele2) / 2.0
    return Coord(lat, lon, ele)
