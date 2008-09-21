import coord
import math


class_by_name = {}


class Metaclass(type):

  def __new__(cls, name, bases, dct):
    result = type.__new__(cls, name, bases, dct)
    if name not in ('Element', 'SimpleElement', 'CompoundElement'):
      class_by_name[name] = result
    return result


class Element(object):
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
    file.write(prefix)
    file.write(str(self))
    file.write('\n')


class SimpleElement(Element):
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
      return '<%s%s>%s</%s>' % (self.name(), attrs, self.text, self.name())


class CompoundElement(Element):
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
    self.children.extend(list(args))
    for key, value in kwargs.items():
      self.children.append(class_by_name[key](value))

  def write(self, file):
    """Write self to file."""
    attrs = ''.join(' %s="%s"' % pair for pair in self.attrs.items())
    if len(self.children) == 0:
      file.write('<%s%s/>' % (self.name(), attrs))
    else:
      file.write('<%s%s>' % (self.name(), attrs))
      for child in self.children:
        child.write(file)
      file.write('</%s>' % self.name())

  def pretty_write(self, file, indent='\t', prefix=''):
    """Write self to file."""
    attrs = ''.join(' %s="%s"' % pair for pair in self.attrs.items())
    if len(self.children) == 0:
      file.write(prefix)
      file.write('<%s%s/>' % (self.name(), attrs))
      file.write('\n')
    else:
      file.write(prefix)
      file.write('<%s%s>' % (self.name(), attrs))
      file.write('\n')
      for child in self.children:
        child.pretty_write(file, indent, indent + prefix)
      file.write(prefix)
      file.write('</%s>' % self.name())
      file.write('\n')

  def __str__(self):
    """Return the KML representation of self."""
    attrs = ''.join(' %s="%s"' % pair for pair in self.attrs.items())
    if len(self.children) == 0:
      return '<%s%s/>' % (self.name(), attrs)
    else:
      return '<%s%s>%s</%s>' % (self.name(), attrs, ''.join(map(str, self.children)), self.name())


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


class altitude(SimpleElement): pass
class altitudeMode(SimpleElement): pass
class BalloonStyle(CompoundElement): pass
class begin(SimpleElement): pass


class color(SimpleElement):

  def __init__(self, rgba):
    if isinstance(rgba, tuple):
      r, g, b, a = rgba
      rgba = '%02x%02x%02x%02x' % (255 * a, 255 * b, 255 * g, 255 * r)
    SimpleElement.__init__(self, rgba)


class coordinates(SimpleElement):

  def __init__(self, coords):
    SimpleElement.__init__(self, ' '.join('%f,%f,%d' % (180.0 * coord.lon / math.pi, 180.0 * coord.lat / math.pi, coord.ele) for coord in coords))


class description(SimpleElement): pass
class Document(CompoundElement): pass
class end(SimpleElement): pass
class extrude(SimpleElement): pass
class Folder(CompoundElement): pass
class href(SimpleElement): pass

class Icon(CompoundElement):

  # FIXME @decorator syntax not supported in python 2.4

  @classmethod
  def character(cls, c, extra=''):
    i = ord(c)
    if ord('1') <= i and i <= ord('9'):
      return cls.palette(3, (i - ord('1')) % 8 + 16 * ((i - ord('1')) / 8), extra)
    elif ord('A') <= i and i <= ord('Z'):
      return cls.palette(5, (i - ord('A')) % 8 + 16 * ((31 - i + ord('A')) / 8), extra)
    else:
      return cls.default()

  @classmethod
  def default(cls):
    return cls.palette(3, 55)

  @classmethod
  def palette(cls, pal, icon, extra=''):
    return cls(href='http://maps.google.com/mapfiles/kml/pal%d/icon%d%s.png' % (pal, icon, extra))

  @classmethod
  def none(cls):
    return cls.palette(2, 15)

  @classmethod
  def number(cls, n, extra=''):
    if 1 <= n and n <= 10:
      return cls.palette(3, (n - 1) % 8 + 16 * ((n - 1) / 8), extra)
    else:
      return cls.default()


class IconStyle(CompoundElement): pass


class kml(CompoundElement):

  def __init__(self, version, *args, **kwargs):
    CompoundElement.__init__(self, *args, **kwargs)
    self.add_attrs(xmlns='http://earth.google.com/kml/%s' % version)

  def write(self, file):
    """Write self to file."""
    file.write('<?xml version="1.0" encoding="UTF-8"?>')
    CompoundElement.write(self, file)


class LabelStyle(CompoundElement): pass
class LineString(CompoundElement): pass
class LineStyle(CompoundElement): pass
class ListStyle(CompoundElement): pass
class listItemType(SimpleElement): pass
class MultiGeometry(CompoundElement): pass
class name(SimpleElement): pass
class open(SimpleElement): pass
class overlayXY(SimpleElement): pass
class Placemark(CompoundElement): pass
class Point(CompoundElement): pass
class PolyStyle(CompoundElement): pass
class scale(SimpleElement): pass
class ScreenOverlay(CompoundElement): pass
class screenXY(SimpleElement): pass
class size(SimpleElement): pass
class Snippet(SimpleElement): pass


class Style(CompoundElement):

  def __init__(self, *args, **kwargs):
    CompoundElement.__init__(self, *args, **kwargs)
    self.add_attrs(id=self.id())


class styleUrl(SimpleElement): pass
class text(SimpleElement): pass
class TimeSpan(CompoundElement): pass
class visibility(SimpleElement): pass
class when(SimpleElement): pass
class width(SimpleElement): pass
