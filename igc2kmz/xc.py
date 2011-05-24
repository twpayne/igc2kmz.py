#   igc2kmz cross country functions
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

from datetime import datetime
import re
try:
    from xml.etree.cElementTree import ElementTree, parse
except ImportError:
    from xml.etree.ElementTree import ElementTree, parse

from coord import Coord
from etree import tag
from gpx import GPX_DATETIME_FORMAT


class Turnpoint(object):

    def __init__(self, name, coord):
        self.name = name
        self.coord = coord

    def build_tree(self, tb):
        attrs = {'lat': str(self.coord.lat), 'lon': str(self.coord.lon)}
        with tag(tb, 'rtept', attrs):
            if self.coord.ele:
                with tag(tb, 'ele'):
                    tb.data('%d' % self.coord.ele)
            with tag(tb, 'name'):
                tb.data(self.name)
            if self.coord.dt:
                with tag(tb, 'time'):
                    tb.data(self.coord.dt.strftime(GPX_DATETIME_FORMAT))
        return tb

    @classmethod
    def from_element(cls, rtept, namespace):
        name = rtept.findtext('{%s}name' % namespace).encode('utf_8')
        lat = float(rtept.get('lat'))
        lon = float(rtept.get('lon'))
        ele_tag = rtept.find('{%s}ele' % namespace)
        ele = 0 if ele_tag is None else int(ele_tag.text)
        time_text = rtept.findtext('{%s}time' % namespace)
        dt = datetime.strptime(time_text, GPX_DATETIME_FORMAT)
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
    def from_element(cls, rte, namespace):
        name = rte.findtext('{%s}name' % namespace).encode('utf_8')
        extensions_tag = rte.find('{%s}extensions' % namespace)
        league_text = extensions_tag.findtext('{%s}league' % namespace)
        league = league_text.encode('utf_8')
        distance_text = extensions_tag.findtext('{%s}distance' % namespace)
        distance = float(distance_text)
        multiplier_text = extensions_tag.findtext('{%s}multiplier' % namespace)
        multiplier = float(multiplier_text)
        score = float(extensions_tag.findtext('{%s}score' % namespace))
        circuit_tag = extensions_tag.find('{%s}circuit' % namespace)
        circuit = not circuit_tag is None
        rtepts = rte.findall('{%s}rtept' % namespace)
        tps = [Turnpoint.from_element(rtept, namespace) for rtept in rtepts]
        return cls(name, league, distance, multiplier, score, circuit, tps)


class XC(object):

    def __init__(self, routes):
        self.routes = routes

    def build_tree(self, tb):
        for route in self.routes:
            route.build_tree(tb)
        return tb

    @classmethod
    def from_element(cls, element, namespace):
        rtes = element.findall('/{%s}rte' % namespace)
        routes = [Route.from_element(rte, namespace) for rte in rtes]
        return cls(routes)

    @classmethod
    def from_file(cls, file):
        element = parse(file)
        namespace = re.match(r'\{(.*)\}', element.getroot().tag).group(1)
        return cls.from_element(element, namespace)
