#   igc2kmz/__init__.py  igc2kmz main module
#   Copyright (C) 2008  Tom Payne
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.


import datetime
import math
import operator
import unicodedata

import third_party.pygooglechart as pygooglechart

import color
import kml
import kmz
import scale
import util


RIGHTWARDS_ARROW = unicodedata.lookup('RIGHTWARDS ARROW').encode('utf_8')
INFINITY = unicodedata.lookup('INFINITY').encode('utf_8')
MULTIPLICATION_SIGN = unicodedata.lookup('MULTIPLICATION SIGN').encode('utf_8')


class Stock(object):

  def make_none_folder(self, visibility):
    icon = kml.Icon(href=self.pixel_url)
    overlay_xy = kml.overlayXY(x=0, y=0, xunits='fraction', yunits='fraction')
    screen_xy = kml.screenXY(x=0, y=0, xunits='fraction', yunits='fraction')
    size = kml.size(x=0, y=0, xunits='fraction', yunits='fraction')
    screen_overlay = kml.ScreenOverlay(icon, overlay_xy, screen_xy, size, visibility=visibility)
    return kml.Folder(screen_overlay, name='None', styleUrl=self.check_hide_children_style.url())

  def make_analysis_style(self, color):
    balloon_style = kml.BalloonStyle(text=kml.CDATA('<h3>$[name]</h3>$[description]'))
    icon_style = kml.IconStyle(self.icons[0], color=color, scale=self.icon_scales[0])
    label_style = kml.LabelStyle(color=color, scale=self.label_scales[0])
    line_style = kml.LineStyle(color=color, width=4)
    return kml.Style(balloon_style, icon_style, label_style, line_style)

  def __init__(self):
    self.kmz = kmz.kmz()
    self.icon_scales = [math.sqrt(x) for x in [0.6, 0.5, 0.4, 0.3]]
    self.icons = [kml.Icon.palette(4, i) for i in [25, 25, 24, 24]]
    self.label_scales = [math.sqrt(x) for x in [0.6, 0.5, 0.4, 0.3]]
    self.radio_folder_style = kml.Style(kml.ListStyle(listItemType='radioFolder'))
    self.kmz.add_roots(self.radio_folder_style)
    self.check_hide_children_style = kml.Style(kml.ListStyle(listItemType='checkHideChildren'))
    self.kmz.add_roots(self.check_hide_children_style)
    self.thermal_style = self.make_analysis_style('cc3333ff')
    self.kmz.add_roots(self.thermal_style)
    self.dive_style = self.make_analysis_style('ccff3333')
    self.kmz.add_roots(self.dive_style)
    self.glide_style = self.make_analysis_style('cc33ff33')
    self.kmz.add_roots(self.glide_style)
    self.time_mark_styles = []
    for i in xrange(0, len(self.icons)):
      icon_style = kml.IconStyle(self.icons[i], scale=self.icon_scales[i])
      label_style = kml.LabelStyle(color='cc33ffff', scale=self.label_scales[i])
      self.time_mark_styles.append(kml.Style(icon_style, label_style))
    self.kmz.add_roots(*self.time_mark_styles)
    balloon_style = kml.BalloonStyle(text=kml.CDATA('<h3>$[name]</h3>$[description]'))
    icon_style = kml.IconStyle(kml.Icon.palette(4, 46), scale=self.icon_scales[0])
    label_style = kml.LabelStyle(scale=self.label_scales[0])
    self.photo_style = kml.Style(balloon_style, icon_style, label_style)
    self.kmz.add_roots(self.photo_style)
    balloon_style = kml.BalloonStyle(text=kml.CDATA('<h3>$[name]</h3>$[description]'))
    icon_style = kml.IconStyle(self.icons[0], color='ccff33ff', scale=self.icon_scales[0])
    label_style = kml.LabelStyle(color='ccff33ff', scale=self.label_scales[0])
    line_style = kml.LineStyle(color='ccff33ff', width=2)
    self.xc_style = kml.Style(balloon_style, icon_style, label_style, line_style)
    self.kmz.add_roots(self.xc_style)
    balloon_style = kml.BalloonStyle(text=kml.CDATA('<h3>$[name]</h3>$[description]'))
    icon_style = kml.IconStyle(self.icons[0], color='ccff33ff', scale=self.icon_scales[0])
    label_style = kml.LabelStyle(color='ccff33ff', scale=self.label_scales[0])
    line_style = kml.LineStyle(color='ccff33ff')
    self.xc_style2 = kml.Style(balloon_style, icon_style, label_style, line_style)
    self.kmz.add_roots(self.xc_style2)
    self.pixel_url = 'images/pixel.png'
    self.kmz.add_files({self.pixel_url: open(self.pixel_url).read()})
    self.visible_none_folder = self.make_none_folder(1)
    self.invisible_none_folder = self.make_none_folder(0)
    animation_icon_url = 'images/paraglider.png'
    self.animation_icon = kml.Icon(href=animation_icon_url)
    self.kmz.add_files({animation_icon_url: open(animation_icon_url).read()})


