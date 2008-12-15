#   igc2kmz utility functions
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


import __builtin__
import datetime
import itertools
import math
import sys


class Bounds(object):

    def __init__(self, value):
        if isinstance(value, list):
            self.min = value[0]
            self.max = value[0]
            for i in xrange(1, len(value)):
                if value[i] < self.min:
                    self.min = value[i]
                elif value[i] > self.max:
                    self.max = value[i]
        elif isinstance(value, tuple):
            self.min, self.max = value
        else:
            self.min = value
            self.max = value

    def __repr__(self):
        return 'Bounds((%(min)s, %(max)s))' % self.__dict__

    def update(self, value):
        if isinstance(value, Bounds):
            if value.min < self.min:
                self.min = value.min
            if value.max > self.max:
                self.max = value.max
        else:
            if value < self.min:
                self.min = value
            if value > self.max:
                self.max = value

    def tuple(self):
        return (self.min, self.max)


class BoundsSet(object):

    def update(self, other):
        for key, value in other.__dict__.items():
            if hasattr(self, key):
                getattr(self, key).update(value)
            else:
                setattr(self, key, Bounds(value.tuple()))


class OpenStruct(object):

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __iter__(self):
        return self.__dict__.iteritems()

    def __repr__(self):
        return 'OpenStruct(%s)' % ', '.join('%s=%s' % (key, repr(value))
                                            for key, value in self)


def runs(seq):
    generator = enumerate(seq)
    try:
        start, current = generator.next()
    except StopIteration:
        return
    index = 0
    for index, element in generator:
        if element != current:
            yield slice(start, index)
            start, current = index, element
    yield slice(start, index + 1)


def runs_where(seq):
    generator = enumerate(seq)
    try:
        start, current = generator.next()
    except StopIteration:
        return
    index = 0
    for index, element in generator:
        if element != current:
            if current:
                yield slice(start, index)
            start, current = index, element
    if current:
        yield slice(start, index + 1)


def condense(seq, t, delta):
    try:
        sl = seq.next()
        start, stop = sl.start, sl.stop
    except StopIteration:
        return
    for sl in seq:
        if t[sl.start] - t[stop] < delta:
            stop = sl.stop
        else:
            yield slice(start, stop)
            start, stop = sl.start, sl.stop
    yield slice(start, stop)


def douglas_peucker(x, y, epsilon):
    """
    Implement the Douglas-Peucker line simplification algorithm.
    TODO: implement http://www.cs.ubc.ca/cgi-bin/tr/1992/TR-92-07.ps
    """
    indexes = set([0])
    stack = [(0, len(x) - 1)]
    while stack:
        left, right = stack.pop()
        indexes.add(right)
        kx, ky = y[left] - y[right], x[right] - x[left]
        c = x[left] * y[right] - x[right] * y[left]
        pivot = left + 1
        max_dist = abs(kx * x[pivot] + ky * y[pivot] + c)
        for i in xrange(left + 2, right):
            dist = abs(kx * x[i] + ky * y[i] + c)
            if dist > max_dist:
                max_dist = dist
                pivot = i
        max_dist /= math.sqrt((x[right] - x[left]) ** 2
                              + (y[right] - y[left]) ** 2)
        if max_dist > epsilon:
            indexes.add(pivot)
            stack.append((left, pivot))
            stack.append((pivot, right))
    return sorted(indexes)


def incr_douglas_peucker(x, y, epsilon, max_indexes=sys.maxint):
    indexes = set([0])
    queue = [(0, len(x) - 1)]
    i = 0
    while i < len(queue):
        left, right = queue[i]
        i += 1
        indexes.add(right)
        if len(indexes) == max_indexes:
            break
        kx, ky = y[left] - y[right], x[right] - x[left]
        c = x[left] * y[right] - x[right] * y[left]
        pivot = left + 1
        max_dist = abs(kx * x[pivot] + ky * y[pivot] + c)
        for j in xrange(left + 2, right):
            dist = abs(kx * x[j] + ky * y[j] + c)
            if dist > max_dist:
                max_dist = dist
                pivot = j
        max_dist /= math.sqrt((x[right] - x[left]) ** 2
                              + (y[right] - y[left]) ** 2)
        if max_dist > epsilon:
            indexes.add(pivot)
            if len(indexes) == max_indexes:
                break
            queue.append((left, pivot))
            queue.append((pivot, right))
    return sorted(indexes)


