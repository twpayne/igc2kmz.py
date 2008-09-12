def rgb_to_kml(rgb):
  return 'ff%02x%02x%02x' % (255 * rgb[2], 255 * rgb[1], 255 * rgb[0])

def _h_to_value(p, q, t):
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


def hsl_to_rgb(hsl):
  "Convert a HSL tuple into a RGB tuple."
  h, s, l = hsl
  if s == 0:
    return (l, l, l)
  if l < 0.5:
    q = l * (s + 1.0)
  else:
    q = l + s - l * s
  p = 2.0 * l - q
  r = _h_to_value(p, q, h + 1.0 / 3.0)
  g = _h_to_value(p, q, h)
  b = _h_to_value(p, q, h - 1.0 / 3.0)
  return (r, g, b)


def hsv_to_rgb(hsv):
  "Convert a HSV tuple into a ABGR tuple."
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
  "Return a gradient from black to white."
  if value < 0.0:
    return 'ff000000'
  elif 1.0 <= value:
    return 'ffffffff'
  else:
    return 'ff%02x%02x%02x' % (255 * value, 255 * value, 255 * value)


def default(value):
  "Return a gradient from blue to green to red."
  if value < 0.0:
    return rgb_to_kml(hsl_to_rgb((2.0 / 3.0, 1.0, 0.5)))
  elif 1.0 <= value:
    return rgb_to_kml(hsl_to_rgb((0.0, 1.0, 0.5)))
  else:
    h = 2.0 * (1.0 - value) / 3.0
    return rgb_to_kml(hsl_to_rgb((h, 1.0, 0.5)))
