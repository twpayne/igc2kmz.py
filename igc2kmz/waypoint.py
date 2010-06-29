#   igc2kmz waypoint functions
#   Copyright (C) 2010  Tom Payne
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


from math import pi

from coord import Coord


class Waypoint(Coord):

    def __init__(self, name, lat, lon, ele, description=None):
        Coord.__init__(self, lat, lon, ele)
        self.name = name
        self.description = description

    @classmethod
    def deg(cls, name, lat, lon, ele, description=None):
        return cls(name, pi * lat / 180.0, pi * lon / 180.0, ele, description)
