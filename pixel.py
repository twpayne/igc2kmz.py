from cStringIO import StringIO
import cairo

surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)
context = cairo.Context(surface)
context.set_source_rgba(0.0, 0.0, 0.0, 0.0)
context.rectangle(0, 0, 1, 1)
context.fill()
string_io = StringIO()
surface.write_to_png(string_io)
print(len(string_io.getvalue()))

