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


from __future__ import with_statement

import datetime
try:
    from xml.etree.cElementTree import ElementTree, parse
except ImportError:
    from xml.etree.ElementTree import ElementTree, parse

from coord import Coord
from etree import tag


class Turnpoint(object):

    def __init__(self, name, coord):
        self.name = name
        self.coord = coord

    def build_tree(self, tb):
        attrs = {'lat': str(self.coord.lat), 'lon': str(self.coord.lon)}
        with tag(tb, 'rtept', attrs):
            if self.coord.ele:
                with tag(tb, 'ele'):
                    tb.data('%d' % ele)
            with tag(tb, 'name'):
                tb.data(self.name)
            with tag(tb, 'time'):
                tb.data(self.coord.dt.strftime('%Y-%m-%dT%H:%M:%SZ'))
        return tb

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


class Route(object):

    def __init__(self, name, league, distance, multiplier, score, circuit, tps):
        self.name = name
        self.league = league
        self.distance = distance
        self.multiplier = multiplier
        self.score = score
        self.circuit = circuit
        self.tps = tps

    def build_tree(self, tb):
        with tag(tb, 'rte'):
            with tag(tb, 'name'):
                tb.data(self.name)
            with tag(tb, 'extensions'):
                with tag(tb, 'league'):
                    tb.data(self.league)
                with tag(tb, 'distance'):
                    tb.data(str(self.distance))
                with tag(tb, 'multiplier'):
                    tb.data('%.2f' % self.multiplier)
                with tag(tb, 'score'):
                    tb.data(str(self.score))
                if self.circuit:
                    with tag(tb, 'circuit'):
                        pass
            for tp in self.tps:
                tp.build_tree(tb)
        return tb

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

    def build_tree(self, tb):
        for route in self.routes:
            route.build_tree(tb)
        return tb

    @classmethod
    def from_element(cls, element):
        routes = map(Route.from_element, element.findall('/rte'))
        return cls(routes)

    @classmethod
    def from_file(cls, file):
        element = parse(file)
        return cls.from_element(element)
