from cStringIO import StringIO
import datetime
import itertools
import math
import urllib
import sys
import time

#import numpy
from pygooglechart import Axis, Chart, XYLineChart

from bounds import bounds, Bounds, BoundsSet
import kml
import kmz
import lib
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


def decimal_step_generator(start=1.0):
  while True:
    yield 1.0 * start
    yield 2.0 * start
    yield 5.0 * start
    start = 10.0 * start


class YAxis(object):

  def __init__(self, y):
    y_range = bounds(y.__iter__())
    for step in decimal_step_generator(0.1):
      bottom = int(y_range.min / step)
      top = int(y_range.max / step)
      if y_range.max > step * top:
        top += 1
      if top - bottom < 16:
        self.range = (step * bottom, step * top)
        self.grid_step = '%.1f' % (100.0 / (top - bottom))
        break


def time_step_generator(start=1):
  steps = [1, 5, 15, 30, 60, 5 * 60, 15 * 60, 30 * 60, 60 * 60, 3 * 60 * 60, 6 * 60 * 60, 12 * 60 * 60, 24 * 60 * 60]
  return itertools.imap(lambda x: datetime.timedelta(0, x), itertools.dropwhile(lambda x: x < start, steps))


def datetime_round_down(dt, delta):
  if delta.seconds >= 3600:
    return dt.replace(minute=0, second=0) - datetime.timedelta(0, 3600 * (dt.hour % int(delta.seconds / 3600)))
  elif delta.seconds >= 60:
    return dt.replace(second=0) - datetime.timedelta(0, 60 * (dt.minute % int(delta.seconds / 60)))
  elif delta.seconds >= 1:
    return dt - datetime.timedelta(0, dt.second % delta.seconds)
  else:
    return dt


class TimeAxis(object):

  def __init__(self, times):
    step = None
    for step in time_step_generator():
      start = datetime_round_down(times[0], step)
      stop = datetime_round_down(times[-1], step)
      if stop < times[-1]:
        stop += step
      duration = (stop - start).seconds
      if (stop - start).seconds / step.seconds < 16:
        self.range = (time.mktime(start.timetuple()), time.mktime(stop.timetuple()))
        self.grid_step = '%.1f' % (100.0 * step.seconds / duration)
        break
    self.labels = []
    self.positions = []
    t = datetime.datetime(start.year, start.month, start.day, start.hour)
    while t <= stop:
      self.labels.append(t.strftime('%H:%M'))
      self.positions.append('%.1f' % (100.0 * (t - start).seconds / duration))
      t += step


class Stock(object):

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
    self.kmz.add_files({self.pixel_url: open(self.pixel_url).read()})
    self.visible_none_folder = self.make_none_folder(1)
    self.invisible_none_folder = self.make_none_folder(0)
    animation_icon_url = 'images/paraglider.png'
    self.animation_icon = kml.Icon(href=animation_icon_url)
    self.kmz.add_files({animation_icon_url: open(animation_icon_url).read()})


class Hints(object):

  def __init__(self):
    self.altitude_mode = 'absolute'
    self.color = 'ff0000ff'
    self.width = 2
    self.graph_width = 720
    self.graph_height = 405


