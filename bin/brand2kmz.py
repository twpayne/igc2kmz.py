#!/usr/bin/python
#
#   igc2kmz.py  igc2kmz brand generator
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

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import igc2kmz.kml as kml


def main(argv):
  parser = optparse.OptionParser(usage='Usage; %prog [options]')
  parser.add_option('-o', '--output', metavar='FILENAME')
  parser.add_option('-n', '--name', metavar='STRING')
  parser.add_option('-i', '--icon', metavar='STRING')
  parser.add_option('-u', '--url', metavar='STRING')
  parser.set_defaults(name='Leonardo')
  parser.set_defaults(url='http://www.paraglidingforum.com/')
  parser.set_defaults(icon='leonardo_logo.gif')
  options, args = parser.parse_args(argv)
  icon = kml.Icon(href=options.icon)
  overlay_xy = kml.overlayXY(x=0.5, y=1, xunits='fraction', yunits='fraction')
  screen_xy = kml.screenXY(x=0.5, y=1, xunits='fraction', yunits='fraction')
  size = kml.size(x=0, y=0, xunits='fraction', yunits='fraction')
  d = {'name': options.name, 'icon': options.icon, 'url': options.url}
  ps = []
  ps.append('<a href="%(url)s"><img alt="%(name)s" src="%(icon)s" /></a>' % d)
  ps.append('<large><a href="%(url)s">%(name)s</a></large>' % d)
  ps.append('<small>Created by <a href="http://github.com/twpayne/igc2kmz/master/tree">igc2kmz</a> Copyright &copy; Tom Payne 2008</a></small>' % d)
  description = kml.CDATA('<center>%s</center>' % ''.join('<p>%s</p>' % p for p in ps))
  screen_overlay = kml.ScreenOverlay(icon, overlay_xy, screen_xy, size, kml.Snippet(), name=options.name, description=description)
  screen_overlay.pretty_write(open(options.output, 'w') if options.output else sys.stdout)


if __name__ == '__main__':
  main(sys.argv)
