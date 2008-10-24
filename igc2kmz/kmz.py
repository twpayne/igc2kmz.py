#   igc2kmz/kmz.py  igc2kmz KMZ functions
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
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import zipfile

import kml


class kmz(object):

    def __init__(self, *elements):
        self.elements = list(elements)
        self.roots = []
        self.files = {}

    def add_roots(self, *roots):
        self.roots.extend(roots)
        return self

    def add_files(self, files):
        self.files.update(files)
        return self

    def add(self, *args):
        for arg in args:
            if isinstance(arg, kmz):
                self.elements[0].add(*arg.elements)
                self.add_roots(*arg.roots)
                self.add_files(arg.files)
            else:
                self.elements[0].add(arg)
        return self

    def add_siblings(self, *args, **kwargs):
        for arg in args:
            if isinstance(arg, kmz):
                self.elements.extend(arg.elements)
                self.add_roots(*arg.roots)
                self.add_files(arg.files)
            else:
                self.elements.append(arg)
        for key, value in kwargs.items():
            self.elements.append(kml.__dict__[key](value))
        return self

    def write(self, filename, version, debug=False):
        date_time = datetime.datetime.now().timetuple()[:6]
        zf = zipfile.ZipFile(filename, 'w')
        document = kml.Document()
        document.add(*self.roots)
        document.add(*self.elements)
        string_io = StringIO()
        if debug:
            kml.kml(version, document).pretty_write(string_io)
        else:
            kml.kml(version, document).write(string_io)
        zi = zipfile.ZipInfo('doc.kml')
        zi.compress_type = zipfile.ZIP_DEFLATED
        zi.date_time = date_time
        zi.external_attr = 0644 << 16
        zf.writestr(zi, string_io.getvalue())
        string_io.close()
        for key, value in self.files.items():
            zi = zipfile.ZipInfo(key)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.date_time = date_time
            zi.external_attr = 0644 << 16
            zf.writestr(zi, value)
        zf.close()
