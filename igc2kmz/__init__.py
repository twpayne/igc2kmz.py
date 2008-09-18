import datetime

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


class Globals(object):

  def __init__(self, options, tracks):
    self.stock = Stock()
    self.bounds = util.BoundsSet()
    for track in tracks:
      self.bounds.merge(track.bounds)
    self.timezone_offset = datetime.timedelta(0, 3600 * options.timezone_offset)
    self.altitude_scale = scale.Scale(self.bounds.ele.tuple(), title='altitude', gradient=color.default_gradient)
    self.altitude_styles = []
    for c in self.altitude_scale.colors():
      balloon_style = kml.BalloonStyle(text='$[description]')
      icon_style = kml.IconStyle(kml.Icon.palette(4, 24), scale=0.5)
      label_style = kml.LabelStyle(color=c)
      self.altitude_styles.append(kml.Style(balloon_style, icon_style, label_style))
    self.stock.kmz.add_roots(*self.altitude_styles)
    self.climb_scale = scale.ZeroCenteredScale(self.bounds.climb.tuple(), title='climb', step=0.1, gradient=color.bilinear_gradient)
    self.speed_scale = scale.Scale(self.bounds.speed.tuple(), title='ground speed', gradient=color.default_gradient)
    self.time_scale = scale.TimeScale(self.bounds.time.tuple(), timezone_offset=self.timezone_offset)
    self.progress_scale = scale.Scale((0.0, 1.0), title='progress', gradient=color.default_gradient)
    self.graph_width = 600
    self.graph_height = 300


class Hints(object):

  def __init__(self):
    self.altitude_mode = 'absolute'
    self.color = 'ff0000ff'
    self.width = 2


def make_solid_track(track, hints, style, altitude_mode, extrude=None, **folder_options):
  line_string = kml.LineString(coordinates=track.coords, altitudeMode=altitude_mode)
  if extrude:
    line_string.add(extrude=1)
  placemark = kml.Placemark(style, line_string)
  folder_options['styleUrl'] = hints.globals.stock.check_hide_children_style.url()
  return kmz.kmz(kml.Folder(placemark, **folder_options))

def make_scale_chart(track, hints, scale):
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

def make_colored_track(track, hints, values, scale, altitude_mode, **folder_options):
  folder = kml.Folder(name='Colored by %s' % scale.title, styleUrl=hints.globals.stock.check_hide_children_style.url(), **folder_options)
  styles = [kml.Style(kml.LineStyle(color=color, width=hints.width)) for color in scale.colors()]
  discrete_values = map(scale.discretize, values)
  for start, end in util.runs(discrete_values):
    line_string = kml.LineString(coordinates=track.coords[start:end + 1], altitudeMode=hints.altitude_mode)
    style_url = kml.styleUrl(styles[discrete_values[start]].url())
    placemark = kml.Placemark(style_url, line_string)
    folder.add(placemark)
  icon = kml.Icon(href=kml.CDATA(make_scale_chart(track, hints, scale).get_url()))
  overlay_xy = kml.overlayXY(x=0, y=1, xunits='fraction', yunits='fraction')
  screen_xy = kml.screenXY(x=0, y=1, xunits='fraction', yunits='fraction')
  size = kml.size(x=0, y=0, xunits='fraction', yunits='fraction')
  screen_overlay = kml.ScreenOverlay(icon, overlay_xy, screen_xy, size)
  folder.add(screen_overlay)
  return kmz.kmz(folder).add_roots(*styles)

def make_track_folder(track, hints):
  folder = kmz.kmz(kml.Folder(name='Track', open=1, styleUrl=hints.globals.stock.radio_folder_style.url()))
  folder.add(hints.globals.stock.invisible_none_folder)
  if track.elevation_data:
    folder.add(make_colored_track(track, hints, track.ele, hints.globals.altitude_scale, 'absolute', visibility=0))
    folder.add(make_colored_track(track, hints, track.climb, hints.globals.climb_scale, 'absolute'))
  folder.add(make_colored_track(track, hints, track.speed, hints.globals.speed_scale, hints.altitude_mode, visibility=not track.elevation_data))
  folder.add(make_colored_track(track, hints, track.progress, hints.globals.progress_scale, hints.altitude_mode, visibility=0))
  folder.add(make_colored_track(track, hints, track.thermal, hints.globals.progress_scale, hints.altitude_mode, visibility=0))
  folder.add(make_solid_track(track, hints, kml.Style(kml.LineStyle(color=hints.color, width=hints.width)), hints.altitude_mode, name='Solid color', visibility=0))
  return folder

