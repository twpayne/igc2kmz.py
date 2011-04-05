#!/usr/bin/env python
#   igc2kmz IGC to Google Earth converter (Leonardo integration)
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
import optparse
import os.path
from math import sqrt
import re
import sys

from sqlalchemy import create_engine, MetaData, Table

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from igc2kmz import Flight, flights2kmz, make_table
from igc2kmz.igc import IGC
import igc2kmz.kml as kml
from igc2kmz.photo import Photo
from igc2kmz.xc import Coord, Route, Turnpoint, XC


DEFAULT_NAME = 'Leonardo'
DEFAULT_URL = 'http://www.paraglidingforum.com'
DEFAULT_ICON = '/modules/leonardo/templates/basic/tpl/leonardo_logo.gif'
DEFAULT_DIRECTORY = '/var/www/html'
DEFAULT_TABLE_PREFIX = 'leonardo'
DEFAULT_IGC_PATH = 'data/flights/tracks/%YEAR%/%PILOTID%'
DEFAULT_PHOTOS_PATH = 'data/flights/photos/%YEAR%/%PILOTID%'
DEFAULT_PHOTOS_URL = '/modules/leonardo/data/flights/photos/%YEAR%/%PILOTID%'

LEAGUE = (None, 'Online Contest', 'World XC Online Contest')
ROUTE_NAME = (
        None,
        'free flight',
        'free triangle',
        'FAI triangle',
        'free flight without turnpoints',
        'maximum distance from take-off')
CIRCUIT = (None, False, True, True, False, False)

SHOW_FLIGHT_URL = '/modules.php?name=leonardo&op=show_flight&flightID=%(ID)d'
PHOTO_URL = '/modules/leonardo/flights/%(path)s/%(name)s'

B_RECORD_RE = re.compile(r'B(\d{2})(\d{2})(\d{2})'
                         r'(\d{2})(\d{5})([NS])(\d{3})(\d{5})([EW])')


def substitute(s, dict):
    for key, value in dict.items():
        s = re.sub('%%%s%%' % re.escape(key), value, s)
    return s


def make_banner(options):
    leonardo_url = options.url + '/modules.php?name=leonardo'
    icon_url = options.url + options.icon
    icon = kml.Icon(href=icon_url)
    overlay_xy = kml.overlayXY(x=0.5, y=1, xunits='fraction', yunits='fraction')
    screen_xy = kml.screenXY(x=0.5, y=1, xunits='fraction', yunits='fraction')
    size = kml.size(x=0, y=0, xunits='fraction', yunits='fraction')
    d = {'name': options.name, 'icon': icon_url, 'url': leonardo_url}
    ps = []
    ps.append('<a href="%(url)s"><img alt="%(name)s" src="%(icon)s" /></a>' % d)
    ps.append('<a href="%(url)s">%(name)s</a>' % d)
    ps.append('Created by <a href="http://github.com/twpayne/igc2kmz/wikis">'
              'igc2kmz</a><br/>Copyright &copy; Tom Payne, 2008')
    html = '<center>%s</center>' % ''.join('<p>%s</p>' % p for p in ps)
    description = kml.CDATA(html)
    balloon_style = kml.BalloonStyle(text=kml.CDATA('$[description]'))
    style = kml.Style(balloon_style)
    return kml.ScreenOverlay(icon, overlay_xy, screen_xy, size, style,
                             Snippet=None, name=options.name,
                             description=description)


def make_takeoff_placemark(takeoff_row):
    coord = Coord.deg(takeoff_row.lat, -takeoff_row.lon, 0)
    point = kml.Point(coordinates=[coord])
    icon_style = kml.IconStyle(kml.Icon.palette(3, 40), scale=sqrt(0.6))
    label_style = kml.LabelStyle(scale=sqrt(0.6))
    style = kml.Style(icon_style, label_style)
    rows = []
    if takeoff_row.name:
        rows.append(('Name', takeoff_row.name))
    if takeoff_row.intName:
        if takeoff_row.intName != takeoff_row.name:
            rows.append(('Name in English', takeoff_row.intName))
    if takeoff_row.location:
        rows.append(('Location', takeoff_row.location))
    if takeoff_row.intLocation:
        if takeoff_row.intLocation != takeoff_row.location:
            rows.append(('Location in English', takeoff_row.intLocation))
    if takeoff_row.countryCode:
        rows.append(('Country', takeoff_row.countryCode))
    if takeoff_row.description:
        rows.append(('Description', takeoff_row.description))
    if takeoff_row.link:
        rows.append(('URL', '<a href="%(link)s">%(link)s</a>' % takeoff_row))
    if takeoff_row.modifyDate:
        rows.append(('Last modified', takeoff_row.modifyDate))
    description = kml.CDATA(make_table(rows))
    return kml.Placemark(point, style, Snippet=None, name=takeoff_row.name,
                         description=description)


