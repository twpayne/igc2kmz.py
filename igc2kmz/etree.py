#   igc2kmz ElementTree functions
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


class tag(object):

    def __init__(self, tb, name, attrs={}):
        self.tb = tb
        self.name = name
        self.attrs = attrs

    def __enter__(self):
        self.tb.start(self.name, self.attrs)
        return self.tb

    def __exit__(self, type, value, traceback):
        self.tb.end(self.name)
