class Bounds:

  def __init__(self, min, max=None):
    self.min = min
    self.max = max or min

  def merge(self, value):
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


class BoundsSet:

  def merge(self, other):
    for key, value in other.__dict__.items():
      if hasattr(self, key):
        getattr(self, key).merge(value)
      else:
        setattr(self, key, Bounds(value.min, value.max))
