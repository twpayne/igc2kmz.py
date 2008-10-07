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

import coord


class RtePt(object):

  def __init__(self, etree):
    self.dt = datetime.datetime.strptime(etree.findtext('time'), '%Y-%m-%dT%H:%M:%SZ')
    self.fix = etree.findtext('fix')
    self.name = etree.findtext('name')
    lat = float(etree.get('lat'))
    lon = float(etree.get('lon'))
    ele = int(etree.findtext('ele')) if self.fix == '3d' else 0
    self.coord = coord.Coord.deg(lat, lon, ele, dt)


class Rte(object):

  def __init__(self, etree):
    self.name = etree.findtext('name')
    self.distance = float(etree.findtext('extensions/distance'))
    self.multiplier = float(etree.findtext('extensions/multiplier'))
    self.score = float(etree.findtext('extensions/score'))
    self.rtepts = [RtePt(rtept) for rtept in etree.findall('rtept')]


class XC(object):

  def __init__(self, etree):
    self.league = etree.findtext('/metadata/extensions/league')
    self.rtes = [Rte(rte) for rte in etree.findall('/rte')]


def parse(file):
  return XC(xml.etree.ElementTree.parse(file))