def make_shadow_folder(track, hints):
  if not track.elevation_data:
    return kmz.kmz()
  folder = kmz.kmz(kml.Folder(name='Shadow', open=1, styleUrl=hints.globals.stock.radio_folder_style.url()))
  folder.add(hints.globals.stock.invisible_none_folder)
  folder.add(make_solid_track(track, hints, kml.Style(kml.LineStyle(color='ff000000', width=1)), 'clampToGround', name='Normal', visibility=1))
  folder.add(make_solid_track(track, hints, kml.Style(kml.LineStyle(color='00000000', width=1), kml.PolyStyle(color='80000000')), 'absolute', True, name='Extrude', visibility=0))
  folder.add(make_solid_track(track, hints, kml.Style(kml.LineStyle(color=hints.color, width=hints.width)), 'clampToGround', name='Solid color', visibility=0))
  return folder

def make_animation(track, hints):
  style = kml.Style(kml.IconStyle(hints.globals.stock.animation_icon, color=hints.color, scale=0.5))
  folder = kml.Folder(style, name='Animation', open=0, styleUrl=hints.globals.stock.check_hide_children_style.url())
  point = kml.Point(coordinates=[track.coords[0]], altitudeMode=hints.altitude_mode)
  timespan = kml.TimeSpan(end=kml.dateTime(track.times[0]))
  placemark = kml.Placemark(point, timespan, styleUrl=style.url())
  folder.add(placemark)
  for i in xrange(1, len(track.coords)):
    point = kml.Point(coordinates=[track.coords[i - 1].halfway_to(track.coords[i])], altitudeMode=hints.altitude_mode)
    timespan = kml.TimeSpan(begin=kml.dateTime(track.times[i - 1]), end=kml.dateTime(track.times[i]))
    placemark = kml.Placemark(point, timespan, styleUrl=style.url())
    folder.add(placemark)
  point = kml.Point(coordinates=[track.coords[-1]], altitudeMode=hints.altitude_mode)
  timespan = kml.TimeSpan(begin=kml.dateTime(track.times[-1]))
  placemark = kml.Placemark(point, timespan, styleUrl=style.url())
  folder.add(placemark)
  return kmz.kmz(folder)

def make_placemark(track, coord, altitudeMode=None, name=None, styleUrl=None):
  point = kml.Point(coordinates=[coord], altitudeMode=altitudeMode)
  placemark = kml.Placemark(point, kml.Snippet(), name=name, styleUrl=styleUrl)
  return placemark

def make_altitude_marks_folder(track, hints):
  if track.elevation_data:
    folder = kml.Folder(name='Altitude marks', styleUrl=hints.globals.stock.check_hide_children_style.url())
    for index in util.salient([c.ele for c in track.coords], 100):
      coord = track.coords[index]
      folder.add(make_placemark(track, coord, altitudeMode='absolute', name='%dm' % coord.ele, styleUrl=hints.globals.altitude_styles[hints.globals.altitude_scale.discretize(coord.ele)].url()))
    return kmz.kmz(folder)
  else:
    return kmz.kmz()

def make_graph_chart(track, hints, values, scale):
  chart = pygooglechart.XYLineChart(hints.globals.graph_width, hints.globals.graph_height, x_range=hints.globals.time_scale.range, y_range=scale.range)
  chart.fill_solid(pygooglechart.Chart.BACKGROUND, 'ffffff00')
  chart.fill_solid(pygooglechart.Chart.CHART, 'ffffffcc')
  axis_index = chart.set_axis_labels(pygooglechart.Axis.BOTTOM, hints.globals.time_scale.labels)
  chart.set_axis_positions(axis_index, hints.globals.time_scale.positions)
  chart.set_axis_style(axis_index, 'ffffff')
  axis_index = chart.set_axis_range(pygooglechart.Axis.LEFT, scale.range[0], scale.range[1])
  chart.set_axis_style(axis_index, 'ffffff')
  chart.set_grid(hints.globals.time_scale.grid_step, scale.grid_step, 2, 2)
  y = [hints.globals.graph_height * (v - scale.range[0]) / (scale.range[1] - scale.range[0]) for v in values]
  indexes = util.incremental_douglas_peucker(hints.time_positions, y, 1, 450)
  chart.add_data([track.coords.t[i] for i in indexes])
  chart.add_data([values[i] for i in indexes])
  return chart

