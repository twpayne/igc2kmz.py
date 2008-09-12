import math

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
