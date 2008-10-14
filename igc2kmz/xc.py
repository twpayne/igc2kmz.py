#   igc2kmz.py  igc2kmz XC module
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
import xml.etree.ElementTree

from coord import Coord


class Turnpoint(object):

    def __init__(self, name, coord):
        self.name = name
        self.coord = coord

    @classmethod
    def from_element(cls, rtept):
        name = rtept.findtext('name').encode('utf_8')
        lat = float(rtept.get('lat'))
        lon = float(rtept.get('lon'))
        ele_tag = rtept.find('ele')
        ele = int(ele_tag.text) if ele_tag else 0
        dt = datetime.datetime.strptime(rtept.findtext('time'),
                                        '%Y-%m-%dT%H:%M:%SZ')
        coord = Coord.deg(lat, lon, ele, dt)
        return cls(name, coord)


class Rte(object):

    def __init__(self, name, league, distance, multiplier, score, circuit, tps):
        self.name = name
        self.league = league
        self.distance = distance
        self.multiplier = multiplier
        self.score = score
        self.circuit = circuit
        self.tps = tps

    @classmethod
    def from_element(cls, rte):
        name = rte.findtext('name').encode('utf_8')
        league = rte.findtext('extensions/league').encode('utf_8')
        distance = float(rte.findtext('extensions/distance'))
        multiplier = float(rte.findtext('extensions/multiplier'))
        score = float(rte.findtext('extensions/score'))
        circuit = not rte.find('extensions/circuit') is None
        tps = map(Turnpoint.from_element, rte.findall('rtept'))
        return cls(name, league, distance, multiplier, score, circuit, tps)


class XC(object):

    def __init__(self, routes):
        self.routes = routes

    @classmethod
    def from_element(cls, element):
        routes = map(Rte.from_element, element.findall('/rte'))
        return cls(routes)

    @classmethod
    def from_file(cls, file):
        element = xml.etree.ElementTree.parse(file)
        return cls.from_element(element)
