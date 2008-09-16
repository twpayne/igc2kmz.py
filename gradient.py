def hsl_to_rgba(hsl, a=1.0):
  """Convert a HSL tuple into a RGB tuple."""
  def h_to_value(p, q, t):
    if t < 0.0:
      t += 1.0
    elif 1.0 < t:
      t -= 1.0
    if t < 1.0 / 6.0:
      return p + 6.0 * (q - p) * t
    elif t < 0.5:
      return q
    elif t < 2.0 / 3.0:
      return p + 6.0 * (q - p) * (2.0 / 3.0 - t)
    else:
      return p
  h, s, l = hsl
  if s == 0:
    return (l, l, l, a)
  if l < 0.5:
    q = l * (s + 1.0)
  else:
    q = l + s - l * s
  p = 2.0 * l - q
  r = h_to_value(p, q, h + 1.0 / 3.0)
  g = h_to_value(p, q, h)
  b = h_to_value(p, q, h - 1.0 / 3.0)
  return (r, g, b, a)


def hsv_to_rgb(hsv):
  """Convert a HSV tuple into a ABGR tuple."""
  h, s, v = hsv
  hi = int(h)
  f = h - hi
  p = v * (1.0 - f)
  q = v * (1.0 - f * s)
  t = v * (1.0 - (1.0 - f) * s)
  if hi == 0:
    return (v, t, p)
  elif hi == 1:
    return (q, v, p)
  elif hi == 2:
    return (p, v, t)
  elif hi == 3:
    return (p, q, v)
  elif hi == 4:
    return (t, p, v)
  else:
    return (v, p, q)


def grayscale(value):
  """Return a gradient from black to white."""
  if value < 0.0:
    return (1.0, 0.0, 0.0, 0.0)
  elif 1.0 <= value:
    return (1.0, 1.0, 1.0, 1.0)
  else:
    return (1.0, value, value, value)


def default(value):
  """Return a gradient from blue to green to red."""
  if value < 0.0:
    return hsl_to_rgba((2.0 / 3.0, 1.0, 0.5))
  elif 1.0 <= value:
    return hsl_to_rgba((0.0, 1.0, 0.5))
  else:
    h = 2.0 * (1.0 - value) / 3.0
    return hsl_to_rgba((h, 1.0, 0.5))


def bilinear(value):
  """Return a bilinear gradient from blue to green to red."""
  if value < 0.0:
    h = 2.0 / 3.0
  elif value < 0.5:
    h = (6.0 - 4.0 * value) / 9.0
  elif value == 0.5:
    h = 1.0 / 3.0
  elif value < 1.0:
    h = (4.0 - 4.0 * value) / 9.0
  else:
    h = 0.0
  return hsl_to_rgba((h, 1.0, 0.5))