def make_graph(track, hints, values, scale):
  icon = kml.Icon(href=kml.CDATA(make_graph_chart(track, hints, values, scale).get_url()))
  overlay_xy = kml.overlayXY(x=0, y=0, xunits='fraction', yunits='fraction')
  screen_xy = kml.screenXY(x=0, y=16, xunits='fraction', yunits='pixels')
  size = kml.size(x=0, y=0, xunits='fraction', yunits='fraction')
  screen_overlay = kml.ScreenOverlay(icon, overlay_xy, screen_xy, size)
  folder = kml.Folder(screen_overlay, name=scale.title.capitalize(), styleUrl=hints.globals.stock.check_hide_children_style.url(), visibility=0)
  return folder

def make_graphs_folder(track, hints):
  folder = kmz.kmz(kml.Folder(name='Graphs', open=1, styleUrl=hints.globals.stock.radio_folder_style.url()))
  folder.add(hints.globals.stock.visible_none_folder)
  folder.add(make_graph(track, hints, [c.ele for c in track.coords], hints.globals.altitude_scale))
  #folder.add(make_graph(track, hints, track.climb, hints.globals.climb_scale))
  #folder.add(make_graph(track, hints, track.speed, hints.globals.speed_scale))
  return folder

def track2kmz(track, hints):
  folder = kmz.kmz(kml.Folder(name=track.meta.name, open=1))
  rows = []
  if track.meta.pilot_name:
    rows.append(('Pilot name', track.meta.pilot_name))
  if track.meta.glider_type:
    rows.append(('Glider type', track.meta.glider_type))
  if track.meta.glider_id:
    rows.append(('Glider ID', track.meta.glider_id))
  rows.append(('Take-off time', (track.times[0] + hints.globals.timezone_offset).strftime('%H:%M:%S')))
  rows.append(('Landing time', (track.times[-1] + hints.globals.timezone_offset).strftime('%H:%M:%S')))
  hour, seconds = divmod((track.times[-1] - track.times[0]).seconds, 3600)
  minute, second = divmod(seconds, 60)
  rows.append(('Duration', '%d:%02d:%02d' % (hour, minute, second)))
  if track.elevation_data:
    rows.append(('Take-off altitude', '%dm' % track.coords[0].ele))
    rows.append(('Maximum altitude', '%dm' % track.bounds.ele.max))
    rows.append(('Minimum altitude', '%dm' % track.bounds.ele.min))
    rows.append(('Landing altitude', '%dm' % track.coords[-1].ele))
    rows.append(('Total altitude gain', '%dm' % track.total_dz_positive))
    rows.append(('Maximum altitude gain', '%dm' % track.max_dz_positive))
    rows.append(('Maximum climb', '%.1fm/s' % track.bounds.climb.max))
    rows.append(('Maximum sink', '%.1fm/s' % track.bounds.climb.min))
  rows.append(('Maximum speed', '%.1fkm/h' % track.bounds.speed.max))
  folder.add(kml.description(kml.CDATA('<table>%s</table>' % ''.join('<tr><th align="right">%s</th><td>%s</td></tr>' % row for row in rows))))
  snippet = [track.meta.pilot_name, track.meta.glider_type, (track.times[0] + hints.globals.timezone_offset).strftime('%Y-%m-%d')]
  folder.add(kml.Snippet(', '.join(s for s in snippet if s)))
  hints.time_positions = [hints.globals.graph_width * (t - hints.globals.time_scale.range[0]) / (hints.globals.time_scale.range[1] - hints.globals.time_scale.range[0]) for t in track.coords.t]
  folder.add(make_animation(track, hints))
  folder.add(make_track_folder(track, hints))
  folder.add(make_shadow_folder(track, hints))
  folder.add(make_altitude_marks_folder(track, hints))
  folder.add(make_graphs_folder(track, hints))
  return folder
