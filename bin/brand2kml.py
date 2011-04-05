#!/usr/bin/env python
#
#   igc2kmz brand generator
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

import optparse
import os.path
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import igc2kmz.kml as kml


DEFAULT_NAME = 'Leonardo'
DEFAULT_ICON = 'http://www.paraglidingforum.com/modules/leonardo/templates/basic/tpl/leonardo_logo.gif'
DEFAULT_URL = 'http://www.paraglidingforum.com/modules.php?name=leonardo&op=list_flights'


def main(argv):
    parser = optparse.OptionParser(usage='Usage; %prog [options]')
    parser.add_option('-o', '--output', metavar='FILENAME')
    parser.add_option('-n', '--name', metavar='STRING')
    parser.add_option('-i', '--icon', metavar='STRING')
    parser.add_option('-u', '--url', metavar='STRING')
    parser.set_defaults(name=DEFAULT_NAME)
    parser.set_defaults(icon=DEFAULT_ICON)
    parser.set_defaults(url=DEFAULT_URL)
    options, args = parser.parse_args(argv)
    icon = kml.Icon(href=options.icon)
    overlay_xy = kml.overlayXY(x=0.5, y=1, xunits='fraction', yunits='fraction')
    screen_xy = kml.screenXY(x=0.5, y=1, xunits='fraction', yunits='fraction')
    size = kml.size(x=0, y=0, xunits='fraction', yunits='fraction')
    d = {'name': options.name, 'icon': options.icon, 'url': options.url}
    ps = []
    ps.append('<a href="%(url)s"><img alt="%(name)s" src="%(icon)s" /></a>' % d)
    ps.append('<a href="%(url)s">%(name)s</a>' % d)
    ps.append('Created by <a href="http://github.com/twpayne/igc2kmz/wikis">'
              'igc2kmz</a><br/>Copyright &copy; Tom Payne, 2008')
    html = '<center>%s</center' % ''.join('<p>%s</p>' % p for p in ps)
    description = kml.CDATA(html)
    snippet = kml.Snippet()
    balloon_style = kml.BalloonStyle(text=kml.CDATA('$[description]'))
    style = kml.Style(balloon_style)
    screen_overlay = kml.ScreenOverlay(icon, overlay_xy, screen_xy, size,
            snippet, style, name=options.name, description=description)
    output = open(options.output, 'w') if options.output else sys.stdout
    screen_overlay.pretty_write(output)


if __name__ == '__main__':
    main(sys.argv)
