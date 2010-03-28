#   igc2kmz main module
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
from math import pi, sqrt
from itertools import cycle, izip
import operator
import os
import re
import unicodedata
import urlparse

import third_party.pygooglechart as pygooglechart

from color import bilinear_gradient, default_gradient
from coord import rad_to_cardinal
import kml
import kmz
from scale import Scale, TimeScale, ZeroCenteredScale
import util


if 0:
    RIGHTWARDS_ARROW = unicodedata.lookup('RIGHTWARDS ARROW').encode('utf_8')
    INFINITY = unicodedata.lookup('INFINITY').encode('utf_8')
    MULTIPLICATION_SIGN = unicodedata.lookup('MULTIPLICATION SIGN').encode('utf_8')
    UP_TACK = unicodedata.lookup('UP TACK').encode('utf_8')
else:
    RIGHTWARDS_ARROW = '->'
    INFINITY = 'inf'
    MULTIPLICATION_SIGN = 'x'
    UP_TACK = 'n/a'

BASE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))


def make_table(rows, bgcolors='#dddddd #ffffff'.split()):
    trs = ('<tr bgcolor="%s"><th align="right">%s</th><td>%s</td></tr>'
           % (bgcolor, row[0], row[1])
           for row, bgcolor in izip(rows, cycle(bgcolors)))
    return '<table cellpadding="1" cellspacing="1">%s</table>' % ''.join(trs)