class Flight(object):

  def __init__(self, track, **kwargs):
    self.track = track
    self.altitude_mode = 'absolute' if self.track.elevation_data else 'clampToGround'
    self.color = 'ff0000ff'
    self.width = 2
    self.pilot_name = track.pilot_name
    self.glider_type = track.glider_type
    self.glider_id = track.glider_id
    self.photos = []
    self.xc = None
    self.__dict__.update(kwargs)

  def make_description(self, globals):
    rows = []
    if self.pilot_name:
      rows.append(('Pilot name', self.pilot_name))
    if self.glider_type:
      rows.append(('Glider type', self.glider_type))
    if self.glider_id:
      rows.append(('Glider ID', self.glider_id))
    rows.append(('Take-off time', (self.track.bounds.time.min + globals.timezone_offset).strftime('%H:%M:%S')))
    rows.append(('Landing time', (self.track.bounds.time.max + globals.timezone_offset).strftime('%H:%M:%S')))
    hour, seconds = divmod((self.track.bounds.time.max - self.track.bounds.time.min).seconds, 3600)
    minute, second = divmod(seconds, 60)
    rows.append(('Duration', '%d:%02d:%02d' % (hour, minute, second)))
    if self.track.elevation_data:
      rows.append(('Take-off altitude', '%dm' % self.track.coords[0].ele))
      rows.append(('Maximum altitude', '%dm' % self.track.bounds.ele.max))
      rows.append(('Minimum altitude', '%dm' % self.track.bounds.ele.min))
      rows.append(('Landing altitude', '%dm' % self.track.coords[-1].ele))
      rows.append(('Total altitude gain', '%dm' % self.track.total_dz_positive))
      rows.append(('Maximum altitude gain', '%dm' % self.track.max_dz_positive))
      rows.append(('Maximum climb', '%.1fm/s' % self.track.bounds.climb.max))
      rows.append(('Maximum sink', '%.1fm/s' % self.track.bounds.climb.min))
    rows.append(('Maximum speed', '%.1fkm/h' % self.track.bounds.speed.max))
    description = kml.description(kml.CDATA('<table>%s</table>' % ''.join('<tr><th align="right">%s</th><td>%s</td></tr>' % row for row in rows)))
    return kmz.kmz(description)

  def make_snippet(self, globals):
    strings = [self.pilot_name, self.glider_type, (self.track.bounds.time.min + globals.timezone_offset).strftime('%Y-%m-%d')]
    snippet = kml.Snippet(', '.join(s for s in strings if s))
    return kmz.kmz(snippet)

  def make_solid_track(self, globals, style, altitude_mode, extrude=None, **folder_options):
    line_string = kml.LineString(coordinates=self.track.coords, altitudeMode=altitude_mode)
    if extrude:
      line_string.add(extrude=1)
    placemark = kml.Placemark(style, line_string)
    folder_options['styleUrl'] = globals.stock.check_hide_children_style.url()
    return kmz.kmz(kml.Folder(placemark, **folder_options))

  def make_scale_chart(self, globals, scale):
    chart = pygooglechart.SimpleLineChart(40, 200, x_range=(0, 1), y_range=scale.range)
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
    axis_index = chart.set_axis_range(pygooglechart.Axis.RIGHT, scale.range[0], scale.range[1])
    chart.set_axis_style(axis_index, 'ffffff')
    return chart

  def make_colored_track(self, globals, values, scale, altitude_mode, **folder_options):
    folder = kml.Folder(name='Colored by %s' % scale.title, styleUrl=globals.stock.check_hide_children_style.url(), **folder_options)
    styles = [kml.Style(kml.LineStyle(color=color, width=self.width)) for color in scale.colors()]
    discrete_values = map(scale.discretize, values)
    for sl in util.runs(discrete_values):
      line_string = kml.LineString(coordinates=self.track.coords[sl.start:sl.stop + 1], altitudeMode=self.altitude_mode)
      style_url = kml.styleUrl(styles[discrete_values[sl.start]].url())
      placemark = kml.Placemark(style_url, line_string)
      folder.add(placemark)
    icon = kml.Icon(href=kml.CDATA(self.make_scale_chart(globals, scale).get_url()))
    overlay_xy = kml.overlayXY(x=0, y=1, xunits='fraction', yunits='fraction')
    screen_xy = kml.screenXY(x=0, y=1, xunits='fraction', yunits='fraction')
    size = kml.size(x=0, y=0, xunits='fraction', yunits='fraction')
    screen_overlay = kml.ScreenOverlay(icon, overlay_xy, screen_xy, size)
    folder.add(screen_overlay)
    return kmz.kmz(folder).add_roots(*styles)

  def make_track_folder(self, globals):
    folder = kmz.kmz(kml.Folder(name='Track', open=1, styleUrl=globals.stock.radio_folder_style.url()))
    folder.add(globals.stock.invisible_none_folder)
    if self.track.elevation_data:
      folder.add(self.make_colored_track(globals, self.track.climb, globals.scales.climb, 'absolute'))
      folder.add(self.make_colored_track(globals, self.track.ele, globals.scales.altitude, 'absolute', visibility=0))
    folder.add(self.make_colored_track(globals, self.track.speed, globals.scales.speed, self.altitude_mode, visibility=not self.track.elevation_data))
    if hasattr(self.track, 'tas'):
      folder.add(self.make_colored_track(globals, self.track.tas, globals.scales.tas, self.altitude_mode, visibility=0))
    folder.add(self.make_solid_track(globals, kml.Style(kml.LineStyle(color=self.color, width=self.width)), self.altitude_mode, name='Solid color', visibility=0))
    return folder

  def make_shadow_folder(self, globals):
    if not self.track.elevation_data:
      return kmz.kmz()
    folder = kmz.kmz(kml.Folder(name='Shadow', open=1, styleUrl=globals.stock.radio_folder_style.url()))
    folder.add(globals.stock.invisible_none_folder)
    folder.add(self.make_solid_track(globals, kml.Style(kml.LineStyle(color='ff000000', width=1)), 'clampToGround', name='Normal', visibility=1))
    folder.add(self.make_solid_track(globals, kml.Style(kml.LineStyle(color='00000000', width=1), kml.PolyStyle(color='80000000')), 'absolute', True, name='Extrude', visibility=0))
    folder.add(self.make_solid_track(globals, kml.Style(kml.LineStyle(color=self.color, width=self.width)), 'clampToGround', name='Solid color', visibility=0))
    return folder

  def make_animation(self, globals):
    style = kml.Style(kml.IconStyle(globals.stock.animation_icon, color=self.color, scale=globals.stock.icon_scales[0]))
    folder = kml.Folder(style, name='Animation', open=0, styleUrl=globals.stock.check_hide_children_style.url())
    point = kml.Point(coordinates=[self.track.coords[0]], altitudeMode=self.altitude_mode)
    timespan = kml.TimeSpan(end=kml.dateTime(self.track.coords[0].dt))
    placemark = kml.Placemark(point, timespan, styleUrl=style.url())
    folder.add(placemark)
    for i in xrange(1, len(self.track.coords)):
      point = kml.Point(coordinates=[self.track.coords[i - 1].halfway_to(self.track.coords[i])], altitudeMode=self.altitude_mode)
      timespan = kml.TimeSpan(begin=kml.dateTime(self.track.coords[i - 1].dt), end=kml.dateTime(self.track.coords[i].dt))
      placemark = kml.Placemark(point, timespan, styleUrl=style.url())
      folder.add(placemark)
    point = kml.Point(coordinates=[self.track.coords[-1]], altitudeMode=self.altitude_mode)
    timespan = kml.TimeSpan(begin=kml.dateTime(self.track.coords[-1].dt))
    placemark = kml.Placemark(point, timespan, styleUrl=style.url())
    folder.add(placemark)
    return kmz.kmz(folder)

  def make_placemark(self, globals, coord, altitudeMode=None, name=None, styleUrl=None):
    point = kml.Point(coordinates=[coord], altitudeMode=altitudeMode)
    placemark = kml.Placemark(point, kml.Snippet(), name=name, styleUrl=styleUrl)
    return placemark

  def make_altitude_marks_folder(self, globals):
    if self.track.elevation_data:
      folder = kml.Folder(name='Altitude marks', styleUrl=globals.stock.check_hide_children_style.url(), visibility=0)
      for index in util.salient([c.ele for c in self.track.coords], 100):
        coord = self.track.coords[index]
        folder.add(self.make_placemark(globals, coord, altitudeMode='absolute', name='%dm' % coord.ele, styleUrl=globals.altitude_styles[globals.scales.altitude.discretize(coord.ele)].url()))
      return kmz.kmz(folder)
    else:
      return kmz.kmz()

  def make_photos_folder(self, globals):
    if not len(self.photos):
      return kmz.kmz()
    folder = kml.Folder(name='Photos', open=0)
    for photo in sorted(self.photos, key=operator.attrgetter('dt')):
      if photo.coord:
        coord = photo.coord
        altitude_mode = 'absolute' if photo.elevation_data else 'clampToGround'
      else:
        coord = self.track.coord_at(photo.dt - globals.timezone_offset)
        altitude_mode = self.altitude_mode
      point = kml.Point(coordinates=[coord], altitudeMode=altitude_mode)
      description = kml.CDATA('<img alt="%s" src="%s" height="%d" width="%d" />' % (photo.name, photo.url, photo.jpeg.height, photo.jpeg.width))
      placemark = kml.Placemark(point, kml.Snippet(), name=photo.name, description=description, styleUrl=globals.stock.photo_style.url())
      folder.add(placemark)
    return kmz.kmz(folder)

  def make_xc_folder(self, globals):
    def make_row(rte, i, j, percentage=False):
      distance = rte.rtepts[i].coord.distance_to(rte.rtepts[j].coord)
      th = '%s %s %s' % (rte.rtepts[i].name, RIGHTWARDS_ARROW, rte.rtepts[j].name)
      if percentage:
        td = '%.1fkm (%.1f%%)' % (distance / 1000.0, 0.1 * distance / rte.distance)
      else:
        td = '%.1fkm' % (distance / 1000.0)
      return (th, td)
    def make_leg(rte, i, j, name=True, arrow=False, styleUrl=None):
      line_string = kml.LineString(coordinates=[rte.rtepts[k].coord for k in (i, j)], altitudeMode='clampToGround', tessellate=1)
      multi_geometry = kml.MultiGeometry(line_string)
      if name:
        point = kml.Point(coordinates=[rte.rtepts[i].coord.halfway_to(rte.rtepts[j].coord)])
        multi_geometry.add(point)
        name = kml.name('%.1fkm' % (rte.rtepts[i].coord.distance_to(rte.rtepts[j].coord) / 1000.0))
      if arrow:
        bearing = rte.rtepts[j].coord.initial_bearing_to(rte.rtepts[i].coord)
        coordinates = [rte.rtepts[j].coord.coord_at(bearing - math.pi / 12.0, 400.0), rte.rtepts[j].coord, rte.rtepts[j].coord.coord_at(bearing + math.pi / 12.0, 400.0)]
        line_string = kml.LineString(coordinates=coordinates, altitudeMode='clampToGround', tessellate=1)
        multi_geometry.add(line_string)
      if styleUrl is None:
        styleUrl = globals.stock.xc_style.url()
      return kml.Placemark(name, multi_geometry, styleUrl=styleUrl)
    if not self.xc:
      return kmz.kmz()
    folder = kml.Folder(name='Cross country', open=0, styleUrl=globals.stock.radio_folder_style.url())
    folder.add(globals.stock.invisible_none_folder)
    for rank, rte in enumerate(sorted(self.xc.rtes, key=operator.attrgetter('score'), reverse=True)):
      rows = []
      rows.append(('League', self.xc.league))
      rows.append(('Type', rte.name))
      if rte.circuit:
        if len(rte.rtepts) == 4:
          rows.append(make_row(rte, 1, 2))
          rows.append(make_row(rte, 2, 1))
        else:
          for i in xrange(1, len(rte.rtepts) - 2):
            rows.append(make_row(rte, i, i + 1, percentage=True))
          rows.append(make_row(rte, -2, 1, percentage=True))
      else:
        for i in xrange(0, len(rte.rtepts) - 1):
          rows.append(make_row(rte, i, i + 1))
      rows.append(('Distance', '%.1fkm' % rte.distance))
      rows.append(('Multiplier', '%s %.1f points/km' % (MULTIPLICATION_SIGN, rte.multiplier)))
      rows.append(('Score', '<b>%.2f points</b>' % rte.score))
      if rte.circuit:
        rows.append(make_row(rte, -1, 0))
      description = '<table>%s</table>' % ''.join('<tr><th align="right">%s</th><td>%s</td></tr>' % row for row in rows)
      name = '%s (%.1fkm, %.2f points)' % (rte.name, rte.distance, rte.score)
      visibility = 1 if rank == 0 else 0
      rte_folder = kml.Folder(kml.Snippet(), name=name, description=kml.CDATA(description), styleUrl=globals.stock.check_hide_children_style.url(), visibility=visibility)
      for rtept in rte.rtepts:
        coord = self.track.coord_at(rtept.coord.dt)
        point = kml.Point(coordinates=[rtept.coord], altitudeMode=self.altitude_mode, extrude=1)
        placemark = kml.Placemark(point, name=rtept.name, styleUrl=globals.stock.xc_style.url())
        rte_folder.add(placemark)
      if rte.circuit:
        rte_folder.add(make_leg(rte, 0, 1, name=None, arrow=True))
        if len(rte.rtepts) == 4:
          rte_folder.add(make_leg(rte, 1, 2))
        else:
          for i in xrange(1, len(rte.rtepts) - 2):
            rte_folder.add(make_leg(rte, i, i + 1, arrow=True))
          rte_folder.add(make_leg(rte, -2, 1, styleUrl=globals.stock.xc_style2.url()))
        rte_folder.add(make_leg(rte, -2, -1, name=None, arrow=True))
      else:
        for i in xrange(0, len(rte.rtepts) - 1):
          rte_folder.add(make_leg(rte, i, i + 1, arrow=True))
      folder.add(rte_folder)
    return kmz.kmz(folder)

  def make_analysis_folder(self, globals, title, slices, styleUrl):
    if not self.track.elevation_data or len(slices) == 0:
      return kmz.kmz()
    folder = kml.Folder(name=title.capitalize() + "s", styleUrl=globals.stock.check_hide_children_style.url(), visibility=0)
    for sl in slices:
      c = self.track.coords[sl.start].halfway_to(self.track.coords[sl.stop])
      point = kml.Point(coordinates=[c], altitudeMode='absolute')
      line_string = kml.LineString(coordinates=[self.track.coords[sl.start], self.track.coords[sl.stop]], altitudeMode='absolute')
      multi_geometry = kml.MultiGeometry(point, line_string)
      total_dz_positive = total_dz_negative = 0
      peak_climb = util.Bounds(0.0)
      for i in xrange(sl.start, sl.stop):
        dz = self.track.coords[i + 1].ele - self.track.coords[i].ele
        dt = self.track.t[i + 1] - self.track.t[i]
        if dz > 0:
          total_dz_positive += dz
        elif dz < 0:
          total_dz_negative += dz
        peak_climb.update(float(dz) / dt)
      climb = util.Bounds(self.track.climb[sl])
      dz = float(self.track.coords[sl.stop].ele - self.track.coords[sl.start].ele)
      dt = self.track.t[sl.stop] - self.track.t[sl.start]
      dp = self.track.coords[sl.start].distance_to(self.track.coords[sl.stop])
      theta = self.track.coords[sl.start].initial_bearing_to(self.track.coords[sl.stop])
      rows = []
      if title == 'thermal':
        rows.append(('Altitude gain', '%dm' % dz))
        rows.append(('Average climb', '%.1fm/s' % (dz / dt)))
        rows.append(('Maximum climb', '%.1fm/s' % climb.max))
        rows.append(('Peak climb', '%.1fm/s' % peak_climb.max))
        rows.append(('Efficiency', '%d%%' % (100.0 * dz / (dt * climb.max) + 0.5)))
      elif title == 'glide':
        rows.append(('Altitude loss', '%dm' % dz))
        rows.append(('Distance', '%.1fkm' % (dp / 1000.0)))
        rows.append(('Average glide ratio', '%.1f:1' % (-dp / dz) if dz < 0 else '%s:1' % INFINITY))
        rows.append(('Average speed', '%.1fkm/h' % (3.6 * dp / dt)))
      elif title == 'dive':
        rows.append(('Altitude loss', '%dm' % dz))
        rows.append(('Average descent', '%.1fm/s' % (dz / dt)))
        rows.append(('Maximum descent', '%.1fm/s' % climb.min))
        rows.append(('Peak descent', '%.1fm/s' % peak_climb.min))
      rows.append(('Start altitude', '%dm' % self.track.coords[sl.start].ele))
      rows.append(('Finish alitude', '%dm' % self.track.coords[sl.stop].ele))
      rows.append(('Start time', (self.track.coords[sl.start].dt + globals.timezone_offset).strftime('%H:%M:%S')))
      rows.append(('Finish time', (self.track.coords[sl.stop].dt + globals.timezone_offset).strftime('%H:%M:%S')))
      rows.append(('Duration', '%d:%02d' % divmod(self.track.t[sl.stop] - self.track.t[sl.start], 60)))
      rows.append(('Accumulated altitude gain', '%dm' % total_dz_positive))
      rows.append(('Accumulated altitude loss', '%dm' % total_dz_negative))
      if title == 'thermal':
        rows.append(('Drift', '%.1fkm/h %s' % (3.6 * dp / dt, coord.rad_to_compass(theta + math.pi))))
      analysis_table = '<table>%s</table>' % ''.join('<tr><th align="right">%s</th><td>%s</td></tr>' % row for row in rows)
      description = kml.description(kml.CDATA(analysis_table))
      if title == 'thermal':
        name = '%dm at %.1fm/s' % (dz, dz / dt)
      elif title == 'glide':
        ld = '%.1f:1' % (-dp / dz) if dz < 0 else '%s:1' % INFINITY
        name = '%.1fkm at %s, %dkm/h' % (dp / 1000.0, ld, 3.6 * dp / dt + 0.5)
      elif title == 'dive':
        name = '%dm at %.1fm/s' % (-dz, dz / dt)
      placemark = kml.Placemark(multi_geometry, description, kml.Snippet(), name=name, styleUrl=styleUrl)
      folder.add(placemark)
    return kmz.kmz(folder)

  def make_graph_chart(self, globals, values, scale):
    chart = pygooglechart.XYLineChart(globals.graph_width, globals.graph_height, x_range=globals.scales.time.range, y_range=scale.range)
    chart.fill_solid(pygooglechart.Chart.BACKGROUND, 'ffffff00')
    chart.fill_solid(pygooglechart.Chart.CHART, 'ffffffcc')
    axis_index = chart.set_axis_labels(pygooglechart.Axis.BOTTOM, globals.scales.time.labels)
    chart.set_axis_positions(axis_index, globals.scales.time.positions)
    chart.set_axis_style(axis_index, 'ffffff')
    axis_index = chart.set_axis_range(pygooglechart.Axis.LEFT, scale.range[0], scale.range[1])
    chart.set_axis_style(axis_index, 'ffffff')
    chart.set_grid(globals.scales.time.grid_step, scale.grid_step, 2, 2)
    y = [globals.graph_height * (v - scale.range[0]) / (scale.range[1] - scale.range[0]) for v in values]
    indexes = util.incremental_douglas_peucker(self.time_positions, y, 1, 450)
    chart.add_data([self.track.t[i] for i in indexes])
    chart.add_data([values[i] for i in indexes])
    return chart

  def make_graph(self, globals, values, scale):
    icon = kml.Icon(href=kml.CDATA(self.make_graph_chart(globals, values, scale).get_url()))
    overlay_xy = kml.overlayXY(x=0, y=0, xunits='fraction', yunits='fraction')
    screen_xy = kml.screenXY(x=0, y=16, xunits='fraction', yunits='pixels')
    size = kml.size(x=0, y=0, xunits='fraction', yunits='fraction')
    screen_overlay = kml.ScreenOverlay(icon, overlay_xy, screen_xy, size)
    folder = kml.Folder(screen_overlay, name=scale.title.capitalize() + " graph", styleUrl=globals.stock.check_hide_children_style.url(), visibility=0)
    return folder

  def make_time_mark(self, globals, coord, dt, styleUrl):
    point = kml.Point(coordinates=[coord], altitudeMode=self.altitude_mode)
    name = (dt + globals.timezone_offset).strftime('%H:%M')
    return kml.Placemark(point, name=name, styleUrl=styleUrl)

  def make_time_marks_folder(self, globals, step=datetime.timedelta(0, 900)):
    folder = kml.Folder(name='Time marks', styleUrl=globals.stock.check_hide_children_style.url(), visibility=0)
    folder.add(self.make_time_mark(globals, self.track.coords[0], self.track.coords[0].dt, globals.stock.time_mark_styles[0].url()))
    dt = util.datetime_floor(self.track.coords[0].dt, step)
    while dt <= self.track.coords[0].dt:
      dt += step
    while dt < self.track.coords[-1].dt:
      coord = self.track.coord_at(dt)
      if dt.minute == 0:
        style_index = 0
      elif dt.minute == 30:
        style_index = 1
      elif dt.minute == 15 or dt.minute == 45:
        style_index = 2
      else:
        style_index = 3
      folder.add(self.make_time_mark(globals, coord, dt, globals.stock.time_mark_styles[style_index].url()))
      dt += step
    folder.add(self.make_time_mark(globals, self.track.coords[-1], self.track.coords[-1].dt, globals.stock.time_mark_styles[0].url()))
    return folder

  def to_kmz(self, globals):
    self.time_positions = [globals.graph_width * (t - globals.scales.time.range[0]) / (globals.scales.time.range[1] - globals.scales.time.range[0]) for t in self.track.t]
    folder = kmz.kmz(kml.Folder(name=self.track.filename, open=1))
    folder.add(self.make_description(globals))
    folder.add(self.make_snippet(globals))
    folder.add(self.make_track_folder(globals))
    folder.add(self.make_shadow_folder(globals))
    folder.add(self.make_animation(globals))
    folder.add(self.make_photos_folder(globals))
    folder.add(self.make_xc_folder(globals))
    folder.add(self.make_altitude_marks_folder(globals))
    if self.track.elevation_data:
      folder.add(self.make_graph(globals, [c.ele for c in self.track.coords], globals.scales.altitude))
    folder.add(self.make_analysis_folder(globals, 'thermal', self.track.thermals, globals.stock.thermal_style.url()))
    folder.add(self.make_analysis_folder(globals, 'glide', self.track.glides, globals.stock.glide_style.url()))
    folder.add(self.make_analysis_folder(globals, 'dive', self.track.dives, globals.stock.dive_style.url()))
    folder.add(self.make_time_marks_folder(globals))
    return folder

