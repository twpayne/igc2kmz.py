#!/usr/bin/python
#
#   test/test_util.py  igc2kmz utility unit tests
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


import os.path
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from igc2kmz.util import find_first_ge, salient, runs_where


class TestFindFirstGE(unittest.TestCase):

  def test_empty(self):
    self.assertEqual(find_first_ge([], 0), None)

  def test_minus1(self):
    self.assertEqual(find_first_ge([0, 2, 4, 6, 8], -1), 0)

  def test_0(self):
    self.assertEqual(find_first_ge([0, 2, 4, 6, 8], 0), 0)

  def test_1(self):
    self.assertEqual(find_first_ge([0, 2, 4, 6, 8], 1), 1)

  def test_2(self):
    self.assertEqual(find_first_ge([0, 2, 4, 6, 8], 2), 1)

  def test_3(self):
    self.assertEqual(find_first_ge([0, 2, 4, 6, 8], 3), 2)

  def test_4(self):
    self.assertEqual(find_first_ge([0, 2, 4, 6, 8], 4), 2)

  def test_5(self):
    self.assertEqual(find_first_ge([0, 2, 4, 6, 8], 5), 3)

  def test_6(self):
    self.assertEqual(find_first_ge([0, 2, 4, 6, 8], 6), 3)

  def test_7(self):
    self.assertEqual(find_first_ge([0, 2, 4, 6, 8], 7), 4)

  def test_8(self):
    self.assertEqual(find_first_ge([0, 2, 4, 6, 8], 8), 4)

  def test_9(self):
    self.assertEqual(find_first_ge([0, 2, 4, 6, 8], 9), None)


class TestSalient(unittest.TestCase):

  def test_empty(self):
    self.assertEqual(salient([]), [])

  def test_one(self):
    self.assertEqual(salient([0]), [0])

  def test_2up(self):
    self.assertEqual(salient([0, 1]), [0, 1])

  def test_2down(self):
    self.assertEqual(salient([1, 0]), [0, 1])

  def test_2flat(self):
    self.assertEqual(salient([0, 0]), [0, 1])

  def test_3up(self):
    self.assertEqual(salient([0, 1, 2]), [0, 2])

  def test_3down(self):
    self.assertEqual(salient([2, 1, 0]), [0, 2])

  def test_3flat(self):
    self.assertEqual(salient([0, 0, 0]), [0, 2])

  def test_3n(self):
    self.assertEqual(salient([0, 1, 0]), [0, 1, 2])

  def test_3u(self):
    self.assertEqual(salient([1, 0, 1]), [0, 1, 2])

  def test_3n_epsilon(self):
    self.assertEqual(salient([0, 1, 0], 2), [0, 2])

  def test_3u_epsilon(self):
    self.assertEqual(salient([1, 0, 1], 2), [0, 2])

  def test_4up(self):
    self.assertEqual(salient([0, 1, 2, 3]), [0, 3])

  def test_4down(self):
    self.assertEqual(salient([3, 2, 1, 0]), [0, 3])

  def test_4flat(self):
    self.assertEqual(salient([0, 0, 0, 0]), [0, 3])

  def test_nhump(self):
    self.assertEqual(salient([0, 1, 1, 0]), [0, 1, 3])

  def test_uhump(self):
    self.assertEqual(salient([1, 0, 0, 1]), [0, 1, 3])

  def test_notch(self):
    self.assertEqual(salient([0,1,2,3,3,5,6,7]), [0, 7])

  def test_complex1(self):
    self.assertEqual(salient([0,2,4,6,8,7,6,7,9,7]), [0, 4, 6, 8, 9])

  def test_complex2(self):
    self.assertEqual(salient([0,2,4,6,8,7,6,7,8,7], 2), [0, 4, 6, 9])

  def test_complex3(self):
    self.assertEqual(salient([0,2,4,6,8,7,6,7,8,7], 3), [0, 9])


class TestRunsWhere(unittest.TestCase):

  def test_1(self):
    self.assertEqual(list(runs_where([])), [])

  def test_2(self):
    self.assertEqual(list(runs_where([True])), [slice(0, 1)])

  def test_3(self):
    self.assertEqual(list(runs_where([False])), [])

  def test_4(self):
    self.assertEqual(list(runs_where([True, False])), [slice(0, 1)])

  def test_5(self):
    self.assertEqual(list(runs_where([False, True])), [slice(1, 2)])


if __name__ == '__main__':
  unittest.main()
