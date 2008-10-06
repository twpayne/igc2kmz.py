#!/usr/bin/python
#
#   test/test_igc.py  igc2kmz IGC test functions
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


import os
import pprint
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import igc2kmz.exif


def main(argv):
  for arg in argv[1:]:
    try:
      pprint.pprint(igc2kmz.exif.JPEG(open(arg)).__dict__)
    except igc2kmz.exif.SyntaxError, line:
      print "%s: %s" % (arg, line)


if __name__ == '__main__':
  main(sys.argv)