def main(argv):
    parser = optparse.OptionParser(
            usage='Usage: %prog [options] flightID',
            description='IGC to Google Earth converter (Leonardo integration)')
    parser.add_option('-o', '--output', metavar='FILENAME',
                      help='set output filename')
    parser.add_option('-n', '--name', metavar='STRING')
    parser.add_option('-i', '--icon', metavar='URL')
    parser.add_option('-u', '--url', metavar='URL', help='set URL')
    parser.add_option('-d', '--directory', metavar='PATH', help='set directory')
    parser.add_option('-e', '--engine', metavar='URL', help='set engine')
    parser.add_option('-z', '--tz-offset', metavar='HOURS', type='int',
                      help='set timezone offset')
    parser.add_option('-t', '--table-prefix', metavar='STRING',
                      help='set table prefix')
    parser.add_option('-x', '--igc-suffix', metavar='STRING',
                      help='set IGC file suffix')
    parser.add_option('-I', '--igc-path', metavar='STRING',
                      help='set IGC path')
    parser.add_option('-P', '--photos-path', metavar='STRING',
                      help='set photos path')
    parser.add_option('-U', '--photos-url', metavar='STRING',
                      help='set photos URL')
    parser.set_defaults(output='igc2kmz.kmz')
    parser.set_defaults(name=DEFAULT_NAME)
    parser.set_defaults(icon=DEFAULT_ICON)
    parser.set_defaults(url=DEFAULT_URL)
    parser.set_defaults(directory=DEFAULT_DIRECTORY)
    parser.set_defaults(tz_offset=0)
    parser.set_defaults(table_prefix=DEFAULT_TABLE_PREFIX)
    parser.set_defaults(igc_path=DEFAULT_IGC_PATH)
    parser.set_defaults(photos_path=DEFAULT_PHOTOS_PATH)
    parser.set_defaults(photos_url=DEFAULT_PHOTOS_URL)
    parser.set_defaults(igc_suffix='.saned.full.igc')
    options, args = parser.parse_args(argv)
    #
    flights_dir = os.path.join(options.directory,
                               'modules', 'leonardo', 'flights')
    #
    roots = []
    roots.append(make_banner(options))
    #
    metadata = MetaData(options.engine)
    pilots_table = Table(options.table_prefix + '_pilots', metadata,
                         autoload=True)
    flights_table = Table(options.table_prefix + '_flights', metadata,
                          autoload=True)
    flights_score_table = Table(options.table_prefix + '_flights_score',
                                metadata, autoload=True)
    photos_table = Table(options.table_prefix + '_photos', metadata,
                         autoload=True)
    waypoints_table = Table(options.table_prefix + '_waypoints', metadata,
                            autoload=True)
    #
    flights = []
    for flightID in args[1:]:
        select = flights_table.select(flights_table.c.ID == int(flightID))
        flight_row = select.execute().fetchone()
        if flight_row is None:
            raise KeyError, id
        if flight_row.userServerID:
            pilot_id = '%(userServerID)d_%(userID)d' % flight_row
        else:
            pilot_id = flight_row.userID
        substitutions = {
                'PILOTID': str(pilot_id),
                'YEAR': str(flight_row.DATE.year),
                }
        igc_path = os.path.join(options.directory,
                                substitute(options.igc_path, substitutions),
                                flight_row.filename + options.igc_suffix)
        track = IGC(open(igc_path), date=flight_row.DATE).track()
        flight = Flight(track)
        flight.glider_type = flight_row.glider
        flight.url = options.url + SHOW_FLIGHT_URL % flight_row
        #
        select = pilots_table.select((pilots_table.c.pilotID
                                     == flight_row.userID) &
                                     (pilots_table.c.serverID
                                     == flight_row.userServerID))
        pilot_row = select.execute().fetchone()
        if pilot_row is None:
            raise KeyError, '(%(userID)s, %(userServerID)s)' % flight_row
        flight.pilot_name = '%(FirstName)s %(LastName)s' % pilot_row
        #
        routes = []
        select = flights_score_table.select(flights_score_table.c.flightID
                                            == flight_row.ID)
        for flight_score_row in select.execute().fetchall():
            route_name = ROUTE_NAME[flight_score_row.type]
            league = LEAGUE[flight_score_row.method]
            distance = flight_score_row.distance
            score = flight_score_row.score
            multiplier = round(score / distance, 2)
            circuit = CIRCUIT[flight_score_row.type]
            tps = []
            for i in xrange(1, 8):
                m = B_RECORD_RE.match(flight_score_row['turnpoint%d' % i])
                if not m:
                    continue
                time = datetime.time(*map(int, m.group(1, 2, 3)))
                dt = datetime.datetime.combine(flight_row.DATE, time)
                lat = int(m.group(4)) + int(m.group(5)) / 60000.0
                if m.group(6) == 'S':
                    lat = -lat
                lon = int(m.group(7)) + int(m.group(8)) / 60000.0
                if m.group(9) == 'W':
                    lon = -lon
                coord = Coord.deg(lat, lon, 0, dt)
                name = 'Start' if i == 1 else 'TP%d' % (i - 1)
                tp = Turnpoint(name, coord)
                tps.append(tp)
            tps[-1].name = 'Finish'
            route = Route(route_name, league, distance, multiplier, score,
                          circuit, tps)
            routes.append(route)
        flight.xc = XC(routes)
        #
        if flight_row.hasPhotos:
            select = photos_table.select(photos_table.c.flightID
                                         == flight_row.ID)
            for photo_row in select.execute().fetchall():
                photo_url = options.url \
                        + substitute(options.photos_url, substitutions) \
                        + '/' + photo_row.name
                photo_path = os.path.join(options.directory,
                                          substitute(options.photos_path, substitutions),
                                          photo_row.name)
                photo = Photo(photo_url, path=photo_path)
                if photo_row.description:
                    photo.description = photo_row.description
                flight.photos.append(photo)
        #
        flights.append(flight)
        #
        select = waypoints_table.select(waypoints_table.c.ID
                                        == flight_row.takeoffID)
        takeoff_row = select.execute().fetchone()
        if takeoff_row:
            roots.append(make_takeoff_placemark(takeoff_row))
    #
    kmz = flights2kmz(flights, roots=roots, tz_offset=options.tz_offset)
    kmz.write(options.output, '2.2')

if __name__ == '__main__':
    main(sys.argv)
