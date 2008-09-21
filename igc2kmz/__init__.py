import datetime
import math

import pygooglechart

import color
import kml
import kmz
import scale
import util


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
    self.label_scales = [math.sqrt(x) for x in [0.8, 0.6, 0.4]]
    self.radio_folder_style = kml.Style(kml.ListStyle(listItemType='radioFolder'))
    self.kmz.add_roots(self.radio_folder_style)
    self.check_hide_children_style = kml.Style(kml.ListStyle(listItemType='checkHideChildren'))
    self.kmz.add_roots(self.check_hide_children_style)
    balloon_style = kml.BalloonStyle(text=kml.CDATA('<h3>$[name]</h3>$[description]'))
    icon_style = kml.IconStyle(kml.Icon.palette(4, 24), scale=0.5)
    label_style = kml.LabelStyle(color='880033ff', scale=self.label_scales[1])
    line_style = kml.LineStyle(color='880033ff', width=4)
    self.thermal_style = kml.Style(balloon_style, icon_style, label_style, line_style)
    self.kmz.add_roots(self.thermal_style)
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
    self.altitude_mode = 'absolute'
    self.color = 'ff0000ff'
    self.width = 2
    self.pilot_name = track.pilot_name
    self.glider_type = track.glider_type
    self.glider_id = track.glider_id
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
    strings = [self.track.pilot_name, self.track.glider_type, (self.track.bounds.time.min + globals.timezone_offset).strftime('%Y-%m-%d')]
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

  def make_colored_track(self, globals, values, scale, altitude_mode, **folder_options):
    folder = kml.Folder(name='Colored by %s' % scale.title, styleUrl=globals.stock.check_hide_children_style.url(), **folder_options)
    styles = [kml.Style(kml.LineStyle(color=color, width=self.width)) for color in scale.colors()]
    discrete_values = map(scale.discretize, values)
    for start, end in util.runs(discrete_values):
      line_string = kml.LineString(coordinates=self.track.coords[start:end + 1], altitudeMode=self.altitude_mode)
      style_url = kml.styleUrl(styles[discrete_values[start]].url())
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
      folder.add(self.make_colored_track(globals, self.track.ele, globals.altitude_scale, 'absolute', visibility=0))
      folder.add(self.make_colored_track(globals, self.track.climb, globals.climb_scale, 'absolute'))
    folder.add(self.make_colored_track(globals, self.track.speed, globals.speed_scale, self.altitude_mode, visibility=not self.track.elevation_data))
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
    style = kml.Style(kml.IconStyle(globals.stock.animation_icon, color=self.color, scale=0.5))
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
      folder = kml.Folder(name='Altitude marks', styleUrl=globals.stock.check_hide_children_style.url())
      for index in util.salient([c.ele for c in self.track.coords], 100):
        coord = self.track.coords[index]
        folder.add(self.make_placemark(globals, coord, altitudeMode='absolute', name='%dm' % coord.ele, styleUrl=globals.altitude_styles[globals.altitude_scale.discretize(coord.ele)].url()))
      return kmz.kmz(folder)
    else:
      return kmz.kmz()

  def make_climb_chart(self, globals, climb):
    chart = pygooglechart.GoogleOMeterChart(100, 100, x_range=(0, 100 * self.track.bounds.climb.max))
    chart.add_data([100.0 * climb])
    colors = []
    for i in xrange(0, 16 + 1):
      r, g, b, a = globals.climb_scale.color(i * self.track.bounds.climb.max / 16)
      colors.append('%02x%02x%02x' % (255 * r, 255 * g, 255 * b))
    chart.set_colours(colors)
    chart.set_pie_labels(['%.1fm/s' % climb])
    return chart

  def make_thermals_folder(self, globals):
    if self.track.elevation_data:
      folder = kml.Folder(name='Thermals', styleUrl=globals.stock.check_hide_children_style.url(), visibility=0)
      for start, end in self.track.thermals:
        coord = self.track.coords[start].halfway_to(self.track.coords[end + 1])
        point = kml.Point(coordinates=[coord], altitudeMode='absolute')
        line_string = kml.LineString(coordinates=[self.track.coords[start], self.track.coords[end + 1]], altitudeMode='absolute')
        multi_geometry = kml.MultiGeometry(point, line_string)
        total_dz_positive = 0
        total_dz_negative = 0
        max_climb = 0.0
        climb_hist_data = [0] * (int(self.track.bounds.climb.max / 0.5) + 1)
        for i in xrange(start, end):
          dz = self.track.coords[i + 1].ele - self.track.coords[i].ele
          if dz > 0:
            total_dz_positive += dz
          elif dz < 0:
            total_dz_negative += dz
          if self.track.climb[i] > max_climb:
            max_climb = self.track.climb[i]
          climb_hist_data[int(self.track.climb[i] / 0.5)] += 1
        dz = float(self.track.coords[end + 1].ele - self.track.coords[start].ele)
        dt = self.track.t[end + 1] - self.track.t[start]
        dp = self.track.coords[start].distance_to(self.track.coords[end + 1])
        rows = []
        rows.append(('Altitude gain', '%dm' % dz))
        rows.append(('Average climb', '%.1fm/s' % (dz / dt)))
        rows.append(('Maximum climb', '%.1fm/s' % max_climb))
        rows.append(('Start altitude', '%dm' % self.track.coords[start].ele))
        rows.append(('Finish alitude', '%dm' % self.track.coords[end + 1].ele))
        rows.append(('Start time', (self.track.coords[start].dt + globals.timezone_offset).strftime('%H:%M:%S')))
        rows.append(('Finish time', (self.track.coords[end + 1].dt + globals.timezone_offset).strftime('%H:%M:%S')))
        rows.append(('Duration', '%d:%02d' % divmod(self.track.t[end + 1] - self.track.t[start], 60)))
        rows.append(('Accumulated altitude gain', '%dm' % total_dz_positive))
        rows.append(('Accumulated altitude loss', '%dm' % total_dz_negative))
        rows.append(('Drift', '%.1fkm/h' % (3.6 * dp / dt)))
        if dt * max_climb != 0.0: # FIXME
          rows.append(('Efficiency', '%d%%' % (100.0 * dz / (dt * max_climb))))
        analysis_table = '<table>%s</table>' % ''.join('<tr><th align="right">%s</th><td>%s</td></tr>' % row for row in rows)
        #average_climb_chart = self.make_climb_chart(globals, dz / dt)
        #max_climb_chart = self.make_climb_chart(globals, max_climb)
        #climb_hist_chart = pygooglechart.StackedVerticalBarChart(100, 40, y_range=(0, max(climb_hist_data)))
        #climb_hist_chart.set_bar_width(5)
        #climb_hist_chart.add_data(climb_hist_data)
        #rows = []
        #rows.append('%s<center>%s</center>' % (average_climb_chart.get_html_img(), 'Average climb'))
        #rows.append('%s<center>%s</center>' % (max_climb_chart.get_html_img(), 'Maximum climb'))
        #rows.append('%s<center>%s</center>' % (climb_hist_chart.get_html_img(), 'Climb histogram'))
        #graphs_table = '<table>%s</table>' % ''.join('<tr><th>%s</th></tr>' % row for row in rows)
        #description = kml.description(kml.CDATA('<table><tr>%s</tr></table>' % ''.join('<td valign="top">%s<td>' % t for t in [graphs_table, analysis_table])))
        description = kml.description(kml.CDATA(analysis_table))
        name = '%dm at %.1fm/s' % (dz, dz / dt)
        placemark = kml.Placemark(multi_geometry, description, kml.Snippet(), name=name, styleUrl=globals.stock.thermal_style.url())
        folder.add(placemark)
      return kmz.kmz(folder)
    else:
      return kmz.kmz()

  def make_graph_chart(self, globals, values, scale):
    chart = pygooglechart.XYLineChart(globals.graph_width, globals.graph_height, x_range=globals.time_scale.range, y_range=scale.range)
    chart.fill_solid(pygooglechart.Chart.BACKGROUND, 'ffffff00')
    chart.fill_solid(pygooglechart.Chart.CHART, 'ffffffcc')
    axis_index = chart.set_axis_labels(pygooglechart.Axis.BOTTOM, globals.time_scale.labels)
    chart.set_axis_positions(axis_index, globals.time_scale.positions)
    chart.set_axis_style(axis_index, 'ffffff')
    axis_index = chart.set_axis_range(pygooglechart.Axis.LEFT, scale.range[0], scale.range[1])
    chart.set_axis_style(axis_index, 'ffffff')
    chart.set_grid(globals.time_scale.grid_step, scale.grid_step, 2, 2)
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
    folder = kml.Folder(screen_overlay, name=scale.title.capitalize(), styleUrl=globals.stock.check_hide_children_style.url(), visibility=0)
    return folder

  def make_graphs_folder(self, globals):
    folder = kmz.kmz(kml.Folder(name='Graphs', open=1, styleUrl=globals.stock.radio_folder_style.url()))
    folder.add(globals.stock.visible_none_folder)
    folder.add(self.make_graph(globals, [c.ele for c in self.track.coords], globals.altitude_scale))
    #folder.add(self.make_graph(globals, self.track.climb, globals.climb_scale))
    #folder.add(self.make_graph(globals, self.track.speed, globals.speed_scale))
    return folder

  def to_kmz(self, globals):
    self.time_positions = [globals.graph_width * (t - globals.time_scale.range[0]) / (globals.time_scale.range[1] - globals.time_scale.range[0]) for t in self.track.t]
    folder = kmz.kmz(kml.Folder(name=self.track.filename, open=1))
    folder.add(self.make_description(globals))
    folder.add(self.make_snippet(globals))
    folder.add(self.make_animation(globals))
    folder.add(self.make_track_folder(globals))
    folder.add(self.make_shadow_folder(globals))
    folder.add(self.make_altitude_marks_folder(globals))
    folder.add(self.make_thermals_folder(globals))
    folder.add(self.make_graphs_folder(globals))
    return folder

