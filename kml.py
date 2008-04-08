import coord
import datetime
import yaml

class Element:

  def name(self):
    return self.__class__.__name__

  def id(self):
    return '%x' % id(self)

  def url(self):
    return '#%s' % self.id()
  
  def write(self, file):
    file.write(str(self))

class SimpleElement(Element):

  def __init__(self, text=None, **kwargs):
    if text is None:
      self.text = None
    else:
      self.text = str(text)
    self.attrs = kwargs

  def __str__(self):
    if len(self.attrs) == 0:
      attrs = ''
    else:
      attrs = ''.join([' %s="%s"' % pair for pair in self.attrs.items()])
    if self.text is None:
      return '<%s%s/>' % (self.name(), attrs)
    else:
      return '<%s%s>%s</%s>' % (self.name(), attrs, self.text, self.name())

class CompoundElement(Element):

  def __init__(self, *args, **kwargs):
    self.attrs = {}
    self.children = []
    self.add(*args, **kwargs)

  def add_attrs(self, **kwargs):
    self.attrs.update(kwargs)

  def add(self, *args, **kwargs):
    self.children.extend(list(args))
    for key, value in kwargs.items():
      self.children.append(globals()[key](value))

  def write(self, file):
    if len(self.attrs) == 0:
      attrs = ''
    else:
      attrs = ''.join([' %s="%s"' % pair for pair in self.attrs.items()])
    if len(self.children) == 0:
      file.write('<%s%s/>' % (self.name(), attrs))
    else:
      file.write('<%s%s>' % (self.name(), attrs))
      for child in self.children:
	child.write(file)
      file.write('</%s>' % self.name())

  def __str__(self):
    if len(self.attrs) == 0:
      attrs = ''
    else:
      attrs = ''.join([' %s="%s"' % pair for pair in self.attrs.items()])
    if len(self.children) == 0:
      return '<%s%s/>' % (self.name(), attrs)
    else:
      return '<%s%s>%s</%s>' % (self.name(), attrs, ''.join(map(str, self.children)), self.name())



class CDATA:

  def __init__(self, value):
    self.value = value

  def __str__(self):
    return '<![CDATA[%s]]>' % self.value


class dateTime:

  def __init__(self, value):
    self.value = value

  def __str__(self):
    return self.value.strftime('%Y-%m-%dT%H:%M:%SZ')


class altitude(SimpleElement): pass
class altitudeMode(SimpleElement): pass
class color(SimpleElement): pass


class coordinates(SimpleElement):

  def __init__(self, coords):
    SimpleElement.__init__(self, ' '.join(['%f,%f,%d' % (coord.lon, coord.lat, coord.ele) for coord in coords]))


class description(SimpleElement): pass
class Document(CompoundElement): pass
class extrude(SimpleElement): pass
class Folder(CompoundElement): pass
class href(SimpleElement): pass
class Icon(CompoundElement): pass


class kml(CompoundElement):

  def __init__(self, version, *args, **kwargs):
    CompoundElement.__init__(self, *args, **kwargs)
    self.add_attrs(xmlns='http://earth.google.com/kml/%s' % version)

  def write(self, file):
    file.write('<?xml version="1.0" encoding="UTF-8"?>')
    CompoundElement.write(self, file)


class LineString(CompoundElement): pass
class LineStyle(CompoundElement): pass
class ListStyle(CompoundElement): pass
class listItemType(SimpleElement): pass
class name(SimpleElement): pass
class open(SimpleElement): pass
class overlayXY(SimpleElement): pass
class Placemark(CompoundElement): pass
class PolyStyle(CompoundElement): pass
class ScreenOverlay(CompoundElement): pass
class screenXY(SimpleElement): pass
class size(SimpleElement): pass
class Snippet(SimpleElement): pass


class Style(CompoundElement):

  def __init__(self, *args, **kwargs):
    CompoundElement.__init__(self, *args, **kwargs)
    self.add_attrs(id=self.id())


class styleUrl(SimpleElement): pass
class visibility(SimpleElement): pass
class when(SimpleElement): pass
class width(SimpleElement): pass


if __name__ == '__main__':
  import sys
  #print(Document(altitude(40), altitudeMode='absolute'))
  coords = coordinates(coord.Coord(1, 2, 3))
  k = kml('2.1', Style(coords), when(dateTime(datetime.datetime.now())))
  k.add(name='Tom')
  k.write(sys.stdout)
  sys.stdout.write('\n')
