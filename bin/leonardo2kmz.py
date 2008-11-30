#!/usr/bin/env python2.5
#   igc2kmz Leonardo integration
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


import optparse
import os.path
import sys
from urlparse import urljoin

from sqlalchemy import create_engine, MetaData, Table

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from igc2kmz import flights2kmz, Flight
from igc2kmz.igc import IGC
import igc2kmz.kml as kml
from igc2kmz.photo import Photo


def main(argv):
    parser = optparse.OptionParser(
            usage='Usage: %prog [options] flightID',
            description='IGC to Google Earth converter')
    parser.add_option('-o', '--output', metavar='FILENAME',
                      help='set output filename')
    parser.add_option('-n', '--name', metavar='STRING')
    parser.add_option('-i', '--icon', metavar='URL')
    parser.add_option('-u', '--url', metavar='URL', help='set URL')
    parser.add_option('-d', '--directory', metavar='PATH', help='set directory')
    parser.add_option('-e', '--engine', metavar='URL', help='set engine')
    parser.add_option('--debug', action='store_true',
                      help='enable pretty KML output')
    parser.set_defaults(output='igc2kmz.kmz')
    parser.set_defaults(name='Leonardo')
    parser.set_defaults(icon='http://www.paraglidingforum.com/modules/leonardo/templates/basic/tpl/leonardo_logo.gif')
    parser.set_defaults(url='http://localhost/phpbb2-leonardo/')
    parser.set_defaults(directory='/home/twp/src/phpbb2-leonardo')
    parser.set_defaults(engine='mysql://phpbb2:VDuURtNK02Nb@localhost/phpbb2')
    parser.set_defaults(debug=False)
    options, args = parser.parse_args(argv)
    #
    leonardo_dir = os.path.join(options.directory, 'modules', 'leonardo')
    flights_dir = os.path.join(leonardo_dir, 'flights')
    leonardo_url = urljoin(options.url, 'modules.php?name=leonardo')
    #
    icon = kml.Icon(href=options.icon)
    overlay_xy = kml.overlayXY(x=0.5, y=1, xunits='fraction', yunits='fraction')
    screen_xy = kml.screenXY(x=0.5, y=1, xunits='fraction', yunits='fraction')
    size = kml.size(x=0, y=0, xunits='fraction', yunits='fraction')
    d = {'name': options.name, 'icon': options.icon, 'url': leonardo_url}
    ps = []
    ps.append('<a href="%(url)s"><img alt="%(name)s" src="%(icon)s" /></a>' % d)
    ps.append('<a href="%(url)s">%(name)s</a>' % d)
    ps.append('Created by <a href="http://github.com/twpayne/igc2kmz/wikis">'
              'igc2kmz</a><br/>Copyright &copy; Tom Payne, 2008')
    html = '<center>%s</center' % ''.join('<p>%s</p>' % p for p in ps)
    description = kml.CDATA(html)
    balloon_style = kml.BalloonStyle(text=kml.CDATA('$[description]'))
    style = kml.Style(balloon_style)
    screen_overlay = kml.ScreenOverlay(icon, overlay_xy, screen_xy, size,
            style, Snippet=None, name=options.name, description=description)
    #
    engine = create_engine(options.engine)
    metadata = MetaData(bind=engine)
    pilots_table = Table('leonardo_pilots', metadata, autoload=True)
    flights_table = Table('leonardo_flights', metadata, autoload=True)
    flights_score_table = Table('leonardo_flights_score', metadata,
                                autoload=True)
    photos_table = Table('leonardo_photos', metadata, autoload=True)
    flights = []
    for flightID in args[1:]:
        flight_row = flights_table.select(flights_table.c.ID == int(flightID)).execute().fetchone()
        if flight_row is None:
            raise KeyError, id
        igc_path = os.path.join(*map(str, (flights_dir, flight_row.userID, 'flights', flight_row.DATE.year, flight_row.filename)))
        track = IGC(open(igc_path)).track()
        flight = Flight(track)
        flight.glider_type = flight_row.glider
        flight.url = urljoin(options.url, 'modules.php?name=leonardo&op=show_flight&flightID=%d' % flight_row.ID)
        pilot_row = pilots_table.select(pilots_table.c.pilotID == flight_row.userID).execute().fetchone()
        if pilot_row is None:
            raise KeyError, flight_row.userID
        flight.pilot_name = '%(FirstName)s %(LastName)s' % pilot_row
        if flight_row.hasPhotos:
            for photo_row in photos_table.select(photos_table.c.flightID == flight_row.ID).execute().fetchall():
                photo_url = urljoin(options.url, 'modules/leonardo/flights/%s/%s' % (photo_row.path, photo_row.name))
                photo_path = os.path.join(flights_dir, photo_row.path, photo_row.name)
                photo = Photo(photo_url, path=photo_path)
                if photo_row.description:
                    photo.description = photo_row.description
                flight.photos.append(photo)
        flights.append(flight)
    kmz = flights2kmz(flights, roots=[screen_overlay])
    kmz.write(options.output, '2.2', debug=options.debug)

if __name__ == '__main__':
    main(sys.argv)