def flights2kmz(flights, timezone_offset=0):
  stock = Stock()
  globals = util.OpenStruct()
  globals.stock = stock
  globals.bounds = util.BoundsSet()
  for flight in flights:
    globals.bounds.update(flight.track.bounds)
  globals.timezone_offset = datetime.timedelta(0, 3600 * timezone_offset)
  globals.scales = util.OpenStruct()
  globals.scales.altitude = scale.Scale(globals.bounds.ele.tuple(), title='altitude', gradient=color.default_gradient)
  globals.altitude_styles = []
  for c in globals.scales.altitude.colors():
    balloon_style = kml.BalloonStyle(text='$[description]')
    icon_style = kml.IconStyle(globals.stock.icons[0], color=c, scale=globals.stock.icon_scales[0])
    label_style = kml.LabelStyle(color=c, scale=globals.stock.label_scales[0])
    globals.altitude_styles.append(kml.Style(balloon_style, icon_style, label_style))
  stock.kmz.add_roots(*globals.altitude_styles)
  globals.scales.climb = scale.ZeroCenteredScale(globals.bounds.climb.tuple(), title='climb', step=0.1, gradient=color.bilinear_gradient)
  globals.scales.speed = scale.Scale(globals.bounds.speed.tuple(), title='ground speed', gradient=color.default_gradient)
  globals.scales.time = scale.TimeScale(globals.bounds.time.tuple(), timezone_offset=globals.timezone_offset)
  if hasattr(globals.bounds, 'tas'):
    globals.scales.tas = scale.Scale(globals.bounds.tas.tuple(), title='air speed', gradient=color.default_gradient)
  globals.graph_width = 600
  globals.graph_height = 300
  result = kmz.kmz()
  result.add_siblings(stock.kmz)
  for flight in flights:
    result.add_siblings(flight.to_kmz(globals))
  return result
