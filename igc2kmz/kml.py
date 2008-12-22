#   igc2kmz KML functions
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


from math import acos, ceil, pi


class_by_name = {}


class Metaclass(type):

    def __new__(cls, name, bases, dct):
        result = type.__new__(cls, name, bases, dct)
        if not name.startswith('_'):
            class_by_name[name] = result
        return result


class _Element(object):
    """KML element base class."""
    __metaclass__ = Metaclass

    def name(self):
        """Return name."""
        return self.__class__.__name__

    def id(self):
        """Return a unique id."""
        return '%x' % id(self)

    def url(self):
        """Return a URL referring to self."""
        return '#%s' % self.id()
    
    def write(self, file):
        """Write self to file."""
        file.write(str(self))

    def pretty_write(self, file, indent='\t', prefix=''):
        """Write self to file."""
        file.write('%s%s\n' % (prefix, self))


class _SimpleElement(_Element):
    """A KML element with no children."""

    def __init__(self, text=None, **kwargs):
        if text is None:
            self.text = None
        elif isinstance(text, bool):
            self.text = str(int(text))
        else:
            self.text = str(text)
        self.attrs = kwargs

    def __str__(self):
        """Return the KML representation of self."""
        attrs = ''.join(' %s="%s"' % pair for pair in self.attrs.items())
        if self.text is None:
            return '<%s%s/>' % (self.name(), attrs)
        else:
            return '<%s%s>%s</%s>' \
                   % (self.name(), attrs, self.text, self.name())


class _CompoundElement(_Element):
    """A KML element with children."""

    def __init__(self, *args, **kwargs):
        self.attrs = {}
        self.children = []
        self.add(*args, **kwargs)

    def add_attrs(self, **kwargs):
        """Add attributes."""
        self.attrs.update(kwargs)

    def add(self, *args, **kwargs):
        """Add children."""
        self.children.extend(list(arg for arg in args if not arg is None))
        for key, value in kwargs.items():
            self.children.append(class_by_name[key](value))

    def write(self, file):
        """Write self to file."""
        attrs = ''.join(' %s="%s"' % pair for pair in self.attrs.items())
        if self.children:
            file.write('<%s%s>' % (self.name(), attrs))
            for child in self.children:
                child.write(file)
            file.write('</%s>' % self.name())
        else:
            file.write('<%s%s/>' % (self.name(), attrs))

    def pretty_write(self, file, indent='\t', prefix=''):
        """Write self to file."""
        attrs = ''.join(' %s="%s"' % pair for pair in self.attrs.items())
        if self.children:
            file.write('%s<%s%s>\n' % (prefix, self.name(), attrs))
            for child in self.children:
                child.pretty_write(file, indent, indent + prefix)
            file.write('%s</%s>\n' % (prefix, self.name()))
        else:
            file.write('%s<%s%s/>\n' % (prefix, self.name(), attrs))

    def __str__(self):
        """Return the KML representation of self."""
        attrs = ''.join(' %s="%s"' % pair for pair in self.attrs.items())
        if self.children:
            return '<%s%s>%s</%s>' % (self.name(), attrs,
                                      ''.join(map(str, self.children)),
                                      self.name())
        else:
            return '<%s%s/>' % (self.name(), attrs)


class Verbatim(_Element):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        """Return the KML representation of self."""
        return self.value


class CDATA(object):
    """A KML CDATA."""

    def __init__(self, value):
        self.value = value

    def __str__(self):
        """Return the KML representation of self."""
        return '<![CDATA[%s]]>' % self.value


class dateTime(object):
    """A KML dateTime."""

    def __init__(self, value):
        self.value = value

    def __str__(self):
        """Return the KML representation of self."""
        return self.value.strftime('%Y-%m-%dT%H:%M:%SZ')


class altitude(_SimpleElement): pass
class altitudeMode(_SimpleElement): pass
class BalloonStyle(_CompoundElement): pass
class begin(_SimpleElement): pass
class bgColor(_SimpleElement): pass
class Camera(_CompoundElement): pass


class color(_SimpleElement):

    def __init__(self, rgba):
        if isinstance(rgba, tuple):
            r, g, b, a = rgba
            rgba = '%02x%02x%02x%02x' % (255 * a, 255 * b, 255 * g, 255 * r)
        _SimpleElement.__init__(self, rgba)


