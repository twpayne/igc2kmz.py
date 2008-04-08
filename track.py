from cStringIO import StringIO
import math
import sys

import cairo
import numpy

import kml
import kmz
from OpenStruct import OpenStruct

def runs(list):
  if len(list) == 0:
    return
  i = 0
  for j in range(1, len(list)):
    if list[i] != list[j]:
      yield((i, j))
      i = j
  yield((i, len(list)))


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


def hsl_to_rgb(hsl):
  h, s, l = hsl
  if s == 0:
    return (l, l, l)
  q = l * (s + 1.0) if l < 0.5 else l + s - l * s
  p = 2.0 * l - q
  r = h_to_value(p, q, h + 1.0 / 3.0)
  g = h_to_value(p, q, h)
  b = h_to_value(p, q, h - 1.0 / 3.0)
  return (r, g, b)


def hsv_to_rgb(hsv):
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


def rgb_to_kml(rgb):
  return 'ff%02x%02x%02x' % (255 * rgb[2], 255 * rgb[1], 255 * rgb[0])


def grayscaleGradient(value):
  if value < 0.0:
    return (0.0, 0.0, 0.0)
  elif 1.0 <= value:
    return (1.0, 1.0, 1.0)
  else:
    return (value, value, value)


def defaultGradient(value):
  if value < 0.0:
    return hsl_to_rgb((2.0 / 3.0, 1.0, 0.5))
  elif 1.0 <= value:
    return hsl_to_rgb((0.0, 1.0, 0.5))
  else:
    h = 2.0 * (1.0 - value) / 3.0
    return hsl_to_rgb((h, 1.0, 0.5))


class Scale:

  def __init__(self, title, range, gradient):
    self.title = title
    self.range = map(float, range)
    self.gradient = gradient

  def normalize(self, value):
    if value < self.range[0]:
      return 0.0
    elif self.range[1] <= value:
      return 1.0
    else:
      return (value - self.range[0]) / (self.range[1] - self.range[0])

  def discretize(self, value, n=32):
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

  def rgb(self, value):
    return self.gradient(self.normalize(value))

  def rgbs(self, n=32):
    return [self.gradient(float(i) / (n - 1)) for i in range(0, n)]


class ZeroCenteredScale(Scale):

  def normalize(self, value):
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


class Stock:

  def make_pixel(self):
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)
    context = cairo.Context(surface)
    context.set_source_rgba(0.0, 0.0, 0.0, 0.0)
    context.rectangle(0, 0, 1, 1)
    context.fill()
    string_io = StringIO()
    surface.write_to_png(string_io)
    return string_io.getvalue()

  def make_none_folder(self, visibility):
    icon = kml.Icon(href=self.pixel_url)
    overlay_xy = kml.overlayXY(x=0, y=0, xunits='fraction', yunits='fraction')
    screen_xy = kml.screenXY(x=0, y=0, xunits='fraction', yunits='fraction')
    size = kml.size(x=0, y=0, xunits='fraction', yunits='fraction')
    screen_overlay = kml.ScreenOverlay(icon, overlay_xy, screen_xy, size, visibility=visibility)
    folder = kml.Folder(screen_overlay, name='None', styleUrl=self.check_hide_children_style.url())
    return kmz.kmz(folder)

  def __init__(self):
    self.kmz = kmz.kmz()
    self.radio_folder_style = kml.Style(kml.ListStyle(listItemType='radioFolder'))
    self.kmz.add_roots(self.radio_folder_style)
    self.check_hide_children_style = kml.Style(kml.ListStyle(listItemType='checkHideChildren'))
    self.kmz.add_roots(self.check_hide_children_style)
    self.pixel_url = 'images/pixel.png'
    self.kmz.add_files({self.pixel_url: self.make_pixel()})
    self.visible_none_folder = self.make_none_folder(1)
    self.invisible_none_folder = self.make_none_folder(0)


class Hints:

  def __init__(self):
    self.altitude_mode = 'absolute'
    self.color = 'ff0000ff'
    self.stock = Stock()
    self.width = 2


class Bounds:

  def __init__(self, value):
    self.min = self.max = value

  def update(self, value):
    if value < self.min:
      self.min = value
    if self.max < value:
      self.max = value


