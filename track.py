from cStringIO import StringIO
import datetime
import itertools
import math
import urllib
import sys
import time

import numpy
import pygooglechart

from bounds import bounds, Bounds, BoundsSet
import kml
import kmz
import lib
from OpenStruct import OpenStruct


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


class Track(object):

  def __init__(self, meta, times, coords):
    self.meta = meta
    self.times = times
    self.coords = coords
    self.bounds = BoundsSet()
    self.bounds.ele = Bounds(self.coords[0].ele)
    for coord in self.coords:
      self.bounds.ele.merge(coord.ele)
    self.bounds.time = Bounds(self.times[0], self.times[-1])
    self.elevation_data = self.bounds.ele.min != 0 or self.bounds.ele.max != 0
    self.s = [0.0]
    for i in xrange(1, len(self.coords)):
      self.s.append(self.s[i - 1] + self.coords[i - 1].distance_to(self.coords[i]))

  def pre(self, dt):
    coords = []
    ss = []
    i0 = 0
    for i in xrange(0, len(self.coords)):
      t0 = self.coords.t[i] - dt
      while self.coords.t[i0] <= t0:
        i0 += 1
      if i0 == 0:
        coord0 = self.coords[0]
        s0 = self.s[0]
      else:
        delta0 = float(t0 - self.coords.t[i0 - 1]) / (self.coords.t[i0] - self.coords.t[i0 - 1])
        coord0 = self.coords[i0 - 1].interpolate(self.coords[i0], delta0)
        s0 = (1.0 - delta0) * self.s[i0 - 1] + delta0 * self.s[i0]
      coords.append(coord0)
      ss.append(s0)
    return (coords, ss)

  def post(self, dt):
    n = len(self.coords)
    coords = []
    ss = []
    i1 = 0
    for i in xrange(0, len(self.coords)):
      t1 = self.coords.t[i] + dt
      while i1 < n and self.coords.t[i1] < t1:
        i1 += 1
      if i1 == n:
        coord1 = self.coords[n - 1]
        s1 = self.s[n - 1]
      else:
        delta1 = float(t1 - self.coords.t[i1 - 1]) / (self.coords.t[i1] - self.coords.t[i1 - 1])
        coord1 = self.coords[i1 - 1].interpolate(self.coords[i1], delta1)
        s1 = (1.0 - delta1) * self.s[i1 - 1] + delta1 * self.s[i1]
      coords.append(coord1)
      ss.append(s1)
    return (coords, ss)

  def moving_pre_progress(self, dt=20):
    result = []
    i0 = 0
    for i in xrange(0, len(self.coords)):
      t0 = self.coords.t[i] - dt
      while self.coords.t[i0] <= t0:
        i0 += 1
      if i0 == 0:
        coord0 = self.coords[0]
        s0 = self.s[0]
      else:
        delta0 = float(t0 - self.coords.t[i0 - 1]) / (self.coords.t[i0] - self.coords.t[i0 - 1])
        coord0 = self.coords[i0 - 1].interpolate(self.coords[i0], delta0)
        s0 = (1.0 - delta0) * self.s[i0 - 1] + delta0 * self.s[i0]
      dp = coord0.distance_to(self.coords[i])
      ds = self.s[i] - s0
      if ds == 0.0:
        result.append(0.0)
      elif dp > ds:
        result.append(1.0)
      else:
        result.append(ds and dp / ds or 0.0)
    return result

  def analyse(self, dt=20):
    n = len(self.coords)
    self.ele = []
    for i in xrange(1, n):
      self.ele.append((self.coords[i - 1].ele + self.coords[i].ele) / 2.0)
    self.total_dz_positive = 0
    self.max_dz_positive = 0
    min_ele = self.coords[0].ele
    for i in xrange(1, n):
      dz = self.coords[i].ele - self.coords[i - 1].ele
      if dz > 0:
        self.total_dz_positive += dz
      if self.coords[i].ele < min_ele:
        min_ele = self.coords[i].ele
      elif self.coords[i].ele - min_ele > self.max_dz_positive:
        self.max_dz_positive = self.coords[i].ele - min_ele
    self.speed = []
    self.climb = []
    i0 = i1 = 0
    for i in xrange(1, n):
      t0 = (self.coords.t[i - 1] + self.coords.t[i]) / 2 - dt / 2
      while self.coords.t[i0] <= t0:
        i0 += 1
      if i0 == 0:
        coord0 = self.coords[0]
        s0 = self.s[0]
      else:
        delta0 = float(t0 - self.coords.t[i0 - 1]) / (self.coords.t[i0] - self.coords.t[i0 - 1])
        coord0 = self.coords[i0 - 1].interpolate(self.coords[i0], delta0)
        s0 = (1.0 - delta0) * self.s[i0 - 1] + delta0 * self.s[i0]
      t1 = t0 + dt
      while i1 < n and self.coords.t[i1] < t1:
        i1 += 1
      if i1 == n:
        coord1 = self.coords[n - 1]
        s1 = self.s[n - 1]
      else:
        delta1 = float(t1 - self.coords.t[i1 - 1]) / (self.coords.t[i1] - self.coords.t[i1 - 1])
        coord1 = self.coords[i1 - 1].interpolate(self.coords[i1], delta1)
        s1 = (1.0 - delta1) * self.s[i1 - 1] + delta1 * self.s[i1]
      ds = s1 - s0
      dz = coord1.ele - coord0.ele
      self.speed.append(3.6 * ds / dt)
      self.climb.append(dz / dt)
    self.bounds.speed = bounds(self.speed.__iter__())
    self.bounds.climb = bounds(self.climb.__iter__())
    pre_coords, pre_s = self.pre(20)
    post_coords, post_s = self.post(20)
    self.pre_progress = []
    self.progress = []
    self.post_progress = []
    for i in xrange(0, n):
      pre_dp = pre_coords[i].distance_to(self.coords[i])
      pre_ds = self.s[i] - pre_s[i]
      if pre_ds == 0.0:
        self.pre_progress.append(0.0)
      elif pre_dp > pre_ds:
        self.pre_progress.append(1.0)
      else:
        self.pre_progress.append(pre_dp / pre_ds)
      dp = pre_coords[i].distance_to(post_coords[i])
      ds = post_s[i] - pre_s[i]
      if ds == 0.0:
        self.progress.append(0.0)
      elif dp > ds:
        self.progress.append(1.0)
      else:
        self.progress.append(dp / ds)
      post_dp = self.coords[i].distance_to(post_coords[i])
      post_ds = post_s[i] - self.s[i]
      if post_ds == 0.0:
        self.post_progress.append(0.0)
      elif post_dp > post_ds:
        self.post_progress.append(1.0)
      else:
        self.post_progress.append(post_dp / post_ds)
    self.thermal = [0] * n
    state = 0
    for i in xrange(0, n):
      if state == 0:
        if self.post_progress[i] < 0.9:
          start = i
          state = 1
      elif state == 1:
        if self.progress[i] < 0.9:
          state = 2
      elif state == 2:
        if self.progress[i] < 0.9:
          state = 1
        elif self.pre_progress[i] >= 0.9:
          self.thermal[start:i] = [1] * (i - start)
          state = 0


  def make_solid_track(self, hints, style, altitude_mode, extrude=None, **folder_options):
    line_string = kml.LineString(coordinates=self.coords, altitudeMode=altitude_mode)
    if extrude:
      line_string.add(extrude=1)
    placemark = kml.Placemark(style, line_string)
    folder_options['styleUrl'] = hints.globals.stock.check_hide_children_style.url()
    return kmz.kmz(kml.Folder(placemark, **folder_options))

  def make_scale_chart(self, hints, scale):
    chart = pygooglechart.SimpleLineChart(50, 200, x_range=(0, 1), y_range=scale.range)
    chart.fill_solid(pygooglechart.Chart.BACKGROUND, 'ffffff00')
    chart.fill_solid(pygooglechart.Chart.CHART, 'ffffffcc')
    for i in xrange(0, 32 + 1):
      y = i * (scale.range[1] - scale.range[0]) / 32 + scale.range[0]
      chart.add_data([y, y])
      chart.set_line_style(i, 0)
    for i in xrange(0, 32):
      r, g, b, a = scale.color((i * (scale.range[1] - scale.range[0]) + 0.5) / 32 + scale.range[0])
      color = '%02x%02x%02x' % (255 * r, 255 * g, 255 * b)
      chart.add_fill_range(color, i, i + 1)
    axis_index = chart.set_axis_range(pygooglechart.Axis.LEFT, scale.range[0], scale.range[1])
    chart.set_axis_style(axis_index, 'ffffff')
    return chart

  def make_colored_track(self, hints, values, scale, altitude_mode, **folder_options):
    folder = kml.Folder(name='Colored by %s' % scale.title, styleUrl=hints.globals.stock.check_hide_children_style.url(), **folder_options)
    styles = [kml.Style(kml.LineStyle(color=color, width=hints.width)) for color in scale.colors()]
    discrete_values = map(scale.discretize, values)
    for start, end in lib.runs(discrete_values):
      line_string = kml.LineString(coordinates=self.coords[start:end + 1], altitudeMode=hints.altitude_mode)
      style_url = kml.styleUrl(styles[discrete_values[start]].url())
      placemark = kml.Placemark(style_url, line_string)
      folder.add(placemark)
    icon = kml.Icon(href=kml.CDATA(self.make_scale_chart(hints, scale).get_url()))
    overlay_xy = kml.overlayXY(x=0, y=1, xunits='fraction', yunits='fraction')
    screen_xy = kml.screenXY(x=0, y=1, xunits='fraction', yunits='fraction')
    size = kml.size(x=0, y=0, xunits='fraction', yunits='fraction')
    screen_overlay = kml.ScreenOverlay(icon, overlay_xy, screen_xy, size)
    folder.add(screen_overlay)
    return kmz.kmz(folder).add_roots(*styles)

  def make_track_folder(self, hints):
    folder = kmz.kmz(kml.Folder(name='Track', open=1, styleUrl=hints.globals.stock.radio_folder_style.url()))
    folder.add(hints.globals.stock.invisible_none_folder)
    if self.elevation_data:
      folder.add(self.make_colored_track(hints, self.ele, hints.globals.altitude_scale, 'absolute', visibility=0))
      folder.add(self.make_colored_track(hints, self.climb, hints.globals.climb_scale, 'absolute'))
    folder.add(self.make_colored_track(hints, self.speed, hints.globals.speed_scale, hints.altitude_mode, visibility=not self.elevation_data))
    folder.add(self.make_colored_track(hints, self.pre_progress, hints.globals.progress_scale, hints.altitude_mode, visibility=0))
    folder.add(self.make_colored_track(hints, self.progress, hints.globals.progress_scale, hints.altitude_mode, visibility=0))
    folder.add(self.make_colored_track(hints, self.post_progress, hints.globals.progress_scale, hints.altitude_mode, visibility=0))
    folder.add(self.make_colored_track(hints, self.thermal, hints.globals.progress_scale, hints.altitude_mode, visibility=0))
    folder.add(self.make_solid_track(hints, kml.Style(kml.LineStyle(color=hints.color, width=hints.width)), hints.altitude_mode, name='Solid color', visibility=0))
    return folder

  def make_shadow_folder(self, hints):
    if not self.elevation_data:
      return kmz.kmz()
    folder = kmz.kmz(kml.Folder(name='Shadow', open=1, styleUrl=hints.globals.stock.radio_folder_style.url()))
    folder.add(hints.globals.stock.invisible_none_folder)
    folder.add(self.make_solid_track(hints, kml.Style(kml.LineStyle(color='ff000000', width=1)), 'clampToGround', name='Normal', visibility=1))
    folder.add(self.make_solid_track(hints, kml.Style(kml.LineStyle(color='00000000', width=1), kml.PolyStyle(color='80000000')), 'absolute', True, name='Extrude', visibility=0))
    folder.add(self.make_solid_track(hints, kml.Style(kml.LineStyle(color=hints.color, width=hints.width)), 'clampToGround', name='Solid color', visibility=0))
    return folder

  def make_animation(self, hints):
    style = kml.Style(kml.IconStyle(hints.globals.stock.animation_icon, color=hints.color, scale=0.5))
    folder = kml.Folder(style, name='Animation', open=0, styleUrl=hints.globals.stock.check_hide_children_style.url())
    point = kml.Point(coordinates=[self.coords[0]], altitudeMode=hints.altitude_mode)
    timespan = kml.TimeSpan(end=kml.dateTime(self.times[0]))
    placemark = kml.Placemark(point, timespan, styleUrl=style.url())
    folder.add(placemark)
    for i in xrange(1, len(self.coords)):
      point = kml.Point(coordinates=[self.coords[i - 1].halfway_to(self.coords[i])], altitudeMode=hints.altitude_mode)
      timespan = kml.TimeSpan(begin=kml.dateTime(self.times[i - 1]), end=kml.dateTime(self.times[i]))
      placemark = kml.Placemark(point, timespan, styleUrl=style.url())
      folder.add(placemark)
    point = kml.Point(coordinates=[self.coords[-1]], altitudeMode=hints.altitude_mode)
    timespan = kml.TimeSpan(begin=kml.dateTime(self.times[-1]))
    placemark = kml.Placemark(point, timespan, styleUrl=style.url())
    folder.add(placemark)
    return kmz.kmz(folder)

  def make_placemark(self, coord, altitudeMode=None, name=None, styleUrl=None):
    point = kml.Point(coordinates=[coord], altitudeMode=altitudeMode)
    placemark = kml.Placemark(point, kml.Snippet(), name=name, styleUrl=styleUrl)
    return placemark

  def make_altitude_marks_folder(self, hints):
    if self.elevation_data:
      folder = kml.Folder(name='Altitude marks', styleUrl=hints.globals.stock.check_hide_children_style.url())
      for index in lib.salient([c.ele for c in self.coords], 100):
        coord = self.coords[index]
        folder.add(self.make_placemark(coord, altitudeMode='absolute', name='%dm' % coord.ele, styleUrl=hints.globals.altitude_styles[hints.globals.altitude_scale.discretize(coord.ele)].url()))
      return kmz.kmz(folder)
    else:
      return kmz.kmz()

  def make_graph_chart(self, hints, values, scale):
    chart = pygooglechart.XYLineChart(hints.globals.graph_width, hints.globals.graph_height, x_range=hints.globals.time_scale.range, y_range=scale.range)
    chart.fill_solid(pygooglechart.Chart.BACKGROUND, 'ffffff00')
    chart.fill_solid(pygooglechart.Chart.CHART, 'ffffffcc')
    axis_index = chart.set_axis_labels(pygooglechart.Axis.BOTTOM, hints.globals.time_scale.labels)
    chart.set_axis_positions(axis_index, hints.globals.time_scale.positions)
    chart.set_axis_style(axis_index, 'ffffff')
    axis_index = chart.set_axis_range(pygooglechart.Axis.LEFT, scale.range[0], scale.range[1])
    chart.set_axis_style(axis_index, 'ffffff')
    chart.set_grid(hints.globals.time_scale.grid_step, scale.grid_step, 2, 2)
    y = hints.globals.graph_height * (numpy.array(values) - scale.range[0]) / (scale.range[1] - scale.range[0])
    indexes = lib.incremental_douglas_peucker(hints.time_positions, y, 1, 450)
    chart.add_data([self.coords.t[i] for i in indexes])
    chart.add_data([values[i] for i in indexes])
    return chart

  def make_graph(self, hints, values, scale):
    icon = kml.Icon(href=kml.CDATA(self.make_graph_chart(hints, values, scale).get_url()))
    overlay_xy = kml.overlayXY(x=0, y=0, xunits='fraction', yunits='fraction')
    screen_xy = kml.screenXY(x=0, y=16, xunits='fraction', yunits='pixels')
    size = kml.size(x=0, y=0, xunits='fraction', yunits='fraction')
    screen_overlay = kml.ScreenOverlay(icon, overlay_xy, screen_xy, size)
    folder = kml.Folder(screen_overlay, name=scale.title.capitalize(), styleUrl=hints.globals.stock.check_hide_children_style.url(), visibility=0)
    return folder

  def make_graphs_folder(self, hints):
    folder = kmz.kmz(kml.Folder(name='Graphs', open=1, styleUrl=hints.globals.stock.radio_folder_style.url()))
    folder.add(hints.globals.stock.visible_none_folder)
    folder.add(self.make_graph(hints, [c.ele for c in self.coords], hints.globals.altitude_scale))
    #folder.add(self.make_graph(hints, self.climb, hints.globals.climb_scale))
    #folder.add(self.make_graph(hints, self.speed, hints.globals.speed_scale))
    folder.add(self.make_graph(hints, self.pre_progress, hints.globals.progress_scale))
    folder.add(self.make_graph(hints, self.progress, hints.globals.progress_scale))
    folder.add(self.make_graph(hints, self.post_progress, hints.globals.progress_scale))
    folder.add(self.make_graph(hints, self.thermal, hints.globals.progress_scale))
    return folder

  def kmz(self, hints):
    folder = kmz.kmz(kml.Folder(name=self.meta.name, open=1))
    rows = []
    if self.meta.pilot_name:
      rows.append(('Pilot name', self.meta.pilot_name))
    if self.meta.glider_type:
      rows.append(('Glider type', self.meta.glider_type))
    if self.meta.glider_id:
      rows.append(('Glider ID', self.meta.glider_id))
    rows.append(('Take-off time', (self.times[0] + hints.globals.timezone_offset).strftime('%H:%M:%S')))
    rows.append(('Landing time', (self.times[-1] + hints.globals.timezone_offset).strftime('%H:%M:%S')))
    hour, seconds = divmod((self.times[-1] - self.times[0]).seconds, 3600)
    minute, second = divmod(seconds, 60)
    rows.append(('Duration', '%d:%02d:%02d' % (hour, minute, second)))
    if self.elevation_data:
      rows.append(('Take-off altitude', '%dm' % self.coords[0].ele))
      rows.append(('Maximum altitude', '%dm' % self.bounds.ele.max))
      rows.append(('Minimum altitude', '%dm' % self.bounds.ele.min))
      rows.append(('Landing altitude', '%dm' % self.coords[-1].ele))
      rows.append(('Total altitude gain', '%dm' % self.total_dz_positive))
      rows.append(('Maximum altitude gain', '%dm' % self.max_dz_positive))
      rows.append(('Maximum climb', '%.1fm/s' % self.bounds.climb.max))
      rows.append(('Maximum sink', '%.1fm/s' % self.bounds.climb.min))
    rows.append(('Maximum speed', '%.1fkm/h' % self.bounds.speed.max))
    folder.add(kml.description(kml.CDATA('<table>%s</table>' % ''.join('<tr><th align="right">%s</th><td>%s</td></tr>' % row for row in rows))))
    snippet = [self.meta.pilot_name, self.meta.glider_type, (self.times[0] + hints.globals.timezone_offset).strftime('%Y-%m-%d')]
    folder.add(kml.Snippet(', '.join(s for s in snippet if s)))
    hints.time_positions = hints.globals.graph_width * (numpy.array(self.coords.t) - hints.globals.time_scale.range[0]) / (hints.globals.time_scale.range[1] - hints.globals.time_scale.range[0])
    folder.add(self.make_animation(hints))
    folder.add(self.make_track_folder(hints))
    folder.add(self.make_shadow_folder(hints))
    folder.add(self.make_altitude_marks_folder(hints))
    folder.add(self.make_graphs_folder(hints))
    return folder