class Stock(object):

    def make_none_folder(self, visibility):
        icon = kml.Icon(href=self.pixel_url)
        overlay_xy = kml.overlayXY(x=0, xunits='fraction',
                                   y=0, yunits='fraction')
        screen_xy = kml.screenXY(x=0, xunits='fraction', y=0, yunits='fraction')
        size = kml.size(x=0, xunits='fraction', y=0, yunits='fraction')
        screen_overlay = kml.ScreenOverlay(icon, overlay_xy, screen_xy, size,
                                           visibility=visibility)
        style_url = self.check_hide_children_style.url()
        return kml.Folder(screen_overlay, name='None', styleUrl=style_url)

    def make_analysis_style(self, color, bgcolors, rows):
        text = '<h3>$[name]</h3>$[description]' + make_table(rows, bgcolors)
        bg_color = 'ff' + ''.join(reversed(re.findall(r'..', bgcolors[1][1:])))
        balloon_style = kml.BalloonStyle(text=kml.CDATA(text), bgColor=bg_color)
        icon_style = kml.IconStyle(self.icons[0], color=color,
                                   scale=self.icon_scales[0])
        label_style = kml.LabelStyle(color=color, scale=self.label_scales[0])
        line_style = kml.LineStyle(color=color, width=4)
        return kml.Style(balloon_style, icon_style, label_style, line_style)

    def __init__(self):
        self.kmz = kmz.kmz()
        #
        self.icon_scales = [sqrt(x) for x in [0.6, 0.5, 0.4, 0.3]]
        self.icons = [kml.Icon.palette(4, i) for i in [25, 25, 24, 24]]
        self.label_scales = [sqrt(x) for x in [0.6, 0.5, 0.4, 0.3]]
        #
        list_style = kml.ListStyle(listItemType='radioFolder')
        self.radio_folder_style = kml.Style(list_style)
        self.kmz.add_roots(self.radio_folder_style)
        #
        list_style = kml.ListStyle(listItemType='checkHideChildren')
        self.check_hide_children_style = kml.Style(list_style)
        self.kmz.add_roots(self.check_hide_children_style)
        #
        bgcolors = '#ffcccc #ffdddd'.split()
        rows = [
                ['Altitude gain', '$[altitude_change]m'],
                ['Average climb', '$[average_climb]m/s'],
                ['Maximum climb', '$[maximum_climb]m/s'],
                ['Peak climb', '$[peak_climb]m/s'],
                ['Efficiency', '$[efficiency]%'],
                ['Start altitude', '$[start_altitude]m'],
                ['Finish altitude', '$[finish_altitude]m'],
                ['Start time', '$[start_time]'],
                ['Finish time', '$[finish_time]'],
                ['Duration', '$[duration]'],
                ['Accumulated altitude gain', '$[accumulated_altitude_gain]m'],
                ['Accumulated altitude loss', '$[accumulated_altitude_loss]m'],
                ['Drift', '$[average_speed]km/h $[drift_direction]'],
                ]
        self.thermal_style = self.make_analysis_style('cc3333ff', bgcolors,
                                                      rows)
        self.kmz.add_roots(self.thermal_style)
        bgcolors = '#ccccff #ddddff'.split()
        rows = [
                ['Altitude change', '$[altitude_change]m'],
                ['Average descent', '$[average_climb]m/s'],
                ['Maximum descent', '$[maximum_descent]m/s'],
                ['Peak descent', '$[peak_descent]m/s'],
                ['Start altitude', '$[start_altitude]m'],
                ['Finish altitude', '$[finish_altitude]m'],
                ['Start time', '$[start_time]'],
                ['Finish time', '$[finish_time]'],
                ['Duration', '$[duration]'],
                ['Accumulated altitude gain', '$[accumulated_altitude_gain]m'],
                ['Accumulated altitude loss', '$[accumulated_altitude_loss]m'],
                ]
        self.dive_style = self.make_analysis_style('ccff3333', bgcolors, rows)
        bgcolors = '#ccffcc #ddffdd'.split()
        rows = [
                ['Altitude change', '$[altitude_change]m'],
                ['Average descent', '$[average_climb]m/s'],
                ['Distance', '$[distance]km'],
                ['Average glide ratio', '$[average_ld]:1'],
                ['Average speed', '$[average_speed]km/h'],
                ['Start altitude', '$[start_altitude]m'],
                ['Finish altitude', '$[finish_altitude]m'],
                ['Start time', '$[start_time]'],
                ['Finish time', '$[finish_time]'],
                ['Duration', '$[duration]'],
                ['Accumulated altitude gain', '$[accumulated_altitude_gain]m'],
                ['Accumulated altitude loss', '$[accumulated_altitude_loss]m'],
                ]
        self.kmz.add_roots(self.dive_style)
        self.glide_style = self.make_analysis_style('cc33ff33', bgcolors, rows)
        self.kmz.add_roots(self.glide_style)
        #
        self.time_mark_styles = []
        for i in xrange(0, len(self.icons)):
            icon_style = kml.IconStyle(self.icons[i], scale=self.icon_scales[i])
            label_style = kml.LabelStyle(color='cc33ffff',
                                         scale=self.label_scales[i])
            self.time_mark_styles.append(kml.Style(icon_style, label_style))
        self.kmz.add_roots(*self.time_mark_styles)
        #
        balloon_style = kml.BalloonStyle(text=kml.CDATA('$[description]'))
        icon_style = kml.IconStyle(kml.Icon.palette(4, 46),
                                   scale=self.icon_scales[0])
        label_style = kml.LabelStyle(scale=self.label_scales[0])
        self.photo_style = kml.Style(balloon_style, icon_style, label_style)
        self.kmz.add_roots(self.photo_style)
        #
        text = kml.text(kml.CDATA('<h3>$[name]</h3>$[description]'))
        balloon_style = kml.BalloonStyle(text)
        icon_style = kml.IconStyle(self.icons[0], color='ccff33ff',
                                   scale=self.icon_scales[0])
        label_style = kml.LabelStyle(color='ccff33ff',
                                     scale=self.label_scales[0])
        line_style = kml.LineStyle(color='ccff33ff', width=2)
        self.xc_style = kml.Style(balloon_style, icon_style, label_style,
                                  line_style)
        self.kmz.add_roots(self.xc_style)
        #
        text = kml.text(kml.CDATA('<h3>$[name]</h3>$[description]'))
        balloon_style = kml.BalloonStyle(text)
        icon_style = kml.IconStyle(self.icons[0], color='ccff33ff',
                                   scale=self.icon_scales[0])
        label_style = kml.LabelStyle(color='ccff33ff',
                                     scale=self.label_scales[0])
        line_style = kml.LineStyle(color='ccff33ff')
        self.xc_style2 = kml.Style(balloon_style, icon_style, label_style,
                                   line_style)
        self.kmz.add_roots(self.xc_style2)
        #
        self.pixel_url = os.path.join('images', 'pixel.png')
        pixel = open(os.path.join(BASE_DIR, self.pixel_url)).read()
        self.kmz.add_files({self.pixel_url: pixel})
        #
        self.visible_none_folder = self.make_none_folder(1)
        self.invisible_none_folder = self.make_none_folder(0)
        #
        animation_icon_url = os.path.join('images', 'paraglider.png')
        self.animation_icon = kml.Icon(href=animation_icon_url)
        animation_icon = open(os.path.join(BASE_DIR, animation_icon_url)).read()
        files = {animation_icon_url: animation_icon}
        self.kmz.add_files(files)


