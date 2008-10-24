#   igc2kmz/coord.py  igc2kmz coordinate functions
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


from math import acos, asin, atan2, cos, pi, sin, sqrt


R = 6371000.0
compass = 'N NNE NE ENE E ESE SE SSE S SSW SW WSW W WNW NW NNW'.split()


def rad_to_compass(rad):
    while rad < 0.0:
        rad += 2 * pi
    return compass[int(8 * rad / pi + 0.5) % 16]


class degreeattr(object):

    def __init__(self, attr):
        self.attr = attr

    def __get__(self, obj, type=None):
        return 180.0 * getattr(obj, self.attr) / pi

    def __set__(self, obj, value):
        setattr(obj, self.attr, pi * value / 180.0)


class degreemethod(object):

    def __new__(cls, f):
        def deg_f(*args, **kwargs):
            return 180.0 * f(*args, **kwargs) / pi
        return deg_f


class Coord(object):

    __slots__ = ('lat', 'lon', 'ele', 'dt')

    lat_deg = degreeattr('lat')
    lon_deg = degreeattr('lon')

    def __init__(self, lat, lon, ele, dt=None):
        self.lat = lat
        self.lon = lon
        self.ele = ele
        self.dt = dt

    @classmethod
    def deg(cls, lat, lon, ele, dt=None):
        return cls(pi * lat / 180.0, pi * lon / 180.0, ele, dt)

    def dup(self):
        return Coord(self.lat, self.lon, self.ele, self.dt)

    def initial_bearing_to(self, other):
        """Return the initial bearing from self to other."""
        y = sin(other.lon - self.lon) * cos(other.lat)
        x = cos(self.lat) * sin(other.lat) \
            - sin(self.lat) * cos(other.lat) * cos(other.lon - self.lon)
        return atan2(y, x)

    initial_bearing_to_deg = degreemethod(initial_bearing_to)

    def distance_to(self, other):
        """Return the distance from self to other."""
        d = sin(self.lat) * sin(other.lat) \
            + cos(self.lat) * cos(other.lat) * cos(self.lon - other.lon)
        return R * acos(d) if d < 1.0 else 0.0

    def halfway_to(self, other):
        """Return the point halfway between self and other."""
        bx = cos(other.lat) * cos(other.lon - self.lon)
        by = cos(other.lat) * sin(other.lon - self.lon)
        cos_lat_plus_bx = cos(self.lat) + bx
        lat = atan2(sin(self.lat) + sin(other.lat),
                    sqrt(cos_lat_plus_bx * cos_lat_plus_bx + by * by))
        lon = self.lon + atan2(by, cos_lat_plus_bx)
        ele = (self.ele + other.ele) / 2.0
        return Coord(lat, lon, ele)

    def interpolate(self, other, delta):
        """Return the point delta between self and other."""
        d = sin(self.lat) * sin(other.lat) \
            + cos(self.lat) * cos(other.lat) * cos(other.lon - self.lon)
        d = delta * acos(d) if d < 1.0 else 0.0
        y = sin(other.lon - self.lon) * cos(other.lat)
        x = cos(self.lat) * sin(other.lat) \
            - sin(self.lat) * cos(other.lat) * cos(other.lon - self.lon)
        theta = atan2(y, x)
        lat = asin(sin(self.lat) * cos(d) + cos(self.lat) * sin(d) * cos(theta))
        lon = self.lon + atan2(sin(theta) * sin(d) * cos(self.lat),
                               cos(d) - sin(self.lat) * sin(lat))
        ele = (1.0 - delta) * self.ele + delta * other.ele
        return Coord(lat, lon, ele)

    def coord_at(self, theta, d):
        """Return the point d from self in direction theta."""
        lat = asin(sin(self.lat) * cos(d / R) \
                   + cos(self.lat) * sin(d / R) * cos(theta))
        lon = self.lon + atan2(sin(theta) * sin(d / R) * cos(self.lat),
                               cos(d / R) - sin(self.lat) * sin(lat))
        ele = self.ele
        return Coord(lat, lon, ele)