def bsearch(seq, value, cmp=__builtin__.cmp):
    left, right = 0, len(seq)
    while left <= right:
        middle = (left + right) / 2
        direction = cmp(value, seq[middle])
        if direction < 0:
            right = middle - 1
        elif direction == 0:
            return middle
        else:
            left = middle + 1
    return None


def find_first_ge(seq, value, cmp=__builtin__.cmp):
    left = 0
    right = len(seq)
    while left < right:
        middle = (left + right) / 2
        direction = cmp(value, seq[middle])
        if direction <= 0:
            right = middle
        else:
            left = middle + 1
    if left == len(seq):
        return None
    else:
        return right


def pairwise(iterable):
    """s -> (s0,s1), (s1,s2), (s2,s3), ..."""
    a, b = itertools.tee(iterable)
    for elem in b:
        break
    return itertools.izip(a, b)


def salient(seq, epsilon=0):
    def helper(start, stop):
        if stop - start < 2:
            return
        delta = 0
        left, right = start, stop
        if seq[start] <= seq[stop]:
            max_index = start
            for i in xrange(start + 1, stop + 1):
                if seq[i] > seq[max_index]:
                    max_index = i
                elif seq[max_index] - seq[i] > delta:
                    left, right = max_index, i
                    delta = seq[max_index] - seq[i]
        if seq[start] >= seq[stop]:
            min_index = start
            for i in xrange(start + 1, stop + 1):
                if seq[i] < seq[min_index]:
                    min_index = i
                elif seq[i] - seq[min_index] > delta:
                    left, right = min_index, i
                    delta = seq[i] - seq[min_index]
        if delta >= epsilon and (left != start or right != stop):
            result.add(left)
            result.add(right)
            helper(start, left)
            helper(left, right)
            helper(right, stop)
    result = set()
    if len(seq):
        result.add(0)
        result.add(len(seq) - 1)
        helper(0, len(seq) - 1)
    return sorted(result)


def salient2(seq, epsilons):
    def helper(start, stop):
        if stop - start < 2:
            return
        delta = 0
        left, right = start, stop
        if seq[start] <= seq[stop]:
            max_index = start
            for i in xrange(start + 1, stop + 1):
                if seq[i] > seq[max_index]:
                    max_index = i
                elif seq[max_index] - seq[i] > delta:
                    left, right = max_index, i
                    delta = seq[max_index] - seq[i]
        if seq[start] >= seq[stop]:
            min_index = start
            for i in xrange(start + 1, stop + 1):
                if seq[i] < seq[min_index]:
                    min_index = i
                elif seq[i] - seq[min_index] > delta:
                    left, right = min_index, i
                    delta = seq[i] - seq[min_index]
        if delta >= epsilons[-1] and (left != start or right != stop):
            for i, epsilon in enumerate(epsilons):
                if delta < epsilon:
                    continue
                if not left in result or result[left] > i:
                    result[left] = i
                if not right in result or result[right] > i:
                    result[right] = i
            helper(start, left)
            helper(left, right)
            helper(right, stop)
    result = {}
    if len(seq):
        result[0] = 0
        result[len(seq) - 1] = 0
        helper(0, len(seq) - 1)
    return result.items()


def datetime_floor(dt, delta):
    if delta.seconds >= 3600:
        return dt.replace(minute=0, second=0) \
               - datetime.timedelta(0, 3600 * (dt.hour
                                               % int(delta.seconds / 3600)))
    elif delta.seconds >= 60:
        return dt.replace(second=0) \
               - datetime.timedelta(0, 60 * (dt.minute
                                             % int(delta.seconds / 60)))
    elif delta.seconds >= 1:
        return dt - datetime.timedelta(0, dt.second % delta.seconds)
    else:
        return dt