class Flight(object):

    def __init__(self, track, **kwargs):
        self.track = track
        if self.track.elevation_data:
            self.altitude_mode = 'absolute'
        else:
            self.altitude_mode = 'clampToGround'
        self.color = 'ff0000ff'
        self.width = 2
        self.pilot_name = track.pilot_name
        self.glider_type = track.glider_type
        self.glider_id = track.glider_id
        self.photos = []
        self.url = None
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
        take_off_time = self.track.bounds.time.min + globals.tz_offset
        rows.append(('Take-off time', take_off_time.strftime('%H:%M:%S')))
        landing_time = self.track.bounds.time.max + globals.tz_offset
        rows.append(('Landing time', landing_time.strftime('%H:%M:%S')))
        duration = (self.track.bounds.time.max 
                    - self.track.bounds.time.min).seconds
        hour, seconds = divmod(duration, 3600)
        minute, second = divmod(seconds, 60)
        rows.append(('Duration', '%dh %02dm %02ds' % (hour, minute, second)))
        if self.track.elevation_data:
            rows.append(('Take-off altitude', '%dm' % self.track.coords[0].ele))
            rows.append(('Maximum altitude', '%dm' % self.track.bounds.ele.max))
            rows.append(('Minimum altitude', '%dm' % self.track.bounds.ele.min))
            rows.append(('Landing altitude', '%dm' % self.track.coords[-1].ele))
            rows.append(('Total altitude gain',
                         '%dm' % self.track.total_dz_positive))
            rows.append(('Maximum altitude gain',
                         '%dm' % self.track.max_dz_positive))
            rows.append(('Maximum climb',
                         '%.1fm/s' % self.track.bounds.climb.max))
            rows.append(('Maximum sink',
                         '%.1fm/s' % self.track.bounds.climb.min))
        rows.append(('Maximum speed', '%.1fkm/h' % self.track.bounds.speed.max))
        if self.url:
            components = urlparse.urlparse(self.url)
            html = '<a href="%s">%s</a>' % (self.url, components.netloc)
            rows.append(('Flight URL', html))
        table = make_table(rows)
        return kmz.kmz(kml.description(kml.CDATA(table)))

    def make_snippet(self, globals):
        if self.xc:
            route = sorted(self.xc.routes,
                           key=operator.attrgetter('score'),
                           reverse=True)[0]
            xc = '%.1fkm %s' % (route.distance, route.name)
        else:
            xc = None
        date = self.track.bounds.time.min + globals.tz_offset
        strings = [self.pilot_name, xc, date.strftime('%Y-%m-%d')]
        snippet = kml.Snippet(', '.join(s for s in strings if s))
        return kmz.kmz(snippet)

    def make_solid_track(self, globals, style, altitude_mode, extrude=None,
                         **folder_options):
        line_string = kml.LineString(coordinates=self.track.coords,
                                     altitudeMode=altitude_mode)
        if extrude:
            line_string.add(extrude=1)
        placemark = kml.Placemark(style, line_string)
        style_url = globals.stock.check_hide_children_style.url()
        folder_options['styleUrl'] = style_url
        return kmz.kmz(kml.Folder(placemark, **folder_options))

    def make_scale_chart(self, globals, scale):
        chart = pygooglechart.SimpleLineChart(40, 200, x_range=(0, 1),
                                              y_range=scale.range)
        chart.fill_solid(pygooglechart.Chart.BACKGROUND, 'ffffff00')
        chart.fill_solid(pygooglechart.Chart.CHART, 'ffffffcc')
        for i in xrange(0, 32 + 1):
            y = i * (scale.range[1] - scale.range[0]) / 32 + scale.range[0]
            chart.add_data([y, y])
            chart.set_line_style(i, 0)
        for i in xrange(0, 32):
            r, g, b, a = scale.color((i * (scale.range[1] - scale.range[0])
                                      + 0.5) / 32 + scale.range[0])
            color = '%02x%02x%02x' % (255 * r, 255 * g, 255 * b)
            chart.add_fill_range(color, i, i + 1)
        axis_index = chart.set_axis_range(pygooglechart.Axis.RIGHT,
                                          scale.range[0], scale.range[1])
        chart.set_axis_style(axis_index, 'ffffff')
        return chart

    def make_colored_track(self, globals, values, scale, altitude_mode,
                           scale_chart=True, **folder_options):
        style_url = globals.stock.check_hide_children_style.url()
        folder = kml.Folder(name='Colored by %s' % scale.title,
                            styleUrl=style_url, **folder_options)
        styles = [kml.Style(kml.LineStyle(color=color, width=self.width))
                  for color in scale.colors()]
        discrete_values = map(scale.discretize, values)
        for sl in util.runs(discrete_values):
            coordinates = self.track.coords[sl.start:sl.stop + 1]
            line_string = kml.LineString(coordinates=coordinates,
                                         altitudeMode=self.altitude_mode)
            style_url = kml.styleUrl(styles[discrete_values[sl.start]].url())
            placemark = kml.Placemark(style_url, line_string)
            folder.add(placemark)
        if scale_chart:
            href = self.make_scale_chart(globals, scale).get_url()
            icon = kml.Icon(href=kml.CDATA(href))
            overlay_xy = kml.overlayXY(x=0, xunits='fraction',
                                       y=1, yunits='fraction')
            screen_xy = kml.screenXY(x=0, xunits='fraction',
                                     y=1, yunits='fraction')
            size = kml.size(x=0, xunits='fraction', y=0, yunits='fraction')
            screen_overlay = kml.ScreenOverlay(icon, overlay_xy, screen_xy, size)
            folder.add(screen_overlay)
        return kmz.kmz(folder).add_roots(*styles)

    def make_track_folder(self, globals):
        style_url = globals.stock.radio_folder_style.url()
        folder = kmz.kmz(kml.Folder(name='Track', open=1, styleUrl=style_url))
        folder.add(globals.stock.invisible_none_folder)
        if self.track.elevation_data:
            folder.add(self.make_colored_track(globals, self.track.climb,
                                               globals.scales.climb,
                                               'absolute'))
            folder.add(self.make_colored_track(globals, self.track.ele,
                                               globals.scales.altitude,
                                               'absolute', visibility=0))
        visibility = not self.track.elevation_data
        folder.add(self.make_colored_track(globals, self.track.speed,
                                           globals.scales.speed,
                                           self.altitude_mode,
                                           visibility=visibility))
        if hasattr(self.track, 'tas'):
            folder.add(self.make_colored_track(globals, self.track.tas,
                                               globals.scales.tas,
                                               self.altitude_mode,
                                               visibility=0))
        folder.add(self.make_colored_track(globals, self.track.t,
                                           globals.scales.t, self.altitude_mode,
                                           scale_chart=False,
                                           visibility=visibility))
        style = kml.Style(kml.LineStyle(color=self.color, width=self.width))
        folder.add(self.make_solid_track(globals, style, self.altitude_mode,
                                         name='Solid color', visibility=0))
        return folder

    def make_shadow_folder(self, globals):
        if not self.track.elevation_data:
            return kmz.kmz()
        style_url = globals.stock.radio_folder_style.url()
        folder = kmz.kmz(kml.Folder(name='Shadow', open=0, styleUrl=style_url))
        folder.add(globals.stock.invisible_none_folder)
        style = kml.Style(kml.LineStyle(color='ff000000', width=1))
        folder.add(self.make_solid_track(globals, style, 'clampToGround',
                                         name='Normal'))
        line_style = kml.LineStyle(color='00000000', width=1)
        poly_style = kml.PolyStyle(color='80000000')
        style = kml.Style(line_style, poly_style)
        folder.add(self.make_solid_track(globals, style, 'absolute', True,
                                         name='Extrude', visibility=0))
        style = kml.Style(kml.LineStyle(color=self.color, width=self.width))
        folder.add(self.make_solid_track(globals, style, 'clampToGround',
                                         name='Solid color', visibility=0))
        return folder

    def make_animation(self, globals):
        icon_style = kml.IconStyle(globals.stock.animation_icon,
                                   color=self.color,
                                   scale=globals.stock.icon_scales[0])
        list_style = kml.ListStyle(listItemType='checkHideChildren')
        style = kml.Style(icon_style, list_style)
        folder = kml.Folder(style, name='Animation')
        point = kml.Point(coordinates=[self.track.coords[0]],
                          altitudeMode=self.altitude_mode)
        timespan = kml.TimeSpan(end=kml.dateTime(self.track.coords[0].dt))
        placemark = kml.Placemark(point, timespan, styleUrl=style.url())
        folder.add(placemark)
        for i in xrange(1, len(self.track.coords)):
            coord = self.track.coords[i - 1].halfway_to(self.track.coords[i])
            point = kml.Point(coordinates=[coord],
                              altitudeMode=self.altitude_mode)
            begin = kml.dateTime(self.track.coords[i - 1].dt)
            end = kml.dateTime(self.track.coords[i].dt)
            timespan = kml.TimeSpan(begin=begin, end=end)
            placemark = kml.Placemark(point, timespan, styleUrl=style.url())
            folder.add(placemark)
        point = kml.Point(coordinates=[self.track.coords[-1]],
                          altitudeMode=self.altitude_mode)
        timespan = kml.TimeSpan(begin=kml.dateTime(self.track.coords[-1].dt))
        placemark = kml.Placemark(point, timespan, styleUrl=style.url())
        folder.add(placemark)
        return kmz.kmz(folder)

    def make_tour_folder(self, globals):
        style_url = globals.stock.check_hide_children_style.url()
        folder = kmz.kmz(kml.Folder(name='Tour', styleUrl=style_url))
        dt = self.track.coords[0].dt
        delta = datetime.timedelta(seconds=15 * 60)
        coords = []
        while dt < self.track.coords[-1].dt:
            coords.append(self.track.coord_at(dt))
            dt += delta
        for i in xrange(0, len(coords)):
            j = (i + 1) % len(coords)
            point = kml.Point(coordinates=[coords[i]], altitudeMode=self.altitude_mode)
            heading = coords[i].initial_bearing_to_deg(coords[j])
            camera = kml.Camera(altitude=coords[i].ele, heading=heading,
                                latitude=coords[i].lat_deg,
                                longitude=coords[i].lon_deg, tilt=75)
            placemark = kml.Placemark(point, camera)
            folder.add(placemark)
        return folder

    def make_placemark(self, globals, coord, altitudeMode=None, name=None,
                       style_url=None):
        point = kml.Point(coordinates=[coord], altitudeMode=altitudeMode)
        return kml.Placemark(point, name=name, Snippet=None, styleUrl=style_url)

    def make_altitude_marks_folder(self, globals):
        if not self.track.elevation_data:
            return kmz.kmz()
        style_url = globals.stock.check_hide_children_style.url()
        folder = kml.Folder(name='Altitude marks', styleUrl=style_url,
                            visibility=0)
        for index, j in util.salient2([c.ele for c in self.track.coords],
                                      [100, 50, 10]):
            coord = self.track.coords[index]
            i = globals.scales.altitude.discretize(coord.ele)
            style_url = globals.altitude_styles[j][i].url()
            folder.add(self.make_placemark(globals, coord,
                                           altitudeMode='absolute',
                                           name='%dm' % coord.ele,
                                           style_url=style_url))
        return kmz.kmz(folder)

    def make_photos_folder(self, globals):
        if not len(self.photos):
            return kmz.kmz()
        folder = kml.Folder(name='Photos', open=0)
        for photo in sorted(self.photos, key=operator.attrgetter('dt')):
            if photo.coord:
                coord = photo.coord
                if photo.elevation_data:
                    altitude_mode = 'absolute'
                else:
                    altitude_mode = 'clampToGround'
            else:
                coord = self.track.coord_at(photo.dt - globals.tz_offset)
                altitude_mode = self.altitude_mode
            point = kml.Point(coordinates=[coord], altitudeMode=altitude_mode)
            if photo.description:
                title = '%s: %s' % (photo.name, photo.description)
            else:
                title = photo.name
            description = '<h3>%s</h3>%s' % (title, photo.to_html_img())
            style_url = globals.stock.photo_style.url()
            placemark = kml.Placemark(point, name=photo.name,
                                      description=kml.CDATA(description),
                                      Snippet=kml.CDATA(description),
                                      styleUrl=style_url)
            folder.add(placemark)
        return kmz.kmz(folder)

    def make_xc_folder(self, globals):
        def make_row(route, i, j, percentage=False):
            distance = route.tps[i].coord.distance_to(route.tps[j].coord)
            th = '%s %s %s' \
                 % (route.tps[i].name, RIGHTWARDS_ARROW, route.tps[j].name)
            if percentage:
                td = '%.1fkm (%.1f%%)' \
                     % (distance / 1000.0, 0.1 * distance / route.distance)
            else:
                td = '%.1fkm' % (distance / 1000.0)
            return (th, td)
        def make_leg(route, i, j, name=True, arrow=False, style_url=None):
            coord0 = route.tps[i].coord
            coord1 = route.tps[j].coord
            line_string = kml.LineString(coordinates=[coord0, coord1],
                                         altitudeMode='clampToGround',
                                         tessellate=1)
            multi_geometry = kml.MultiGeometry(line_string)
            if name:
                point = kml.Point(coordinates=[coord0.halfway_to(coord1)])
                multi_geometry.add(point)
                distance = coord0.distance_to(coord1)
                name = kml.name('%.1fkm' % (distance / 1000.0))
            if arrow:
                bearing = coord1.initial_bearing_to(coord0)
                coordinates = [coord1.coord_at(bearing - pi / 12.0, 400.0),
                               coord1,
                               coord1.coord_at(bearing + pi / 12.0, 400.0)]
                line_string = kml.LineString(coordinates=coordinates,
                                             altitudeMode='clampToGround',
                                             tessellate=1)
                multi_geometry.add(line_string)
            if style_url is None:
                style_url = globals.stock.xc_style.url()
            return kml.Placemark(name, multi_geometry, styleUrl=style_url)
        if not self.xc:
            return kmz.kmz()
        style_url = globals.stock.radio_folder_style.url()
        folder = kml.Folder(name='Cross country', open=0, styleUrl=style_url)
        folder.add(globals.stock.invisible_none_folder)
        for rank, route in enumerate(sorted(self.xc.routes,
                                            key=operator.attrgetter('score'),
                                            reverse=True)):
            rows = []
            rows.append(('League', route.league))
            rows.append(('Type', route.name[0].upper() + route.name[1:]))
            if route.circuit:
                if len(route.tps) == 4:
                    rows.append(make_row(route, 1, 2))
                    rows.append(make_row(route, 2, 1))
                else:
                    for i in xrange(1, len(route.tps) - 2):
                        rows.append(make_row(route, i, i + 1, percentage=True))
                    rows.append(make_row(route, -2, 1, percentage=True))
            else:
                for i in xrange(0, len(route.tps) - 1):
                    rows.append(make_row(route, i, i + 1))
            rows.append(('Distance', '%.1fkm' % route.distance))
            rows.append(('Multiplier',
                         '%s %.2f points/km' % (MULTIPLICATION_SIGN,
                                                route.multiplier)))
            rows.append(('Score', '<b>%.2f points</b>' % route.score))
            speed = 3600.0 * route.distance \
                    / (route.tps[-1].coord.dt - route.tps[0].coord.dt).seconds
            rows.append(('Average speed', '%.1fkm/h' % speed))
            if route.circuit:
                rows.append(make_row(route, -1, 0))
            table = make_table(rows)
            name = '%.1fkm %s (%.2f points)' \
                   % (route.distance, route.name, route.score)
            visibility = 1 if rank == 0 else 0
            style_url = globals.stock.check_hide_children_style.url()
            route_folder = kml.Folder(name=name, description=kml.CDATA(table),
                                      Snippet=None, styleUrl=style_url,
                                      visibility=visibility)
            for tp in route.tps:
                coord = self.track.coord_at(tp.coord.dt)
                point = kml.Point(coordinates=[coord],
                                  altitudeMode=self.altitude_mode, extrude=1)
                style_url = globals.stock.xc_style.url()
                placemark = kml.Placemark(point, name=tp.name,
                                          styleUrl=style_url)
                route_folder.add(placemark)
            if route.circuit:
                route_folder.add(make_leg(route, 0, 1, name=None, arrow=True))
                if len(route.tps) == 4:
                    route_folder.add(make_leg(route, 1, 2))
                else:
                    for i in xrange(1, len(route.tps) - 2):
                        route_folder.add(make_leg(route, i, i + 1, arrow=True))
                    style_url = globals.stock.xc_style2.url()
                    route_folder.add(make_leg(route, -2, 1,
                                              style_url=style_url))
                route_folder.add(make_leg(route, -2, -1, name=None, arrow=True))
            else:
                for i in xrange(0, len(route.tps) - 1):
                    route_folder.add(make_leg(route, i, i + 1, arrow=True))
            folder.add(route_folder)
        return kmz.kmz(folder)

    def make_analysis_folder(self, globals, title, slices, style_url):
        if not self.track.elevation_data or len(slices) == 0:
            return kmz.kmz()
        folder_style_url = globals.stock.check_hide_children_style.url()
        folder = kml.Folder(name=title.capitalize() + "s",
                            styleUrl=folder_style_url, visibility=0)
        for sl in slices:
            coord0 = self.track.coords[sl.start]
            coord1 = self.track.coords[sl.stop]
            coord = coord0.halfway_to(coord1)
            point = kml.Point(coordinates=[coord], altitudeMode='absolute')
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
            dz = float(self.track.coords[sl.stop].ele
                       - self.track.coords[sl.start].ele)
            dt = self.track.t[sl.stop] - self.track.t[sl.start]
            dp = coord0.distance_to(coord1)
            theta = coord0.initial_bearing_to(coord1)
            dict = {}
            dict['altitude_change'] = int(round(dz))
            dict['average_climb'] = round(dz / dt, 1)
            dict['maximum_climb'] = round(climb.max, 1)
            dict['peak_climb'] = round(peak_climb.max, 1)
            divisor = dt * climb.max
            if divisor == 0:
                dict['efficiency'] = UP_TACK
            else:
                dict['efficiency'] = int(round(100.0 * dz / divisor))
            dict['distance'] = round(dp / 1000.0, 1)
            average_ld = round(-dp / dz, 1) if dz < 0 else INFINITY
            dict['average_ld'] = average_ld
            dict['average_speed'] = round(3.6 * dp / dt, 1)
            dict['maximum_descent'] = round(climb.min, 1)
            dict['peak_descent'] = round(peak_climb.min, 1)
            dict['start_altitude'] = coord0.ele
            dict['finish_altitude'] = coord1.ele
            start_time = coord0.dt + globals.tz_offset
            dict['start_time'] = start_time.strftime('%H:%M:%S')
            stop_time = coord1.dt + globals.tz_offset
            dict['finish_time'] = stop_time.strftime('%H:%M:%S')
            duration = self.track.t[sl.stop] - self.track.t[sl.start]
            dict['duration'] = '%dm %02ds' % divmod(duration, 60)
            dict['accumulated_altitude_gain'] = total_dz_positive
            dict['accumulated_altitude_loss'] = total_dz_negative
            dict['drift_direction'] = rad_to_cardinal(theta + pi)
            extended_data = kml.ExtendedData.dict(dict)
            if title == 'thermal':
                name = '%dm at %.1fm/s' % (dz, dz / dt)
            elif title == 'glide':
                name = '%.1fkm at %s:1, %dkm/h' \
                       % (dp / 1000.0, average_ld, round(3.6 * dp / dt))
            elif title == 'dive':
                name = '%dm at %.1fm/s' % (-dz, dz / dt)
            placemark = kml.Placemark(point, extended_data, name=name,
                                      Snippet=None, styleUrl=style_url)
            folder.add(placemark)
            line_string = kml.LineString(coordinates=[coord0, coord1],
                                         altitudeMode='absolute')
            placemark = kml.Placemark(line_string, styleUrl=style_url)
            folder.add(placemark)
        return kmz.kmz(folder)

    def make_graph_chart(self, globals, values, scale):
        chart = pygooglechart.XYLineChart(globals.graph_width,
                                          globals.graph_height,
                                          x_range=globals.scales.time.range,
                                          y_range=scale.range)
        chart.fill_solid(pygooglechart.Chart.BACKGROUND, 'ffffff00')
        chart.fill_solid(pygooglechart.Chart.CHART, 'ffffffcc')
        axis_index = chart.set_axis_labels(pygooglechart.Axis.BOTTOM,
                                           globals.scales.time.labels)
        chart.set_axis_positions(axis_index, globals.scales.time.positions)
        chart.set_axis_style(axis_index, 'ffffff')
        axis_index = chart.set_axis_range(pygooglechart.Axis.LEFT,
                                          scale.range[0], scale.range[1])
        chart.set_axis_style(axis_index, 'ffffff')
        chart.set_grid(globals.scales.time.grid_step, scale.grid_step, 2, 2)
        y = [globals.graph_height * (v - scale.range[0])
             / (scale.range[1] - scale.range[0])
             for v in values]
        indexes = util.incr_douglas_peucker(self.time_positions, y, 1, 450)
        chart.add_data([self.track.t[i] for i in indexes])
        chart.add_data([values[i] for i in indexes])
        return chart

    def make_graph(self, globals, values, scale):
        href = self.make_graph_chart(globals, values, scale).get_url()
        icon = kml.Icon(href=kml.CDATA(href))
        overlay_xy = kml.overlayXY(x=0, xunits='fraction',
                                   y=0, yunits='fraction')
        screen_xy = kml.screenXY(x=0, xunits='fraction', y=16, yunits='pixels')
        size = kml.size(x=0, xunits='fraction', y=0, yunits='fraction')
        screen_overlay = kml.ScreenOverlay(icon, overlay_xy, screen_xy, size)
        name = scale.title.capitalize() + " graph"
        style_url = globals.stock.check_hide_children_style.url()
        folder = kml.Folder(screen_overlay, name=name, styleUrl=style_url,
                            visibility=0)
        return folder

    def make_time_mark(self, globals, coord, dt, style_url):
        point = kml.Point(coordinates=[coord], altitudeMode=self.altitude_mode)
        name = (dt + globals.tz_offset).strftime('%H:%M')
        return kml.Placemark(point, name=name, styleUrl=style_url)

    def make_time_marks_folder(self, globals, step=datetime.timedelta(0, 300)):
        style_url = globals.stock.check_hide_children_style.url()
        folder = kml.Folder(name='Time marks', styleUrl=style_url, visibility=0)
        coord = self.track.coords[0]
        style_url = globals.stock.time_mark_styles[0].url()
        folder.add(self.make_time_mark(globals, coord, coord.dt, style_url))
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
            style_url = globals.stock.time_mark_styles[style_index].url()
            folder.add(self.make_time_mark(globals, coord, dt, style_url))
            dt += step
        coord = self.track.coords[-1]
        style_url = globals.stock.time_mark_styles[0].url()
        folder.add(self.make_time_mark(globals, coord, coord.dt, style_url))
        return folder

    def to_kmz(self, globals):
        self.time_positions = [globals.graph_width
                               * (t - globals.scales.time.range[0])
                               / (globals.scales.time.range[1]
                                  - globals.scales.time.range[0])
                               for t in self.track.t]
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
            eles = [c.ele for c in self.track.coords]
            folder.add(self.make_graph(globals, eles, globals.scales.altitude))
        folder.add(self.make_analysis_folder(globals, 'thermal',
                                             self.track.thermals,
                                             globals.stock.thermal_style.url()))
        folder.add(self.make_analysis_folder(globals, 'glide',
                                             self.track.glides,
                                             globals.stock.glide_style.url()))
        folder.add(self.make_analysis_folder(globals, 'dive',
                                             self.track.dives,
                                             globals.stock.dive_style.url()))
        folder.add(self.make_time_marks_folder(globals))
        return folder