def flights2kmz(flights, timezone_offset=0):
  stock = Stock()
  globals = util.OpenStruct()
  globals.stock = stock
  globals.bounds = util.BoundsSet()
  for flight in flights:
    globals.bounds.update(flight.track.bounds)
  globals.timezone_offset = datetime.timedelta(0, 3600 * timezone_offset)
  globals.altitude_scale = scale.Scale(globals.bounds.ele.tuple(), title='altitude', gradient=color.default_gradient)
  globals.altitude_styles = []
  for c in globals.altitude_scale.colors():
    balloon_style = kml.BalloonStyle(text='$[description]')
    icon_style = kml.IconStyle(kml.Icon.palette(4, 24), scale=0.5)
    label_style = kml.LabelStyle(color=c, scale=globals.stock.label_scales[1])
    globals.altitude_styles.append(kml.Style(balloon_style, icon_style, label_style))
  stock.kmz.add_roots(*globals.altitude_styles)
  globals.climb_scale = scale.ZeroCenteredScale(globals.bounds.climb.tuple(), title='climb', step=0.1, gradient=color.bilinear_gradient)
  globals.speed_scale = scale.Scale(globals.bounds.speed.tuple(), title='ground speed', gradient=color.default_gradient)
  globals.time_scale = scale.TimeScale(globals.bounds.time.tuple(), timezone_offset=globals.timezone_offset)
  globals.graph_width = 600
  globals.graph_height = 300
  result = kmz.kmz()
  result.add_siblings(stock.kmz)
  for flight in flights:
    result.add_siblings(flight.to_kmz(globals))
  return result
