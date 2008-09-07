class Scale(object):
  "A linear scale."

  def __init__(self, title, range, gradient):
    self.title = title
    self.range = map(float, range)
    self.gradient = gradient

  def normalize(self, value):
    "Normalize value."
    if value < self.range[0]:
      return 0.0
    elif self.range[1] <= value:
      return 1.0
    else:
      return (value - self.range[0]) / (self.range[1] - self.range[0])

  def discretize(self, value, n=32):
    "Discretize value."
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
    "Return the color for value."
    return self.gradient(self.normalize(value))

  def colors(self, n=32):
    "Return the colors."
    return [self.gradient(float(i) / (n - 1)) for i in range(0, n)]


class ZeroCenteredScale(Scale):
  "A bilinear scale centered on zero."

  def normalize(self, value):
    "Normalize value."
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
