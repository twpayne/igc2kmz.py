import __builtin__
import math


def runs(seq):
  generator = enumerate(seq)
  try:
    start, current = generator.next()
  except StopIteration:
    return
  for index, element in generator:
    if element != current:
      yield (start, index)
      start, current = index, element
  yield (start, index + 1)


def douglas_peucker(x, y, epsilon, left=0, right=None):
  """
  Implement the Douglas-Peucker line simplification algorithm.
  TODO: implement http://www.cs.ubc.ca/cgi-bin/tr/1992/TR-92-07.ps
  """
  if right is None:
    right = len(x) - 1
  indexes = set([left])
  stack = [(left, right)]
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
    max_dist /= math.sqrt((x[right] - x[left]) ** 2 + (y[right] - y[left]) ** 2)
    if max_dist > epsilon:
      indexes.add(pivot)
      stack.append((left, pivot))
      stack.append((pivot, right))
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
    if direction < 0:
      right = middle - 1
    elif direction == 0:
      right = middle
    else:
      left = middle + 1
  if left == len(seq):
    return None
  else:
    return left


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