def make_task_folder(globals, task):
    name = task.name or 'Task'
    rows = []
    tp0 = None
    total = 0.0
    count = -1
    for sl in util.runs([tp.name for tp in task.tps]):
        if tp0 is None:
            tp0 = task.tps[sl.start]
            continue
        tp1 = task.tps[sl.stop - 1]
        distance = tp0.coord.distance_to(tp1.coord)
        th = '%s %s %s' % (tp0.name, RIGHTWARDS_ARROW, tp1.name)
        td = '%.1fkm' % (distance / 1000.0)
        rows.append((th, td))
        total += distance
        count += 1
        tp0 = tp1
    rows.append(('Total', '%.1fkm' % (total / 1000.0)))
    table = make_table(rows)
    snippet = '%.1fkm via %d turnpoints' % (total / 1000.0, count)
    style_url = globals.stock.check_hide_children_style.url()
    folder = kml.Folder(name=name, description=kml.CDATA(table),
                        Snippet=snippet, styleUrl=style_url)
    style_url = globals.stock.xc_style.url()
    done = set()
    for tp in task.tps:
        key = tp.name
        if key in done:
            continue
        else:
            done.add(key)
        point = kml.Point(coordinates=[tp.coord])
        folder.add(kml.Placemark(point, name=tp.name, styleUrl=style_url))
    done = set()
    for tp in task.tps:
        key = (tp.name, tp.radius)
        if key in done:
            continue
        else:
            done.add(key)
        coordinates = kml.coordinates.circle(tp.coord, tp.radius)
        line_string = kml.LineString(coordinates, tessellate=1)
        folder.add(kml.Placemark(line_string, styleUrl=style_url))
    tp0 = None
    for sl in util.runs([tp.name for tp in task.tps]):
        if tp0 is None:
            tp0 = task.tps[sl.start]
            continue
        tp1 = task.tps[sl.stop - 1]
        coord0 = tp0.coord.coord_at(tp0.coord.initial_bearing_to(tp1.coord),
                                    tp0.radius)
        theta = tp1.coord.initial_bearing_to(tp0.coord)
        coord1 = tp1.coord.coord_at(theta, tp1.radius)
        line_string1 = kml.LineString(coordinates=[coord0, coord1],
                                      tessellate=1)
        coords = [coord1.coord_at(theta - pi / 12.0, 400.0),
                  coord1,
                  coord1.coord_at(theta + pi / 12.0, 400.0)]
        line_string2 = kml.LineString(coordinates=coords, tessellate=1)
        multi_geometry = kml.MultiGeometry(line_string1, line_string2)
        folder.add(kml.Placemark(multi_geometry, styleUrl=style_url))
        tp0 = tp1
    return kmz.kmz(folder)


