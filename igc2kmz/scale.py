import datetime
import itertools
import time


class Scale(object):
  """A linear scale."""

  def __init__(self, range, title=None, gradient=None, step=1, max_divisions=16):
    self.range = range
    self.title = title
    self.gradient = gradient
    def steps(step=None):
      while True:
        yield step
        yield 2 * step
        yield 5 * step
        step *= 10
    if step:
      for step in steps(step):
        lower, upper = int(self.range[0] / step), int(self.range[1] / step)
        if self.range[0] < step * lower:
          lower -= 1
        if self.range[1] > step * upper:
          upper += 1
        if upper - lower <= max_divisions:
          self.grid_step = '%.1f' % (100.0 / (upper - lower))
          self.range = (step * lower, step * upper)
          self.step = step
          break

  def normalize(self, value):
    """Normalize value."""
    if value < self.range[0]:
      return 0.0
    elif self.range[1] <= value:
      return 1.0
    else:
      return float(value - self.range[0]) / (self.range[1] - self.range[0])

  def discretize(self, value, n=32):
    """Discretize value."""
    if value < self.range[0]:
      return 0
    elif value > self.range[1]:
      return n - 1
    else:
      result = int(round(n * self.normalize(value)))
      if result > n - 1:
        return n - 1
      else:
        return result

  def color(self, value):
    """Return the color for value."""
    return self.gradient(self.normalize(value))

  def colors(self, n=32):
    """Return the colors."""
    return [self.gradient(float(i) / (n - 1)) for i in xrange(0, n)]


class ZeroCenteredScale(Scale):
  """A bilinear scale centered on zero."""

  def normalize(self, value):
    """Normalize value."""
    if value < 0.0:
      if value < self.range[0]:
        return 0.0
      else:
        return 0.5 - 0.5 * value / self.range[0]
    elif value == 0.0:
      return 0.5
    else:
      if self.range[1] <= value:
        return 1.0
      else:
        return 0.5 + 0.5 * value / self.range[1]


class TimeScale(Scale):

  def __init__(self, range, title=None, gradient=None, step=1, max_divisions=16, timezone_offset=datetime.timedelta(0, 0)):
    def steps(step=None):
      steps = [1, 5, 15, 30, 60, 5 * 60, 15 * 60, 30 * 60, 3600, 3 * 3600, 6 * 3600, 12 * 3600]
      return itertools.imap(lambda seconds: datetime.timedelta(0, seconds), itertools.dropwhile(lambda s: s < step, steps))
    def floor(dt, delta):
      if delta.seconds >= 3600:
        return dt.replace(minute=0, second=0) - datetime.timedelta(0, 3600 * (dt.hour % int(delta.seconds / 3600)))
      elif delta.seconds >= 60:
        return dt.replace(second=0) - datetime.timedelta(0, 60 * (dt.minute % int(delta.seconds / 60)))
      elif delta.seconds >= 1:
        return dt - datetime.timedelta(0, dt.second % delta.seconds)
      else:
        return dt
    lower, upper = range
    if step:
      for step in steps(step):
        lower, upper = floor(range[0], step), floor(range[1], step)
        if upper < range[1]:
          upper += step
        if (upper - lower).seconds / step.seconds < max_divisions:
          range = (int(time.mktime(lower.timetuple())), int(time.mktime(upper.timetuple())))
          self.grid_step = '%.1f' % (100.0 * step.seconds / (upper - lower).seconds)
          self.step = step
          break
    Scale.__init__(self, range, title=title, gradient=gradient, step=None)
    self.labels, self.positions = [], []
    t = datetime.datetime(lower.year, lower.month, lower.day, lower.hour) + self.step
    while t < upper:
      self.labels.append((t + timezone_offset).strftime('%H:%M'))
      self.positions.append('%1.f' % (100.0 * (t - lower).seconds / (upper - lower).seconds))
      t += self.step
