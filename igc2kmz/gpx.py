#   igc2kmz.py  igc2kmz GPX module
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


from datetime import datetime
import math
import re
try:
    from xml.etree.cElementTree import parse
except ImportError:
    from xml.etree.ElementTree import parse

from coord import Coord
from track import Track
from waypoint import Waypoint


GPX_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


class gpx_tag(object):

    def __init__(self, tb):
        self.tb = tb

    def __enter__(self):
        attrs = {
            'creator': 'http://github.com/twpayne/igc2kmz/wikis',
            'version': '1.1',
            'xmlns': 'http://www.topografix.com/GPX/1/1',
            'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'xsi:schemaLocation': 'http://www.topografix.com/GPX/1/1 '
                                  'http://www.topografix.com/GPX/1/1/gpx.xsd'}
        self.tb.start('gpx', attrs)
        return self.tb

    def __exit__(self, type, value, traceback):
        self.tb.end('gpx')


class GPX(object):

    def __init__(self, file):
        try:
            self.filename = file.name
        except AttributeError:
            self.filename = '(unknown)'
        element = parse(file)
        namespace = re.match('\{(.*)\}', element.getroot().tag).group(1)
        ele_tag_name = '{%s}ele' % namespace
        name_tag_name = '{%s}name' % namespace
        time_tag_name = '{%s}time' % namespace
        self.coords = []
        for trkpt in element.findall('/{%s}trk/{%s}trkseg/{%s}trkpt'
                                     % (namespace, namespace, namespace)):
            lat = math.pi * float(trkpt.get('lat')) / 180.0
            lon = math.pi * float(trkpt.get('lon')) / 180.0
            ele_tag = trkpt.find(ele_tag_name)
            ele = 0 if ele_tag is None else float(ele_tag.text)
            time = trkpt.find(time_tag_name)
            if time is None:
                continue
            dt = datetime.strptime(time.text, GPX_DATETIME_FORMAT)
            coord = Coord(lat, lon, ele, dt)
            self.coords.append(coord)
        self.waypoints = []
        for wpt in element.findall('/{%s}wpt' % namespace):
            name = wpt.find(name_tag_name).text
            lat = math.pi * float(wpt.get('lat')) / 180.0
            lon = math.pi * float(wpt.get('lon')) / 180.0
            ele_tag = wpt.find(ele_tag_name)
            ele = 0 if ele_tag is None else float(ele_tag.text)
            waypoint = Waypoint(name, lat, lon, ele)
            self.waypoints.append(waypoint)

    def track(self):
        return Track(self.coords, filename=self.filename)
