#   igc2kmz/__init__.py  igc2kmz photo module
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


import re
import urllib2
import urlparse

import exif


class Photo(object):

  def __init__(self, url):
    if urlparse.urlparse(url).scheme:
      self.url = url
    else:
      self.url = 'file://' + url
    file = urllib2.urlopen(self.url)
    if file.info().typeheader != 'image/jpeg':
      raise RuntimeError, '%s: not an image/jpeg' % self.url
    self.jpeg = exif.JPEG(file)
    value = self.jpeg.exif.get('DateTimeOriginal') or self.jpeg.exif.get('DateTime')
    self.dt = exif.parse_datetime(value) if value else None