class coordinates(_SimpleElement):

    def __init__(self, coords):
        texts = ('%f,%f,%d' % (c.lon_deg, c.lat_deg, c.ele) for c in coords)
        _SimpleElement.__init__(self, ' '.join(texts))

    @classmethod
    def circle(cls, center, radius, ele=None, error=0.1):
        decimation = int(ceil(pi / acos((radius - error) / (radius + error))))
        coords = []
        for i in xrange(0, decimation + 1):
            coord = center.coord_at(-2.0 * pi * i / decimation, radius + error)
            if ele:
                coord.ele = ele
            coords.append(coord)
        return cls(coords)

    @classmethod
    def arc(cls, center, radius, start, stop, error=0.1):
        delta_theta = 2 * pi / int(ceil(pi / acos((radius - error)
                                   / (radius + error))))
        while start < 0:
            start += 2 * pi
            stop += 2 * pi
        while stop < start:
            stop += 2 * pi
        coords = []
        theta = start
        while theta < stop:
            coords.append(center.coord_at(theta, radius + error))
            theta += delta_theta
        coords.append(center.coord_at(stop, radius + error))
        return cls(coords)


class Data(_CompoundElement):

    def __init__(self, name, *args, **kwargs):
        _CompoundElement.__init__(self, *args, **kwargs)
        self.add_attrs(name=name)


class description(_SimpleElement): pass
class Document(_CompoundElement): pass
class end(_SimpleElement): pass


class ExtendedData(_CompoundElement):

    @classmethod
    def dict(cls, dict):
        return cls(*[Data(key, value=value) for key, value in dict.items()])


class extrude(_SimpleElement): pass
class Folder(_CompoundElement): pass
class heading(_SimpleElement): pass
class href(_SimpleElement): pass


class Icon(_CompoundElement):

    @classmethod
    def character(cls, c, extra=''):
        if ord('1') <= ord(c) <= ord('9'):
            icon = (ord(c) - ord('1')) % 8 + 16 * ((ord(c) - ord('1')) / 8)
            return cls.palette(3, icon, extra)
        elif ord('A') <= ord(c) <= ord('Z'):
            icon = (ord(c) - ord('A')) % 8 + 16 * ((31 - ord(c) + ord('A')) / 8)
            return cls.palette(5, icon, extra)
        else:
            return cls.default()

    @classmethod
    def default(cls):
        return cls.palette(3, 55)

    @classmethod
    def palette(cls, pal, icon, extra=''):
        href = 'http://maps.google.com/mapfiles/kml/pal%d/icon%d%s.png' \
               % (pal, icon, extra)
        return cls(href=href)

    @classmethod
    def none(cls):
        return cls.palette(2, 15)

    @classmethod
    def number(cls, n, extra=''):
        if 1 <= n <= 10:
            return cls.palette(3, (n - 1) % 8 + 16 * ((n - 1) / 8), extra)
        else:
            return cls.default()


class IconStyle(_CompoundElement): pass


class kml(_CompoundElement):

    def __init__(self, version, *args, **kwargs):
        _CompoundElement.__init__(self, *args, **kwargs)
        self.add_attrs(xmlns='http://earth.google.com/kml/%s' % version)

    def write(self, file):
        """Write self to file."""
        file.write('<?xml version="1.0" encoding="UTF-8"?>')
        _CompoundElement.write(self, file)


class LabelStyle(_CompoundElement): pass
class latitude(_SimpleElement): pass
class LineString(_CompoundElement): pass
class LineStyle(_CompoundElement): pass
class ListStyle(_CompoundElement): pass
class listItemType(_SimpleElement): pass
class longitude(_SimpleElement): pass
class MultiGeometry(_CompoundElement): pass
class name(_SimpleElement): pass
class open(_SimpleElement): pass
class overlayXY(_SimpleElement): pass
class Placemark(_CompoundElement): pass
class Point(_CompoundElement): pass
class PolyStyle(_CompoundElement): pass
class roll(_SimpleElement): pass
class scale(_SimpleElement): pass
class ScreenOverlay(_CompoundElement): pass
class screenXY(_SimpleElement): pass
class size(_SimpleElement): pass
class Snippet(_SimpleElement): pass


class Style(_CompoundElement):

    def __init__(self, *args, **kwargs):
        _CompoundElement.__init__(self, *args, **kwargs)
        self.add_attrs(id=self.id())


class styleUrl(_SimpleElement): pass
class tessellate(_SimpleElement): pass
class text(_SimpleElement): pass
class tilt(_SimpleElement): pass
class TimeSpan(_CompoundElement): pass
class value(_SimpleElement): pass
class visibility(_SimpleElement): pass
class when(_SimpleElement): pass
class width(_SimpleElement): pass


__all__ = class_by_name.keys()
