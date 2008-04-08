from cStringIO import StringIO
from zipfile import ZipFile, ZipInfo

import kml

class kmz:

  def __init__(self, *elements):
    self.elements = list(elements)
    self.roots = []
    self.files = {}

  def add_roots(self, *roots):
    self.roots.extend(roots)
    return self

  def add_files(self, files):
    self.files.update(files)
    return self

  def add(self, *args):
    for arg in args:
      if isinstance(arg, kmz):
	self.elements[0].add(*arg.elements)
	self.add_roots(*arg.roots)
	self.add_files(arg.files)
      else:
	self.elements[0].add(arg)
    return self

  def add_siblings(self, *args, **kwargs):
    for arg in args:
      if isinstance(arg, kmz):
	self.elements.extend(arg.elements)
	self.add_roots(*arg.roots)
	self.add_files(arg.files)
      else:
	self.elements.append(arg)
    for key, value in kwargs.items():
      self.elements.append(kml.__dict__[key](value))
    return self

  def write(self, filename):
    zipfile = ZipFile(filename, 'w')
    document = kml.Document()
    document.add(*self.roots)
    document.add(*self.elements)
    string_io = StringIO()
    kml.kml('2.1', document).write(string_io)
    zipfile.writestr('doc.kml', string_io.getvalue())
    string_io.close()
    for key, value in self.files.items():
      zipfile.writestr(ZipInfo(key), value)
    zipfile.close()

if __name__ == '__main__':
  k = kmz(roots=kml.name('Tom'), files={'tom.txt': 'hello'})
  k.write('tom.zip')