def flights2kmz(flights, roots=[], tz_offset=0, task=None):
    stock = Stock()
    globals = util.OpenStruct()
    globals.stock = stock
    globals.bounds = util.BoundsSet()
    for flight in flights:
        globals.bounds.update(flight.track.bounds)
    if globals.bounds.climb.min < -5.0:
        globals.bounds.climb.min = -5.0
    if globals.bounds.climb.max > 5.0:
        globals.bounds.climb.max = 5.0
    globals.tz_offset = datetime.timedelta(0, 3600 * tz_offset)
    globals.task = task
    globals.scales = util.OpenStruct()
    globals.scales.altitude = Scale(globals.bounds.ele.tuple(),
                                    title='altitude', gradient=default_gradient)
    globals.altitude_styles = []
    for i in xrange(0, 3):
        altitude_styles = []
        for c in globals.scales.altitude.colors():
            balloon_style = kml.BalloonStyle(text='$[description]')
            icon_style = kml.IconStyle(globals.stock.icons[i], color=c,
                                       scale=globals.stock.icon_scales[i])
            label_style = kml.LabelStyle(color=c,
                                         scale=globals.stock.label_scales[i])
            style = kml.Style(balloon_style, icon_style, label_style)
            altitude_styles.append(style)
        stock.kmz.add_roots(*altitude_styles)
        globals.altitude_styles.append(altitude_styles)
    gradient = bilinear_gradient
    globals.scales.climb = ZeroCenteredScale(globals.bounds.climb.tuple(),
                                             title='climb', step=0.1,
                                             gradient=gradient)
    globals.scales.speed = Scale(globals.bounds.speed.tuple(),
                                 title='ground speed',
                                 gradient=default_gradient)
    globals.scales.time = TimeScale(globals.bounds.time.tuple(),
                                    tz_offset=globals.tz_offset)
    globals.scales.t = Scale(globals.bounds.t.tuple(), title='time',
                             gradient=default_gradient)
    if hasattr(globals.bounds, 'tas'):
        globals.scales.tas = Scale(globals.bounds.tas.tuple(),
                                   title='air speed', gradient=default_gradient)
    globals.graph_width = 600
    globals.graph_height = 300
    result = kmz.kmz()
    result.add_siblings(stock.kmz)
    result.add_roots(kml.open(1), *roots)
    if globals.task:
        result.add_siblings(make_task_folder(globals, globals.task))
    for flight in flights:
        result.add_siblings(flight.to_kmz(globals))
    return result