class Track:

  def __init__(self, meta, times, coords):
    self.meta = meta
    self.times = times
    self.coords = coords
    self.analyse()

  def analyse(self, period=20):
    half_period = period / 2.0
    self.bounds = OpenStruct()
    self.bounds.ele = Bounds(self.coords[0].ele)
    for coord in self.coords:
      self.bounds.ele.update(coord.ele)
    self.elevation_data = self.bounds.ele.min != 0 or self.bounds.ele.max != 0
    self.dz_positive = [0]
    self.s = [0]
    for i in range(1, len(self.coords)):
      dz = self.coords[i].ele - self.coords[i - 1].ele
      dz_positive = dz if dz > 0.0 else 0.0
      self.dz_positive.append(self.dz_positive[i - 1] + dz_positive)
      x = math.sin(math.pi * self.coords[i - 1].lat / 180.0) * math.sin(math.pi * self.coords[i].lat / 180.0) + math.cos(math.pi * self.coords[i - 1].lat / 180.0) * math.cos(math.pi * self.coords[i].lat) * math.cos(math.pi * (self.coords[i - 1].lon - self.coords[i].lon) / 180.0)
      ds = 6371.0 * math.acos(x) if x < 1.0 else 0.0
      self.s.append(self.s[i - 1] + ds)
    """
    n = len(self.coords)
    rlat = numpy.empty((n + 2,))
    rlon = numpy.empty((n + 2,))
    ele = numpy.empty((n + 2,))
    ds = numpy.empty((n + 2,))
    t = numpy.empty((n + 2,))
    rlat[0] = math.pi * self.coords[0].lat / 180.0
    rlon[0] = math.pi * self.coords[0].lon / 180.0
    ele[0] = self.coords[0].ele
    ds[0] = 0.0
    t[0] = -sys.maxint - 1
    for i in range(0, n):
      rlat[i + 1] = math.pi * self.coords[i].lat / 180.0
      rlon[i + 1] = math.pi * self.coords[i].lon / 180.0
      ele[i + 1] = self.coords[i].ele
      x = sin(rlat[i]) * sin(rlat[i + 1]) + cos(rlat[i]) * cos(rlat[i + 1]) * cos(rlon[i] - rlon[i - 1])
      if x < 1.0:
	ds[i + 1] = 6371000.0 * acos(x)
      else:
	ds[i + 1] = 0.0
    rlat[-1] = math.pi * self.coords[-1].lat / 180.0
    rlon[-1] = math.pi * self.coords[-1].lon / 180.0
    ele[-1] = self.coords[-1].ele
    ds[-1] = 0.0
    t[-1] = sys.maxint
    """



  def make_description(self, hints):
    rows = []
    if not self.meta.pilot_name is None:
      rows.append(('Pilot name', self.meta.pilot_name))
    if not self.meta.glider_type is None:
      rows.append(('Glider type', self.meta.glider_type))
    if not self.meta.glider_id is None:
      rows.append(('Glider ID', self.meta.glider_id))
    rows.append(('Take-off time', self.times[0].strftime('%H:%M:%S')))
    rows.append(('Landing time', self.times[-1].strftime('%H:%M:%S')))
    hour, seconds = divmod((self.times[0] - self.times[-1]).seconds, 3600)
    minute, second = divmod(seconds, 60)
    rows.append(('Duration', '%d:%02d:%02d' % (hour, minute, second)))
    print self.s[-1]
    rows.append(('Track length', '%.3fkm' % (self.s[-1] / 1000.0)))
    if self.elevation_data:
      rows.append(('Take-off altitude', '%dm' % self.coords[0].ele))
      rows.append(('Maximum altitude', '%dm' % self.bounds.ele.max))
      rows.append(('Accumulated altitude gain', '%dm' % self.dz_positive[-1]))
      rows.append(('Landing altitude', '%dm' % self.coords[-1].ele))
    description = kml.description(kml.CDATA('<table>%s</table>' % ''.join(['<tr><th align="right">%s</th><td>%s</td></tr>' % row for row in rows])))
    snippet = kml.Snippet(self.meta.pilot_name) # FIXME
    return kmz.kmz(description, snippet)

  def make_solid_track(self, hints, style, altitude_mode, extrude=None, **folder_options):
    line_string = kml.LineString(coordinates=self.coords, altitudeMode=altitude_mode)
    if extrude:
      line_string.add(extrude=1)
    placemark = kml.Placemark(style, line_string)
    folder_options['styleUrl'] = hints.stock.check_hide_children_style.url()
    return kmz.kmz(kml.Folder(placemark, **folder_options))

  def make_colored_track(self, hints, values, scale, altitude_mode, **folder_options):
    folder = kml.Folder(name='Colored by %s' % scale.title, styleUrl=hints.stock.check_hide_children_style.url(), **folder_options)
    styles = [kml.Style(kml.LineStyle(color=rgb_to_kml(rgb), width=hints.width)) for rgb in scale.rgbs()]
    discrete_values = map(scale.discretize, values)
    for start, end in runs(discrete_values):
      line_string = kml.LineString(coordinates=self.coords[start:end + 1], altitudeMode=hints.altitude_mode)
      style_url = kml.styleUrl(styles[discrete_values[start]].url())
      placemark = kml.Placemark(style_url, line_string)
      folder.add(placemark)
    return kmz.kmz(folder).add_roots(*styles)

  def make_track_folder(self, hints):
    folder = kmz.kmz(kml.Folder(name='Track', open=1, styleUrl=hints.stock.radio_folder_style.url()))
    folder.add(hints.stock.invisible_none_folder)
    if self.elevation_data:
      folder.add(self.make_colored_track(hints, map(lambda c: c.ele, self.coords), hints.altitude_scale, 'absolute'))
    folder.add(self.make_solid_track(hints, kml.Style(kml.LineStyle(color=hints.color, width=hints.width)), hints.altitude_mode, name='Solid color', visibility=0))
    return folder

  def make_shadow_folder(self, hints):
    if not self.elevation_data:
      return kmz.kmz()
    folder = kmz.kmz(kml.Folder(name='Shadow', open=1, styleUrl=hints.stock.radio_folder_style.url()))
    folder.add(hints.stock.invisible_none_folder)
    folder.add(self.make_solid_track(hints, kml.Style(kml.LineStyle(color='ff000000', width=1)), 'clampToGround', name='Normal', visibility=1))
    folder.add(self.make_solid_track(hints, kml.Style(kml.LineStyle(color='00000000', width=1), kml.PolyStyle(color='80000000')), 'absolute', True, name='Extrude', visibility=0))
    folder.add(self.make_solid_track(hints, kml.Style(kml.LineStyle(color=hints.color, width=hints.width)), 'clampToGround', name='Solid color', visibility=0))
    return folder

  def kmz(self, hints):
    result = kmz.kmz()
    hints.altitude_scale = Scale('altitude', (self.bounds.ele.min, self.bounds.ele.max), defaultGradient)
    result.add_siblings(hints.stock.kmz)
    result.add_siblings(self.make_description(hints))
    result.add_siblings(open=1)
    result.add_siblings(self.make_track_folder(hints))
    result.add_siblings(self.make_shadow_folder(hints))
    return result