class Track(object):

  def __init__(self, meta, times, coords):
    self.meta = meta
    self.times = times
    self.coords = coords
    self.bounds = BoundsSet()
    self.bounds.ele = Bounds(self.coords[0].ele)
    for coord in self.coords:
      self.bounds.ele.merge(coord.ele)
    self.elevation_data = self.bounds.ele.min != 0 or self.bounds.ele.max != 0

  def analyse(self, period=20):
    half_period = period / 2.0
    self.dz_positive = [0]
    self.s = [0]
    for i in range(1, len(self.coords)):
      dz = self.coords[i].ele - self.coords[i - 1].ele
      if dz > 0.0:
        dz_positive = dz
      else:
        dz_positive = 0.0
      self.dz_positive.append(self.dz_positive[i - 1] + dz_positive)
      x = math.sin(math.pi * self.coords[i - 1].lat / 180.0) * math.sin(math.pi * self.coords[i].lat / 180.0) + math.cos(math.pi * self.coords[i - 1].lat / 180.0) * math.cos(math.pi * self.coords[i].lat) * math.cos(math.pi * (self.coords[i - 1].lon - self.coords[i].lon) / 180.0)
      if x < 1.0:
        ds = 6371.0 * math.acos(x)
      else:
        ds = 0.0
      self.s.append(self.s[i - 1] + ds)
    if 0:
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

  def make_solid_track(self, hints, style, altitude_mode, extrude=None, **folder_options):
    line_string = kml.LineString(coordinates=self.coords, altitudeMode=altitude_mode)
    if extrude:
      line_string.add(extrude=1)
    placemark = kml.Placemark(style, line_string)
    folder_options['styleUrl'] = hints.stock.check_hide_children_style.url()
    return kmz.kmz(kml.Folder(placemark, **folder_options))

  def make_colored_track(self, hints, values, scale, altitude_mode, **folder_options):
    folder = kml.Folder(name='Colored by %s' % scale.title, styleUrl=hints.stock.check_hide_children_style.url(), **folder_options)
    styles = [kml.Style(kml.LineStyle(color=color, width=hints.width)) for color in scale.colors()]
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
      folder.add(self.make_colored_track(hints, map(lambda c: c.ele, self.coords), hints.stock.altitude_scale, 'absolute'))
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

  def make_animation(self, hints):
    style = kml.Style(kml.IconStyle(hints.stock.animation_icon, color=hints.color, scale=0.5))
    folder = kml.Folder(style, name='Animation', open=0, styleUrl=hints.stock.check_hide_children_style.url())
    point = kml.Point(coordinates=[self.coords[0]], altitudeMode=hints.altitude_mode)
    timespan = kml.TimeSpan(end=kml.dateTime(self.times[0]))
    placemark = kml.Placemark(point, timespan, styleUrl=style.url())
    folder.add(placemark)
    for i in range(1, len(self.coords)):
      point = kml.Point(coordinates=[self.coords[i - 1].halfway_to(self.coords[i])], altitudeMode=hints.altitude_mode)
      timespan = kml.TimeSpan(begin=kml.dateTime(self.times[i - 1]), end=kml.dateTime(self.times[i]))
      placemark = kml.Placemark(point, timespan, styleUrl=style.url())
      folder.add(placemark)
    point = kml.Point(coordinates=[self.coords[-1]], altitudeMode=hints.altitude_mode)
    timespan = kml.TimeSpan(begin=kml.dateTime(self.times[-1]))
    placemark = kml.Placemark(point, timespan, styleUrl=style.url())
    folder.add(placemark)
    return kmz.kmz(folder)

  def make_graph(self, hints, name, y, epsilon):
    time_axis = TimeAxis(self.times)
    y_axis = YAxis(y)
    chart = XYLineChart(hints.graph_width, hints.graph_height, x_range=time_axis.range, y_range=y_axis.range)
    chart.fill_solid(Chart.BACKGROUND, 'ffffff00')
    chart.fill_solid(Chart.CHART, 'ffffffcc')
    axis_index = chart.set_axis_range(Axis.LEFT, y_axis.range[0], y_axis.range[1])
    chart.set_axis_style(axis_index, 'ffffff')
    axis_index = chart.set_axis_labels(Axis.BOTTOM, time_axis.labels)
    chart.set_axis_positions(axis_index, time_axis.positions)
    chart.set_axis_style(axis_index, 'ffffff')
    chart.set_grid(time_axis.grid_step, y_axis.grid_step, 2, 2)
    indexes = lib.douglas_peucker(self.coords.t, y, epsilon)
    chart.add_data([self.coords.t[i] for i in indexes])
    chart.add_data([y[i] for i in indexes])
    icon = kml.Icon(href=chart.get_url().replace('&', '&amp;'))
    overlay_xy = kml.overlayXY(x=0, y=0, xunits='fraction', yunits='fraction')
    screen_xy = kml.screenXY(x=0, y=16, xunits='fraction', yunits='pixels')
    size = kml.size(x=0, y=0, xunits='fraction', yunits='fraction')
    screen_overlay = kml.ScreenOverlay(icon, overlay_xy, screen_xy, size)
    folder = kml.Folder(screen_overlay, name=name, styleUrl=hints.stock.check_hide_children_style.url(), visibility=0)
    return folder

  def make_graphs_folder(self, hints):
    folder = kmz.kmz(kml.Folder(name='Graphs', open=1, styleUrl=hints.stock.radio_folder_style.url()))
    folder.add(hints.stock.visible_none_folder)
    folder.add(self.make_graph(hints, 'Altitude', list(coord.ele for coord in self.coords), 5))
    return folder

  def kmz(self, hints):
    folder = kmz.kmz(kml.Folder(name=self.meta.name, open=1))
    rows = []
    if not self.meta.pilot_name is None:
      rows.append(('Pilot name', self.meta.pilot_name))
    if not self.meta.glider_type is None:
      rows.append(('Glider type', self.meta.glider_type))
    if not self.meta.glider_id is None:
      rows.append(('Glider ID', self.meta.glider_id))
    rows.append(('Take-off time', self.times[0].strftime('%H:%M:%S')))
    rows.append(('Landing time', self.times[-1].strftime('%H:%M:%S')))
    hour, seconds = divmod((self.times[-1] - self.times[0]).seconds, 3600)
    minute, second = divmod(seconds, 60)
    rows.append(('Duration', '%d:%02d:%02d' % (hour, minute, second)))
    #rows.append(('Track length', '%.3fkm' % (self.s[-1] / 1000.0)))
    if self.elevation_data:
      rows.append(('Take-off altitude', '%dm' % self.coords[0].ele))
      rows.append(('Maximum altitude', '%dm' % self.bounds.ele.max))
      #rows.append(('Accumulated altitude gain', '%dm' % self.dz_positive[-1]))
      rows.append(('Landing altitude', '%dm' % self.coords[-1].ele))
    folder.add(kml.description(kml.CDATA('<table>%s</table>' % ''.join(['<tr><th align="right">%s</th><td>%s</td></tr>' % row for row in rows]))))
    folder.add(kml.Snippet(self.meta.pilot_name)) # FIXME
    folder.add(self.make_animation(hints))
    folder.add(self.make_track_folder(hints))
    folder.add(self.make_shadow_folder(hints))
    folder.add(self.make_graphs_folder(hints))
    return folder
